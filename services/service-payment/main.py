from fastapi import FastAPI
from pydantic import BaseModel
import httpx
import uvicorn
import logging
import uuid

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = FastAPI(title="Service Payment", version="1.0.0")

NOTIFICATION_SERVICE_URL = "http://service-notification.app.svc.cluster.local:8080"

payments_db = {}

class PaymentRequest(BaseModel):
    order_id: str
    amount: float

@app.get("/health")
def health():
    return {"status": "healthy", "service": "service-payment"}

@app.post("/payment/process")
async def process_payment(req: PaymentRequest):
    payment_id = f"PAY-{str(uuid.uuid4())[:8].upper()}"

    payments_db[payment_id] = {
        "payment_id": payment_id,
        "order_id": req.order_id,
        "amount": req.amount,
        "status": "approved",
        "method": "demo-card-**** 4242"
    }

    logger.info(f"Paiement traité: {payment_id} pour {req.amount}€")
    # Notifie l'utilisateur après paiement réussi
    async with httpx.AsyncClient() as client:
        try:
            await client.post(
                f"{NOTIFICATION_SERVICE_URL}/notify/send",
                json={
                    "user": "client",
                    "message": f"Paiement de {req.amount}€ confirmé (réf: {payment_id})",
                    "channel": "email"
                },
                timeout=3.0
            )
        except httpx.ConnectError:
            logger.warning("service-notification inaccessible, on continue")

    return payments_db[payment_id]

@app.get("/payment/{payment_id}")
def get_payment(payment_id: str):
    if payment_id not in payments_db:
        from fastapi import HTTPException
        raise HTTPException(status_code=404, detail="Paiement introuvable")
    return payments_db[payment_id]

if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8080, log_level="info")
