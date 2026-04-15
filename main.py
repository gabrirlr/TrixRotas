import asyncio
from auth_service import TrixlogAuth
from vehicle_service import TrixlogVehicle
from csv_processor import processar_arquivo_csv
from loguru import logger
import httpx
import os
import time

async def criar_rota_trixlog(token, placa, paradas):
    base_url = os.getenv("TRIXLOG_BASE_URL")
    url = f"{base_url}/route"
    
    # 1. Mantemos a placa original (com hífen) conforme registada
    placa_original = placa.strip().upper()
    
    # 2. RouteKey Curto: Placa + sufixo único (mantendo o hífen na placa)
    # Exemplo: R-ABC-1234-567890
    short_id = str(int(time.time() * 1000))[-6:]
    route_key = f"R-{placa_original}-{short_id}"
    
    data_formatada = paradas[0].data_rota.strftime('%d/%m/%Y')
    
    # 3. Montagem das paradas
    stops_payload = []
    for i, p in enumerate(paradas):
        stops_payload.append({
            "routeKey": route_key,
            "stopKey": f"STP{i+1}",
            "description": p.cliente[:20],
            "plannedSequence": i + 1,
            "type": "Client",
            "plannedDistance": 0,
            "plannedServiceTime": 10,
            "plannedDeliveriesQuantity": 1,
            "address": p.endereco        # ← trocar o hardcode também
            # remover: plannedArrival, plannedDeparture, latitude, longitude
        })

    # 4. Payload fiel ao modelo de sucesso
    payload = {
        "routeKey": route_key,
        "vehiclePlate": placa_original, # Placa com hífen como no cadastro
        "date": data_formatada,
        "description": "ROT-QUEONETICS",
        "plannedDistance": 1,
        "plannedArrival": f"22:00:00 {data_formatada}",
        "plannedDeparture": f"22:00:00 {data_formatada}",
        "totalStops": len(stops_payload),
        "driverId": 1834,
        "lastStopIsDestination": True,
        "status": "PLANNED",
        "originAddress": "ORG-PADRAO",
        "destinationAddress": "DST-PADRAO",
        "originLatitude": paradas[0].latitude,
        "originLongitude": paradas[0].longitude,
        "destinyLatitude": paradas[-1].latitude,
        "destinyLongitude": paradas[-1].longitude,
        "originPOI": "",
        "destinationPOI": "",
        "stops": stops_payload
    }

    headers = {
        "Authorization": f"{token}", 
        "Content-Type": "application/json"
    }
    timeout = httpx.Timeout(30.0)

    async with httpx.AsyncClient(timeout=timeout) as client:
        try:
            logger.info(f"🚀 Enviando rota {route_key} para {placa_original}...")
            response = await client.post(url, json=payload, headers=headers)
            
            if response.status_code in [200, 201]:
                logger.success(f"✅ Rota {route_key} criada com sucesso!")
            else:
                # Agora imprimimos o status e o corpo do erro se a API rejeitar
                logger.error(f"❌ Erro da API {response.status_code}: {response.text}")
                
        except httpx.ConnectTimeout:
            logger.error(f"⌛ Timeout de conexão para {placa_original}. O servidor demorou muito a responder.")
        except Exception as e:
            # Imprimimos o erro completo para diagnóstico
            logger.error(f"❌ Falha inesperada em {placa_original}: {str(e)}")

async def executar_integracao():
    # 1. Autenticação
    auth = TrixlogAuth()
    token = await auth.get_token()
    if not token:
        logger.error("Falha inicial: Sem token de acesso.")
        return

    # 2. Processamento do CSV (Pandas + Pydantic)
    # Certifique-se de que o arquivo 'rotas_clientes.csv' existe
    dados_agrupados = processar_arquivo_csv("rotas_clientes.csv")

    vehicle_manager = TrixlogVehicle(token)

    # 3. Processar cada veículo e suas respectivas paradas
    for placa, paradas in dados_agrupados.items():
        veiculo_pronto = await vehicle_manager.garantir_veiculo(placa)
        if veiculo_pronto:
            await criar_rota_trixlog(token, placa, paradas)
            await asyncio.sleep(1)  # pausa de 1s entre cada rota

if __name__ == "__main__":
    asyncio.run(executar_integracao())