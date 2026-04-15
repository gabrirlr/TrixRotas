import pandas as pd
from datetime import datetime, timedelta

def criar_csv_teste():
    # Definindo a data de amanhã para respeitar a regra de "data futura"
    amanha = (datetime.now() + timedelta(days=1)).strftime('%Y-%m-%d')
    depois_de_amanha = (datetime.now() + timedelta(days=2)).strftime('%Y-%m-%d')

    data = {
        "placa": ["ABC-1234", "ABC-1234", "XYZ-9999", "KGP-5500"],
        "cliente": ["Supermercado Silva", "Farmácia Central", "Indústria Norte", "Loja de Conveniência"],
        "latitude": [-23.5505, -23.5615, -23.5000, -23.5800],
        "longitude": [-46.6333, -46.6559, -46.6000, -46.6700],
        "data_rota": [amanha, amanha, amanha, depois_de_amanha],
        "tipo_veiculo_id": [18538, 18538, 18538, 18538], # ID que vimos no teu Postman
        "org_id": [10020, 10020, 10020, 10020]           # ID da organização Trixlog
    }

    df = pd.DataFrame(data)
    df.to_csv("rotas_clientes.csv", index=False)
    print("✅ Arquivo 'rotas_clientes.csv' criado com sucesso!")

if __name__ == "__main__":
    criar_csv_teste()