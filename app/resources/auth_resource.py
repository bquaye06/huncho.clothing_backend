from flask import request
from flask_restful import Resource
from werkzeug.security import generate_password_hash
from app.models import db, User
from datetime import datetime
import string
import random

# Register new user
class RegisterResource(Resource):
    def post(self):
        data = request.get_json()
        username = data.get('username')
        email = data.get('email')
        password = data.get('password')
        first_name = data.get('first_name')
        middle_name = data.get('middle_name')
        last_name = data.get('last_name')
        date_of_birth = data.get('date_of_birth')
        country = data.get('country')
        
        # Validate required fields
        if not username or not email or not password:
            return {"message": "Username, email and password are required "}, 400
        
        # Hash password
        password_hash = generate_password_hash(password)
        
        # Generate OTP
        otp = ''.join(random.choices(string.digits, k=6))
        
        # create new user
        new_user = User(
            username=username,
            email=email,
            password=password,
            first_name=first_name,
            middle_name=middle_name,
            last_name=last_name,
            date_of_birth = datetime.strptime(date_of_birth, "%Y-%m-%d") if date_of_birth else None,
            country=country
        )
        
        # Add New User to the database
        db.session.add(new_user)
        
        print(f"Verification OTP for {email}: {otp}")
        
        return{
            'Success': True,
            "message" : "User registered. Check email for OTP code."
        }, 201
            

        