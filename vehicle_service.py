import httpx
import os
from loguru import logger
from dotenv import load_dotenv

load_dotenv()

class TrixlogVehicle:
    def __init__(self, token: str):
        self.base_url = "https://qa-trix2.trixlog.com" 
        self.headers = {
            "Authorization": f"{token}", 
            "Content-Type": "application/json"
        }

    async def garantir_veiculo(self, placa_csv: str):
        url_busca = f"{self.base_url}/vehicle"
        
        payload_filter = {
            "pageStart": 0,
            "pageEnd": 10,
            "fieldTerms": {"plate": placa_csv},
            "fieldTermsOperator": "AND",
            "isExactQuery": True, # Solicitamos busca exata à API
            "isNewData": True,
            "sortField": "code",
            "sortDirection": "ASC"
        }

        async with httpx.AsyncClient() as client:
            try:
                response = await client.request("GET", url_busca, json=payload_filter, headers=self.headers)
                data = response.json()
                


                veiculo_existe = False
                
                # Extraímos a lista de resultados independentemente do formato (dict ou list)
                lista_resultados = data if isinstance(data, list) else data.get("list", [])

                if isinstance(lista_resultados, list) and len(lista_resultados) > 0:
                    # PERCORREMOS A LISTA: Procuramos a placa exata
                    for v in lista_resultados:
                        # Comparamos as placas ignorando maiúsculas/minúsculas
                        if str(v.get("plate")).strip().upper() == placa_csv.strip().upper():
                            veiculo_existe = True
                            break

                if veiculo_existe:
                    logger.info(f"✅ Veículo {placa_csv} validado e existente.")
                    return True
                else:
                    logger.warning(f"⚠️ {placa_csv} não encontrado na base. Iniciando cadastro...")
                    return await self.cadastrar_veiculo(placa_csv)

            except Exception as e:
                logger.error(f"❌ Erro ao processar resposta de busca: {e}")
                return False

    async def cadastrar_veiculo(self, placa: str):
        """
        Cria o veículo conforme o payload da imagem image_7ccb49.png
        """
        url_cadastro = f"{self.base_url}/vehicle/"
        payload = {
            "code": placa.replace("-", ""),
            "filiationType": "INHERENT",
            "organization": {"id": 10020, "name": "Trixlog"},
            "plate": placa,
            "status": "ENABLED",
            "vehicleGroup": {"id": 1, "description": "Frota Pesada"},
            "vehicleType": {"id": 18538, "code": "Freezer"}
        }

        async with httpx.AsyncClient() as client:
            try:
                response = await client.post(url_cadastro, json=payload, headers=self.headers)
                response.raise_for_status()
                logger.success(f"✅ Veículo {placa} cadastrado com sucesso!")
                return True
            except Exception as e:
                logger.error(f"❌ Falha ao cadastrar {placa}: {e}")
                return False