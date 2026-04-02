from fastapi import FastAPI
from pydantic import BaseModel
import uvicorn
import logging
from datetime import datetime
from typing import Optional

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = FastAPI(title="Service Notification", version="1.0.0")

# Historique des notifications en mémoire
notifications_log = []

class NotifRequest(BaseModel):
    user: str
    message: str
    channel: Optional[str] = "email"  # email, sms, push

@app.get("/health")
def health():
    return {"status": "healthy", "service": "service-notification"}

@app.post("/notify/send")
def send_notification(req: NotifRequest):
    notif = {
        "id": len(notifications_log) + 1,
        "user": req.user,
        "message": req.message,
        "channel": req.channel,
        "sent_at": datetime.utcnow().isoformat(),
        "status": "sent"
    }
    notifications_log.append(notif)

    logger.info(f"[{req.channel.upper()}] → {req.user}: {req.message}")

    return {"sent": True, "notification_id": notif["id"]}

@app.get("/notify/history")
def get_history():
    return {"notifications": notifications_log, "total": len(notifications_log)}

if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8080, log_level="info")
