from flask_restful import Resource
from flask import request
from flask_jwt_extended import jwt_required, get_jwt_identity
from app.models import db, Order, OrderItem, Product
from flask_limiter import Limiter
from flask_limiter.util import get_remote_address
from app.utils.validators import validate_json

limiter = Limiter(
    key_func=get_remote_address
)

class OrderListResource(Resource):
    @jwt_required()
    @validate_json(["user_id"])
    @limiter.limit("5 per minute")
    def get(self):
        """
        Get all orders firm current user
        """
        user_id = int(get_jwt_identity())
        orders = Order.query.filter_by(user_id=user_id).all()
        return{'orders': [o.to_dict() for o in orders]}, 200
    
    @jwt_required()
    @validate_json(["items"])
    @limiter.limit("5 per minute")
    def post(self):
        """
        Create a new order from the current user's cart(Checkout)
        """
        user_id = int(get_jwt_identity())
        data = request.get_json()
        if not data:
            return {"message": "Request body must be JSON"}, 400

        items = data.get('items')
        if items is None:
            return {"message": "'items' is required in the request body"}, 400
        if not isinstance(items, list):
            return {"message": "'items' must be a list"}, 400

        order_items = []
        total_amount = 0.0

        for item in items:
            if not isinstance(item, dict):
                return {"message": "Each item must be an object with 'product_id' and optional 'quantity'"}, 400

            product_id = item.get('product_id')
            if product_id is None:
                return {"message": "Each item must include 'product_id'"}, 400

            product = Product.query.get(product_id)
            if not product:
                return {"message": f"Product with ID {product_id} not found"}, 404

            try:
                quantity = int(item.get("quantity", 1))
            except (TypeError, ValueError):
                return {"message": "Item 'quantity' must be an integer"}, 400

            if quantity < 1:
                return {"message": "Item 'quantity' must be at least 1"}, 400

            price = float(product.price)
            total_amount += price * quantity
            order_items.append({
                "product_id": product.product_id,
                "quantity": quantity,
                "price": price
            })
        new_order = Order(
            user_id=user_id,
            total_amount=total_amount,
            # status='Pending'
        )
        db.session.add(new_order)
        db.session.flush()  # to get order_id
        
        for oi in order_items:
            new_item = OrderItem(
                order_id=new_order.order_id,
                product_id=oi['product_id'],
                quantity=oi['quantity'],
                price=oi['price']
            )
            db.session.add(new_item)
        db.session.commit()
        return{
            "message": "Order created successfully",
            "order": new_order.to_dict()
        }, 201

class OrderDetailResource(Resource):
    @jwt_required()
    @validate_json(["order_id"])
    @limiter.limit("5 per minute")
    def get(self, order_id):
        """
    Get details of a specific order
        """
        user_id = int(get_jwt_identity())
        order = Order.query.filter_by(order_id=order_id, user_id=user_id).first()
        if not order:
            return {"message": "Order not found"}, 404
        return {"order": order.to_dict()}, 200

class OrderPaymentupdateResource(Resource):
    @validate_json(["order_id", "status"])
    @limiter.limit("5 per minute")
    def post(self):
        """
        Paystack webhook to update order payment status
        """
        data = request.get_json()
        order_id = data.get('order_id')
        status = data.get('status')
        
        order = Order.query.get(order_id)
        if not order:
            return {"message": "Order not found"}, 404
        
        order.payment_status = status
        db.session.commit()
        return {"message": f"Order {order_id} status updated to {status}"}, 200