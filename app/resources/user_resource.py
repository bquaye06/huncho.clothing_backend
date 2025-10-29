from flask_jwt_extended import jwt_required, get_jwt_identity
from flask import request
from flask_restful import Resource
from app.models import db, User
from flask_limiter import Limiter
from flask_limiter.util import get_remote_address
from app.utils.validators import validate_json

limiter = Limiter(
    key_func=get_remote_address
)

# User Profile Resource (GET, UPDATE, DELETE)
class UserProfileResource(Resource):
    @jwt_required()
    @limiter.limit("5 per minute")
    def get(self):
        """Get current user's profile"""
        user_id = int(get_jwt_identity())
        user = User.query.get(user_id)
        if not user:
            return {"message": "User not found"}, 404
        
        return user.user_to_dict(), 200
    
    @jwt_required()
    @limiter.limit("5 per minute")
    def put(self):
        """Update current user's profile"""
        user_id = int(get_jwt_identity())
        user = User.query.get(user_id)
        if not user:
            return {"message": "User not found"}, 404
        
        data = request.get_json()
        user.first_name = data.get('first_name', user.first_name)
        user.middle_name = data.get('middle_name', user.middle_name)
        user.last_name = data.get('last_name', user.last_name)
        user.phone_number = data.get('phone_number', user.phone_number)
        user.email = data.get('email', user.email)
        db.session.commit()
        
        return {"message": "Profile updated successfully"}, 200
    