from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
import uvicorn
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = FastAPI(
    title="Service Auth",
    description="Service d'authentification",
    version="1.0.0"
)

USERS_DB = {
    "alice": {"password": "secret", "role": "user"},
    "admin": {"password": "admin123", "role": "admin"},
}

class LoginRequest(BaseModel):
    username: str 
    password: str 

@app.get("/health")
def health():
    return {"status": "healthy", "service": "service-auth"}

@app.post("/auth/login")
def lgin(req: LoginRequest):
    user = USERS_DB.get(req.username)
    if not user or user["password"] != req.password:
        logger.warning(f"Tentative d'authentification échouée pour: {req.username}")
        raise HTTPException(status_code=401, detail="Identifiants invalides")

    logger.info(f"Authentification réussie: {req.username}")
    return {
        "token": f"demo-token-{req.username}",
        "role": user["role"],
        "expires_in": 300  # 5 minutes (simulé)
    }

@app.get("/auth/validate")
def validate(token: str):
    if token.startswith("demo-token-"):
        username = token.replace("demo-token-", "")
        if username in USERS_DB:
            logger.info(f"Token valide pour: {username}")
            return {"valid": True, "username": username, "role": USERS_DB[username]["role"]}

    logger.warning(f"Token invalide reçu: {token}")
    raise HTTPException(status_code=401, detail="Token invalide")

if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8080, log_level="info")
