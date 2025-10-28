from flask import request
from flask_restful import Resource
from app.models import db, Cart, CartItem, Product, User
from flask_jwt_extended import jwt_required, get_jwt_identity
from datetime import datetime

class CartResource(Resource):
    @jwt_required()
    def get(self):
        """
        Get the current user's active cart
        """
        user_id = int(get_jwt_identity())
        cart = Cart.query.filter_by(user_id=user_id, is_active=True).first()
        
        if not cart:
            # If no active cart, create one
            cart = Cart(user_id=user_id)
            db.session.add(cart)
            db.session.commit()

            return {"cart": cart.to_dict()}, 200

class AddToCartResource(Resource):
    @jwt_required()
    def post(self):
        """"
        Add items to current user's cart or increase if it exists already
        """
        user_id = int(get_jwt_identity())
        data = request.get_json()
        
        product_id = data.get("product_id")
        quantity = int(data.get("quantity", 1))
        
        if not product_id:
            return {"message": "product_id is required"}, 400
        
        product = Product.query.get(product_id)
        if not product:
            return {"message": "product not found"}, 404
        
        cart = Cart.query.filter_by(user_id=user_id, is_active=True).first()
        if not cart:
            cart = Cart(user_id=user_id)
            db.session.add(cart)
            db.session.commit()
        
        # check if item is already in the cart
        cart_item = CartItem.query.filter_by(cart_id=cart.cart_id,product_id=product_id).first()
        if cart_item:
            cart_item.quantity += quantity
            cart_item.updated_at = datetime.utcnow()
        else:
            cart_item = CartItem(
                cart_id=cart.cart_id,
                user_id=user_id,
                product_id=product_id,
                quantity=quantity,
                price_at_time=product.price,
            )
            db.session.add(cart_item)
        db.session.commit()
        return {"message": "Item added to cart successfully", "cart": cart.to_dict()}, 201

class UpdateCartResource(Resource):
    @jwt_required()
    def put(self, cart_item_id):
        """
        Update the quantity of a specific item in the cart by cart_item_id
        """
        user_id = int(get_jwt_identity())
        data = request.get_json()

        if not data or 'quantity' not in data:
            return {"message": "Quantity is required and must be at least 1"}, 400

        try:
            quantity = int(data.get("quantity"))
        except (TypeError, ValueError):
            return {"message": "Quantity must be an integer"}, 400

        if quantity < 1:
            return {"message": "Quantity must be at least 1"}, 400

        cart = Cart.query.filter_by(user_id=user_id, is_active=True).first()
        if not cart:
            return {"message": "No active cart found"}, 404

        # Find the cart item by its id and ensure it belongs to the user's active cart
        cart_item = CartItem.query.filter_by(cart_item_id=cart_item_id, cart_id=cart.cart_id).first()
        if not cart_item:
            return {"message": "Item not found in cart"}, 404

        cart_item.quantity = quantity
        cart_item.updated_at = datetime.utcnow()
        db.session.commit()

        return {"message": "Cart item updated successfully", "cart": cart.to_dict()}, 200

class RemoveFromCartResource(Resource):
    @jwt_required()
    def delete(self, cart_item_id):
        """
        Remove a specific item from the user's cart
        """
        user_id = int(get_jwt_identity())
        cart = Cart.query.filter_by(user_id=user_id, is_active=True).first()
        
        if not cart:
            return {"message": "No active cart found"}, 404
        
        cart_item = CartItem.query.filter_by(cart_id=cart.cart_id, cart_item_id=cart_item_id).first()
        if not cart_item:
            return {"message": "Item not found in cart"}, 404
        
        db.session.delete(cart_item)
        db.session.commit()
        
        return {"message": "Item removed from cart successfully", "cart": cart.to_dict()}, 200

class ClearCartResource(Resource):
    @jwt_required()
    def delete(self):
        """
        Clear all items from the user's active cart.
        """
        user_id = int(get_jwt_identity())
        cart = Cart.query.filter_by(user_id=user_id, is_active=True).first()

        if not cart:
            return {"message": "Cart not found"}, 404

        CartItem.query.filter_by(cart_id=cart.cart_id).delete()
        db.session.commit()

        return {"message": "Cart cleared successfully"}, 200