import base64
import re
import requests
from loguru import logger
from app.config import settings

GMAIL_API_BASE = "https://gmail.googleapis.com/gmail/v1"

def refresh_access_token(refresh_token: str) -> str:
    data = {
        "client_id": settings.GOOGLE_CLIENT_ID,
        "client_secret": settings.GOOGLE_CLIENT_SECRET,
        "grant_type": "refresh_token",
        "refresh_token": refresh_token
    }
    try:
        logger.debug(f"Refreshing access token with client_id: {settings.GOOGLE_CLIENT_ID[:5]}...")
        resp = requests.post("https://oauth2.googleapis.com/token", data=data)
        
        if not resp.ok:
            logger.error(f"Token refresh failed with status {resp.status_code}: {resp.text}")
            resp.raise_for_status()
            
        token_info = resp.json()
        access_token = token_info.get("access_token")
        
        if not access_token:
            logger.error("No access_token in response: {token_info}")
            raise Exception("Failed to refresh access token: No access_token in response")
            
        logger.info("Successfully refreshed access token")
        # Log token expiry if available
        if "expires_in" in token_info:
            logger.info(f"Token expires in {token_info['expires_in']} seconds")
            
        return access_token
    except Exception as e:
        logger.exception(f"Error refreshing token: {str(e)}")
        raise

def list_message_ids(access_token: str, query: str = None, max_results: int = 50):
    url = f"{GMAIL_API_BASE}/users/me/messages"
    params = {}
    if query:
        params["q"] = query
    if max_results:
        params["maxResults"] = max_results
    headers = {"Authorization": f"Bearer {access_token}"}
    
    try:
        logger.debug(f"Making Gmail API request to: {url} with query: {query}")
        resp = requests.get(url, params=params, headers=headers)
        
        # Log detailed information about the response
        if not resp.ok:
            logger.error(f"Gmail API error: {resp.status_code} - {resp.reason}")
            logger.error(f"Response content: {resp.text}")
            
        resp.raise_for_status()
        
        data = resp.json()
        messages = data.get("messages", [])
        
        if not messages:
            logger.warning("No messages found matching the query criteria")
        else:
            logger.info(f"Found {len(messages)} messages matching query")
            
        return [msg['id'] for msg in messages]
    except requests.exceptions.RequestException as e:
        logger.exception(f"Request failed: {str(e)}")
        raise
    except Exception as e:
        logger.exception(f"Error in list_message_ids: {str(e)}")
        raise

def get_message(access_token: str, message_id: str):
    url = f"{GMAIL_API_BASE}/users/me/messages/{message_id}"
    headers = {"Authorization": f"Bearer {access_token}"}
    params = {"format": "full"}
    
    try:
        logger.debug(f"Fetching message with ID: {message_id}")
        resp = requests.get(url, params=params, headers=headers)
        
        if not resp.ok:
            logger.error(f"Failed to fetch message {message_id}: {resp.status_code} - {resp.text}")
            
        resp.raise_for_status()
        return resp.json()
    except Exception as e:
        logger.exception(f"Error fetching message {message_id}: {str(e)}")
        raise

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
