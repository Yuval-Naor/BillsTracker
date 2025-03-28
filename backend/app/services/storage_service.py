from azure.storage.blob import BlobServiceClient
from app.config import settings

blob_service = BlobServiceClient.from_connection_string(settings.AZURE_BLOB_CONNECTION_STRING)
container_client = blob_service.get_container_client(settings.AZURE_BLOB_CONTAINER)
try:
    container_client.create_container()
except Exception:
    pass

def upload_attachment(blob_name: str, data: bytes) -> str:
    try:
        container_client.upload_blob(name=blob_name, data=data, overwrite=True)
        account_url = blob_service.url
        blob_url = f"{account_url}/{settings.AZURE_BLOB_CONTAINER}/{blob_name}"
        return blob_url
    except Exception as e:
        print(f"Blob upload failed for {blob_name}: {e}")
        return None
