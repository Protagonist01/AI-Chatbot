from datetime import datetime, timedelta
from typing import Optional
from jose import JWTError, jwt
from fastapi import HTTPException, Security, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from config import settings

security = HTTPBearer()

# JWT Configuration
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_DAYS = 365  # Long-lived tokens for agents

def create_agent_token(agent_id: str, agent_name: str, expires_delta: Optional[timedelta] = None) -> str:
    """
    Create JWT token for agent authentication
    """
    if expires_delta is None:
        expires_delta = timedelta(days=ACCESS_TOKEN_EXPIRE_DAYS)
    
    expire = datetime.utcnow() + expires_delta
    
    payload = {
        "sub": agent_id,
        "name": agent_name,
        "type": "agent",
        "exp": expire,
        "iat": datetime.utcnow()
    }
    
    token = jwt.encode(payload, settings.api_secret_key, algorithm=ALGORITHM)
    return token

def verify_agent_token(credentials: HTTPAuthorizationCredentials = Security(security)) -> dict:
    """
    Verify JWT token and extract agent info
    """
    token = credentials.credentials
    
    try:
        payload = jwt.decode(token, settings.api_secret_key, algorithms=[ALGORITHM])
        agent_id: str = payload.get("sub")
        agent_name: str = payload.get("name")
        token_type: str = payload.get("type")
        
        if agent_id is None or token_type != "agent":
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid authentication token"
            )
        
        return {
            "agent_id": agent_id,
            "agent_name": agent_name
        }
    
    except JWTError as e:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail=f"Could not validate credentials: {str(e)}"
        )