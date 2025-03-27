from fastapi import APIRouter, Depends, HTTPException
from fastapi.responses import RedirectResponse
import requests
from urllib.parse import urlencode
from app.config import settings
from app.database import SessionLocal
from app import models, security

router = APIRouter()

GOOGLE_AUTH_BASE = "https://accounts.google.com/o/oauth2/v2/auth"
GOOGLE_TOKEN_URL = "https://oauth2.googleapis.com/token"
GOOGLE_USERINFO_URL = "https://www.googleapis.com/oauth2/v2/userinfo"
SCOPE = "https://www.googleapis.com/auth/gmail.readonly email profile"

@router.get("/google")
def google_oauth_login():
    """Redirect to Google's OAuth consent page."""
    params = {
        "client_id": settings.GOOGLE_CLIENT_ID,
        "redirect_uri": settings.GOOGLE_REDIRECT_URI,
        "response_type": "code",
        "scope": SCOPE,
        "access_type": "offline",
        "prompt": "consent"
    }
    auth_url = GOOGLE_AUTH_BASE + "?" + urlencode(params)
    return RedirectResponse(auth_url)

@router.get("/google/callback")
def google_oauth_callback(code: str = None, error: str = None):
    """Handle OAuth callback from Google and issue JWT."""
    if error or not code:
        raise HTTPException(status_code=400, detail="Google OAuth failed or was canceled.")
    token_data = {
        "code": code,
        "client_id": settings.GOOGLE_CLIENT_ID,
        "client_secret": settings.GOOGLE_CLIENT_SECRET,
        "redirect_uri": settings.GOOGLE_REDIRECT_URI,
        "grant_type": "authorization_code"
    }
    token_resp = requests.post(GOOGLE_TOKEN_URL, data=token_data)
    if token_resp.status_code != 200:
        raise HTTPException(status_code=500, detail="Token exchange failed.")
    tokens = token_resp.json()
    access_token = tokens.get("access_token")
    refresh_token = tokens.get("refresh_token")
    if not access_token or not refresh_token:
        raise HTTPException(status_code=500, detail="Token exchange incomplete.")
    userinfo_resp = requests.get(GOOGLE_USERINFO_URL, headers={"Authorization": f"Bearer {access_token}"})
    if userinfo_resp.status_code != 200:
        raise HTTPException(status_code=500, detail="Failed to get user info.")
    profile = userinfo_resp.json()
    email = profile.get("email")
    name = profile.get("name", "Google User")
    
    db = SessionLocal()
    user = db.query(models.User).filter_by(email=email).first()
    if not user:
        user = models.User(email=email, name=name, google_refresh_token=refresh_token)
        db.add(user)
    else:
        user.google_refresh_token = refresh_token
    db.commit()
    jwt_token = security.create_jwt_token(user_id=user.id)
    db.close()
    redirect_url = f"{settings.FRONTEND_URL}/auth/callback?token={jwt_token}"
    return RedirectResponse(redirect_url)

from fastapi.security import HTTPBearer
auth_scheme = HTTPBearer(auto_error=False)

def get_current_user(token: str = Depends(auth_scheme)):
    if not token or not token.credentials:
        raise HTTPException(status_code=401, detail="Not authenticated")
    payload = security.verify_jwt_token(token.credentials)
    user_id = payload.get("sub")
    if not user_id:
        raise HTTPException(status_code=401, detail="Invalid token")
    db = SessionLocal()
    user = db.query(models.User).get(user_id)
    db.close()
    if not user:
        raise HTTPException(status_code=401, detail="User not found")
    return user
