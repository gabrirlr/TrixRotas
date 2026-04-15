import httpx
import os
from dotenv import load_dotenv
from loguru import logger # Usando Loguru conforme definido na stack 

# Carrega as variáveis de ambiente com segurança 
load_dotenv()

class TrixlogAuth:
    def __init__(self):
        self.base_url = os.getenv("TRIXLOG_BASE_URL")
        self.login = os.getenv("TRIXLOG_LOGIN")
        self.password = os.getenv("TRIXLOG_PASSWORD")
        self.token = None

    async def get_token(self):
        """
        Realiza a autenticação via POST /auth conforme o protótipo.
        """
        url = f"{self.base_url}/auth"
        
        # Payload exatamente como na imagem do Postman fornecida
        payload = {
            "login": self.login,
            "password": self.password
        }

        async with httpx.AsyncClient() as client:
            try:
                # Realiza a chamada assíncrona usando httpx 
                response = await client.post(url, json=payload)
                
                # Verifica se houve erro (ex: 401 ou 500)
                response.raise_for_status()
                
                data = response.json()
                
                # Geralmente o token vem num campo chamado 'token' ou 'accessToken'
                # Vou assumir 'token' com base no padrão da API
                self.token = data.get("token") 
                
                logger.info("Autenticação realizada com sucesso na Trixlog.") 
                return self.token
            
            except httpx.HTTPStatusError as e:
                logger.error(f"Falha na autenticação: {e.response.status_code}") 
                return None