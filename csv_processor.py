import pandas as pd
from schemas import RotaCSV
from loguru import logger
from typing import List, Dict

def processar_arquivo_csv(caminho_arquivo: str) -> Dict[str, List[RotaCSV]]:
    """
    Lê o CSV, valida os dados e agrupa por placa do veículo.
    """
    try:
        # 1. Leitura com Pandas conforme a stack 
        df = pd.read_csv(caminho_arquivo, sep=',', encoding='utf-8')
        
        rotas_por_veiculo = {}
        
        # 2. Agrupamento por placa para suportar múltiplos veículos [cite: 8]
        for placa, grupo in df.groupby('placa'):
            lista_paradas = []
            for _, linha in grupo.iterrows():
                # 3. Validação nativa via Pydantic 
                parada = RotaCSV(**linha.to_dict())
                lista_paradas.append(parada)
            
            rotas_por_veiculo[placa] = lista_paradas
            
        logger.info(f"CSV processado: {len(rotas_por_veiculo)} veículos encontrados.")
        return rotas_por_veiculo

    except Exception as e:
        logger.error(f"Erro ao processar CSV: {e}")
        return {}