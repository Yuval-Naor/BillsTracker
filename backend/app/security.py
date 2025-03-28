import jwt
from datetime import datetime, timedelta
from app.config import settings
from fastapi import HTTPException

def create_jwt_token(user_id: int) -> str:
    payload = {
        "sub": str(user_id),  # Ensure the subject is a string
        "exp": datetime.utcnow() + timedelta(hours=settings.JWT_EXPIRE_HOURS)
    }
    token = jwt.encode(payload, settings.JWT_SECRET, algorithm=settings.JWT_ALGORITHM)
    return token

def verify_jwt_token(token: str) -> dict:
    try:
        payload = jwt.decode(token, settings.JWT_SECRET, algorithms=[settings.JWT_ALGORITHM])
        if "sub" not in payload:
            raise HTTPException(status_code=401, detail="Token missing subject")
        # Ensure sub is a string
        if not isinstance(payload["sub"], str):
            payload["sub"] = str(payload["sub"])
        return payload
    except jwt.ExpiredSignatureError:
        raise HTTPException(status_code=401, detail="Token has expired")
    except jwt.InvalidTokenError as e:
        raise HTTPException(status_code=401, detail=f"Invalid token: {str(e)}")
    except Exception as e:
        raise HTTPException(status_code=401, detail=f"Token validation error: {str(e)}")
