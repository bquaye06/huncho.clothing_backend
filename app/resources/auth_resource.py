from flask import request
from flask_restful import Resource
from werkzeug.security import generate_password_hash
from werkzeug.security import check_password_hash
from flask_jwt_extended import create_access_token, create_refresh_token
from app.models import db, User
from flask_mail import Message
from app import mail
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
            first_name=first_name,
            middle_name=middle_name,
            last_name=last_name,
            date_of_birth = datetime.strptime(date_of_birth, "%Y-%m-%d") if date_of_birth else None,
            country=country,
            is_verified = False,
            verification_code=otp
        )
        
        # Hashing the password properly
        new_user.set_password(password)
        
        # Add New User to the database
        try:
            db.session.add(new_user)
            db.session.commit()
        except Exception as e:
            db.session.rollback()
            print(f"Error occurred: {e}")
            return {"message": "User registration failed"}, 500
        
        # Send OTP to user's email and also print in the console for easy shit
        msg = Message(
            subject="Verification code for hunchØ.clothing.",
            recipients=[email],
            body=f"Good day {username}, \n\nYour verification code is: {otp}\n\nThanks for signing up with hunchØ.clothing, happy shopping"
        )
        mail.send(msg)

        print(f"Verification OTP for {email}: {otp}")
        
        return{
            'Success': True,
            "message" : "User registered. Check email for OTP code."
        }, 201
        
# Verify User OTP
class VerifyUserResource(Resource):
        def post(self):
            data = request.get_json()
            email = data.get('email')
            otp = data.get('otp')
            
            # Validate required fields
            if not email or not otp:
                return{'message': 'Email and OTP is required'}, 400
            
            # Find user by email
            user = User.query.filter_by(email=email).first()

            # Check if user exists
            if not user:
                return {'message': 'User not found'}, 404
            
            # Check if OTP matches verified user
            if user.is_verified:
                return{'message': 'User already verified'}, 400
            
            # Check if OTP matches
            if user.verification_code != otp:
                return {'message': "Invalid OTP code"}, 400
            
            # Mark user as Verified
            user.is_verified = True
            user.verification_code = None 
            db.session.commit()
            
            return{
                'Success': True,
                'message': 'User verified successfully'
            }, 200
                

# Login Resource with JWT tokens
class LoginResource(Resource):
    def post(self):
        data = request.get_json()
        email = data.get('email')
        password = data.get('password')
        
        # Validate required fields
        if not email or not password:
            return {'message': 'Email and password are required'}, 400
        
        # find user by email
        user = User.query.filter_by(email=email).first()
        
        # check if user exists
        if not user:
            return {'message': 'invalid email or password'}, 401
        
        # check if user is verified
        if not user.is_verified:
            return {'message': 'User not verified. Please verify your account.'}, 403
        
        # check if password matches the hashed password
        if not check_password_hash(user.password_hash,password):
            return {'message': 'Invalid email or password'}, 401
        
        # create JWT tokens
        access_token = create_access_token(identity=user.user_id)
        refresh_token = create_refresh_token(identity=user.user_id)
        
        # return success message if successfull
        return{
            'success': f'Login successful, Welcome back {user.username} ',
            'access_token': access_token,
            'refresh_token': refresh_token
            
        }, 200
        