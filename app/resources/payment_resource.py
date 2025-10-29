import os
import requests
from flask import request
from flask_restful import Resource
from app.models import db, Order, Payment 
from dotenv import load_dotenv

load_dotenv()
PAYSTACK_SECRET_KEY = os.getenv('PAYSTACK_SECRET_KEY')
PAYSTACK_BASE_URL = os.getenv('PAYSTACK_BASE_URL', "https://api.paystack.co")

class InitializePaymentResource(Resource):
    def post(self):
        data = request.get_json()
        order_id = data.get('order_id')
        email = data.get('email')
        
        if not order_id or not email:
            return{"message": "order_id and email are required"}, 400
        
        order = Order.query.get(order_id)
        if not order:
            return{"message": "Order not found"}, 404
        
        amount_pesewas = float(order.total_amount) * 100 # Paystack expects amount in kobo/pesewas
        payload = {
            "email": email,
            "amount": float(amount_pesewas),
            "currency": "GHS",
        }
        
        headers={
            "Authorization": f"Bearer {PAYSTACK_SECRET_KEY}",
            "Content-Type": "application/json"
        }
        
        response = requests.post(f"{PAYSTACK_BASE_URL}/transaction/initialize", json=payload, headers=headers)
        data = response.json()
        
        if response.status_code == 200 and data.get("status"):
            reference = data["data"]["reference"]
            
            payment = Payment(
                order_id=order_id,
                amount=order.total_amount,
                reference=reference
            )
            db.session.add(payment)
            db.session.commit()
            
            return {
                "authorization_url": data["data"]["authorization_url"],
                "reference": reference
            }, 200
        else:
            return {"message": "Failed to initialize payment", "error": data}, 400

class VerifyPaymentResource(Resource):
    def get(self, reference):
        headers={
            "Authorization": f"Bearer {PAYSTACK_SECRET_KEY}"
        }
        response = requests.get(f"{PAYSTACK_BASE_URL}/transaction/verify/{reference}", headers=headers)
        data = response.json()
        
        if response.status_code == 200 and data.get("data")["status"]== "success":
            payment = Payment.query.filter_by(reference=reference).first()
            if payment:
                payment.status = "successful"
                db.session.commit()
                return {"message": "Payment verified successfully", "data":data["data"]},200
        return {"message": "Payment verification failed", "error": data}, 400
    
class PaystackWebhookResource(Resource):
    def post(self):
        event = request.get_json()
        if not event:
            return {"message": "Invalid payload"}, 400
        
        if event["event"] == "charge.success":
            reference = event["data"]["reference"]
            payment = Payment.query.filter_by(reference=reference).first()
            if payment:
                payment.status = "Successful"
                db.session.commit()
        return {"message": "Webhook received"}, 200