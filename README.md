## 1. Visão Geral da Arquitetura

O sistema foi projetado sob o paradigma de **Middleware Assíncrono**. Ele não apenas
repassa dados, mas atua como uma camada de inteligência que valida, agrupa e garante a
integridade dos recursos no destino (Trixlog) antes de executar a roteirização.
**Acesso ao Código-Fonte:**
gabrirlr/TrixRotas

### Fluxo de Dados

1. **Ingestão** : Leitura de dados brutos via CSV.
2. **Sanitização** : Limpeza de placas e coordenadas via Pydantic.
3. **Orquestração** : Autenticação e verificação de preexistência de ativos.
4. **Execução** : Envio sequencial de payloads complexos.

## 2. Gestão de Identidade (auth_service.py)

A autenticação é o portão de entrada. O módulo foi construído para lidar com a instabilidade
latente de ambientes de homologação (QA).
● **Mecanismo** : Utiliza o protocolo Bearer Token.
● **Resiliência (Timeout)** : Implementa um httpx.Timeout de **30.0 segundos**. Isso é vital
porque o servidor de QA pode demorar a processar o handshake de criptografia em
horários de pico.
● **Tratamento de Erros** :
○ **401 Unauthorized** : O sistema interrompe a execução imediatamente para
evitar o bloqueio da conta por múltiplas tentativas falhas.
○ **ReadTimeout** : Captura falhas de resposta lenta sem derrubar a aplicação,
permitindo logs limpos para o suporte.

## 3. Processamento e Inteligência de Dados

## (csv_processor.py)

Diferente de um processamento linha a linha comum, este módulo transforma dados
tabulares em objetos de logística complexos.

### O Modelo de Dados (Pydantic)

Utilizamos classes BaseModel para garantir que o CSV contenha:
● **Placa** : Validada para strings maiúsculas.
● **Coordenadas** : Latitudes e Longitudes convertidas para float, prevenindo erros de
cálculo geográfico na API.
● **Data** : Convertida para objetos datetime para suportar formatações dinâmicas de
rota.

### Lógica de Agrupamento (Grouping Strategy)


O grande diferencial deste módulo é o uso do pandas para agrupar as paradas.
● **Chave de Agrupamento** : placa_veiculo.
● **Resultado** : Um dicionário Python onde a **chave** é a placa e o **valor** é uma lista de
paradas ordenadas.
● **Benefício** : Isso permite que, ao ler um arquivo com 50 linhas para 3 caminhões, o
sistema dispare apenas **3 requisições** de rota, cada uma contendo seu respectivo
lote de paradas.

## 4. Configuração do Ambiente (.env)

O sistema é agnóstico ao ambiente, utilizando variáveis de sistema para segurança:
**Variável Descrição Exemplo**
TRIXLOG_BASE_URL URL do endpoint da API https://qa-trix2.trixlog.com
TRIXLOG_USER Usuário de integração integrador.queonetics
TRIXLOG_PASS Senha de integração ********

## 5. Como o próximo desenvolvedor deve atuar neste

## módulo

Se o objetivo for evoluir para **Input via API (FastAPI)** , as alterações nesta parte devem ser:

1. **No csv_processor.py** : Criar uma função que aceite um io.BytesIO em vez de um
    caminho de arquivo, permitindo processar o CSV vindo diretamente da memória de
    um upload HTTP.
2. **Validação de Schema** : Adicionar verificações para colunas extras que o novo CSV
    possa ter, mantendo a compatibilidade com o modelo atual.

# Gestão de Ativos e Roteirização

## 1. Sincronização de Frota (vehicle_service.py)


Antes de criar qualquer rota, o sistema realiza um "Check-and-Create". Isso evita que o
processo de roteirização falhe por tentar atribuir uma rota a um veículo inexistente na base
da Trixlog.

### Lógica de Verificação Estrita

```
● Busca Exata : A API de busca é consultada usando o campo plate. Como a Trixlog
pode retornar resultados parciais, o módulo implementa um filtro manual que
compara a placa do CSV com a lista retornada
(v.get("plate").strip().upper() == placa_csv).
● Cadastro Automático : Se a verificação falhar, o método cadastrar_veiculo é
acionado imediatamente.
○ Payload de Cadastro : Inclui campos obrigatórios como vehicleGroup (ID
1), organization (ID 10020) e vehicleType (ID 1). Estes IDs foram
mapeados conforme o ambiente de QA e devem ser revisados ao migrar
para Produção.
```
## 2. Motor de Roteirização (main.py)

Este é o componente mais sensível do sistema, responsável por converter o agrupamento
do CSV em um objeto JSON que a Trixlog consiga processar geograficamente.

### Identificadores Únicos (routeKey)

A regra de negócio da Trixlog impede a criação de duas rotas com o mesmo nome.
● **Formato** : R-{PLACA}-{TIMESTAMP_MS}.
● **Por que milissegundos?** Durante o processamento assíncrono, múltiplas rotas
podem ser geradas no mesmo segundo. O uso de milissegundos garante que cada
routeKey seja único.

### Otimização do Payload de Rota

O payload foi ajustado para espelhar o modelo de sucesso validado:
● **Janela de Tempo** : Definida com plannedArrival e plannedDeparture
estáticos (ex: 22:00:00) para este protótipo, garantindo que a API não rejeite a rota
por inconsistência de horário.
● **Geolocalização de Origem/Destino** : O sistema extrai a latitude/longitude da
primeira e última parada do CSV para preencher os campos
originLatitude/Longitude e destinyLatitude/Longitude. Isso resolve o
**Erro 500** que ocorre quando esses campos são enviados com valor zero.


```
● Sequenciamento : Cada parada recebe um stopKey único e uma
plannedSequence incremental, garantindo que o motor de logística respeite a
ordem definida no CSV.
```
## 3. Gestão de Concorrência e Resiliência

Para evitar sobrecarga no servidor de QA e garantir a estabilidade da integração,
implementamos um fluxo de **Processamento Sequencial Controlado**.
● **Fila de Espera (asyncio.sleep(1))** : Entre a criação de uma rota e outra, o
sistema aguarda 1 segundo. Isso permite que o banco de dados da Trixlog processe
a transação anterior completamente.
● **Timeout Adaptativo** : Todas as requisições utilizam um tempo limite de 30
segundos. Operações de roteirização exigem processamento pesado no servidor e
tendem a demorar mais que requisições CRUD comuns.

## 4. Como o próximo desenvolvedor deve atuar neste

## módulo

Se houver necessidade de expandir a lógica de roteirização:

1. **Dinamicidade de Horários** : Atualmente, as rotas são criadas para as 22:00. O
    próximo passo é extrair o horário de uma coluna específica no CSV.
2. **Tratamento do Erro 405** : Se o sistema retornar "Rota já existente", o desenvolvedor
    deve decidir se o sistema deve **deletar a rota antiga** (via DELETE /route) ou
    apenas ignorar o erro e seguir para o próximo veículo.
3. **IDs de Motorista** : O driverId está fixo (1834). Deve-se implementar uma lógica
    de busca de motorista ou inclusão desta informação no input de dados original.
