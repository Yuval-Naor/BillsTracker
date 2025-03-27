import base64
import re
import requests
from app.config import settings

GMAIL_API_BASE = "https://gmail.googleapis.com/gmail/v1"

def refresh_access_token(refresh_token: str) -> str:
    data = {
        "client_id": settings.GOOGLE_CLIENT_ID,
        "client_secret": settings.GOOGLE_CLIENT_SECRET,
        "grant_type": "refresh_token",
        "refresh_token": refresh_token
    }
    resp = requests.post("https://oauth2.googleapis.com/token", data=data)
    resp.raise_for_status()
    token_info = resp.json()
    return token_info.get("access_token")

def list_message_ids(access_token: str, query: str = None, max_results: int = 50):
    url = f"{GMAIL_API_BASE}/users/me/messages"
    params = {}
    if query:
        params["q"] = query
    if max_results:
        params["maxResults"] = max_results
    headers = {"Authorization": f"Bearer {access_token}"}
    resp = requests.get(url, params=params, headers=headers)
    resp.raise_for_status()
    data = resp.json()
    messages = data.get("messages", [])
    return [msg['id'] for msg in messages]

def get_message(access_token: str, message_id: str):
    url = f"{GMAIL_API_BASE}/users/me/messages/{message_id}"
    headers = {"Authorization": f"Bearer {access_token}"}
    params = {"format": "full"}
    resp = requests.get(url, params=params, headers=headers)
    resp.raise_for_status()
    return resp.json()

def get_attachments_info(message: dict):
    attachments = []
    def traverse(parts):
        for part in parts:
            if part.get("filename") and part.get("body", {}).get("attachmentId"):
                attachments.append({
                    "attachmentId": part["body"]["attachmentId"],
                    "filename": part["filename"],
                    "mimeType": part.get("mimeType")
                })
            if part.get("parts"):
                traverse(part.get("parts"))
    payload = message.get("payload", {})
    parts = payload.get("parts", [])
    traverse(parts)
    return attachments

def download_attachment(access_token: str, message_id: str, attachment_id: str):
    url = f"{GMAIL_API_BASE}/users/me/messages/{message_id}/attachments/{attachment_id}"
    headers = {"Authorization": f"Bearer {access_token}"}
    resp = requests.get(url, headers=headers)
    resp.raise_for_status()
    data = resp.json().get("data")
    if data:
        return base64.urlsafe_b64decode(data + '==')
    return None

def extract_urls_from_text(text: str) -> list:
    url_regex = r'https?://[^\s]+'
    return re.findall(url_regex, text)
