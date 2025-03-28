from pydantic_settings import BaseSettings
from azure.identity import DefaultAzureCredential
from azure.keyvault.secrets import SecretClient
from dotenv import load_dotenv
import os

# Load environment variables from .env file
load_dotenv()

class Settings(BaseSettings):
    GOOGLE_CLIENT_ID: str
    GOOGLE_CLIENT_SECRET: str
    GOOGLE_REDIRECT_URI: str
    JWT_SECRET: str = "CHANGE_ME_SECRET"
    JWT_ALGORITHM: str = "HS256"
    JWT_EXPIRE_HOURS: int = 24
    DATABASE_URL: str
    REDIS_URL: str
    AZURE_OPENAI_ENDPOINT: str
    AZURE_OPENAI_KEY: str
    AZURE_OPENAI_ENGINE: str
    AZURE_OPENAI_API_VERSION: str = "2024-02-01"
    AZURE_BLOB_CONNECTION_STRING: str
    AZURE_BLOB_CONTAINER: str
    FRONTEND_URL: str
    KEY_VAULT_URL: str

    class Config:
        case_sensitive = True

    def load_secrets_from_keyvault(self):
        if os.getenv("USE_KEYVAULT", "false").lower() == "true":
            credential = DefaultAzureCredential()
            client = SecretClient(vault_url=self.KEY_VAULT_URL, credential=credential)
            try:
                self.JWT_SECRET = client.get_secret("JWT_SECRET").value
            except Exception as e:
                print(f"Failed to load JWT_SECRET from Key Vault: {e}")
            # Load other secrets similarly with error handling

settings = Settings()
settings.load_secrets_from_keyvault()
