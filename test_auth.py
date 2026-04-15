import pytest
from auth_service import TrixlogAuth

@pytest.mark.asyncio
async def test_authentication_success():
    # Instanciamos o serviço que criamos
    auth = TrixlogAuth()
    
    # Chamamos o método de login
    token = await auth.get_token()
    
    # Verificações (Assertions)
    assert token is not None, "O token não deveria ser nulo!"
    assert isinstance(token, str), "O token deve ser uma string!"
    
    print(f"\n✅ Teste concluído! Token recebido: {token[:10]}...")

if __name__ == "__main__":
    # Comando para rodar o teste manualmente se desejar
    import asyncio
    asyncio.run(test_authentication_success())