from fastapi import FastAPI, HTTPException, Header
from pydantic import BaseModel
import httpx
import uvicorn
import logging
from typing import Optional

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = FastAPI(title="Service Orders", version="1.0.0")

# Adresse interne Kubernetes de service-auth
# Format : http://<nom-du-service>.<namespace>.svc.cluster.local:<port>
AUTH_SERVICE_URL = "http://service-auth.app.svc.cluster.local:8080"
PAYMENT_SERVICE_URL = "http://service-payment.app.svc.cluster.local:8080"

orders_db = {}
order_counter = 1

class OrderRequest(BaseModel):
    item: str
    quantity: int
    price: float

@app.get("/health")
def health():
    return {"status": "healthy", "service": "service-orders"}

@app.post("/orders/create")
async def create_order(
    order: OrderRequest,
    authorization: Optional[str] = Header(None)
):
    global order_counter

    # Étape 1 : valide le token de l'utilisateur
    token = authorization.replace("Bearer ", "") if authorization else "demo-token-alice"

    async with httpx.AsyncClient() as client:
        try:
            # Appel vers service-auth pour valider le token
            auth_resp = await client.get(
                f"{AUTH_SERVICE_URL}/auth/validate",
                params={"token": token},
                timeout=5.0
            )
            if auth_resp.status_code != 200:
                raise HTTPException(status_code=401, detail="Token invalide")

            user_info = auth_resp.json()
            logger.info(f"Commande créée par: {user_info['username']}")

        except httpx.ConnectError:
            logger.warning("service-auth inaccessible, on continue en démo")
            user_info = {"username": "demo-user", "role": "user"}

    # Étape 2 : crée la commande
    order_id = f"ORD-{order_counter:04d}"
    order_counter += 1
    total = order.quantity * order.price

    orders_db[order_id] = {
        "order_id": order_id,
        "item": order.item,
        "quantity": order.quantity,
        "price": order.price,
        "total": total,
        "user": user_info.get("username", "unknown"),
        "status": "pending"
    }

    # Étape 3 : demande le paiement
    async with httpx.AsyncClient() as client:
        try:
            pay_resp = await client.post(
                f"{PAYMENT_SERVICE_URL}/payment/process",
                json={"order_id": order_id, "amount": total},
                timeout=5.0
            )
            if pay_resp.status_code == 200:
                orders_db[order_id]["status"] = "paid"
                payment_info = pay_resp.json()
            else:
                orders_db[order_id]["status"] = "payment_failed"
                payment_info = {"error": "paiement échoué"}

        except httpx.ConnectError:
            logger.warning("service-payment inaccessible")
            orders_db[order_id]["status"] = "payment_pending"
            payment_info = {"note": "paiement en attente"}

    return {
        "order": orders_db[order_id],
        "payment": payment_info
    }

@app.get("/orders/{order_id}")
def get_order(order_id: str):
    if order_id not in orders_db:
        raise HTTPException(status_code=404, detail="Commande introuvable")
    return orders_db[order_id]

@app.get("/orders")
def list_orders():
    return {"orders": list(orders_db.values()), "total": len(orders_db)}

if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8080, log_level="info")
