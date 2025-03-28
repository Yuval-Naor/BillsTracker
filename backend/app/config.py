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
                jwt_secret = client.get_secret("JWT_SECRET").value
                if jwt_secret:
                    self.JWT_SECRET = jwt_secret
                else:
                    print("Warning: JWT_SECRET is empty in Key Vault.")
            except Exception as e:
                print(f"Failed to load JWT_SECRET from Key Vault: {e}")
            try:
                azure_openai_key = client.get_secret("AZURE_OPENAI_KEY").value
                if azure_openai_key:
                    self.AZURE_OPENAI_KEY = azure_openai_key
                else:
                    print("Warning: AZURE_OPENAI_KEY is empty in Key Vault.")
            except Exception as e:
                print(f"Failed to load AZURE_OPENAI_KEY from Key Vault: {e}")
            try:
                azure_blob_connection_string = client.get_secret("AZURE_BLOB_CONNECTION_STRING").value
                if azure_blob_connection_string:
                    self.AZURE_BLOB_CONNECTION_STRING = azure_blob_connection_string
                else:
                    print("Warning: AZURE_BLOB_CONNECTION_STRING is empty in Key Vault.")
            except Exception as e:
                print(f"Failed to load AZURE_BLOB_CONNECTION_STRING from Key Vault: {e}")
            # Load other secrets similarly with error handling

settings = Settings()
settings.load_secrets_from_keyvault()
