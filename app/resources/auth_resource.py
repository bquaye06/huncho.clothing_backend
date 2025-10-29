from flask import request
from flask_restful import Resource
from werkzeug.security import generate_password_hash
from werkzeug.security import check_password_hash
from flask_jwt_extended import create_access_token, create_refresh_token
from app.models import db, User
from flask_mail import Message
from app.utils.sms_service import send_sms
from app.utils.validators import validate_json
from flask_limiter import Limiter
from flask_limiter.util import get_remote_address
from app import mail
from datetime import datetime
import string
import random

limiter = Limiter(
    key_func=get_remote_address
)

# Register new user
class RegisterResource(Resource):
    @validate_json(['username', 'email', 'password'])
    @limiter.limit("5 per minute")
    def post(self):
        data = request.get_json()
        username = data.get('username')
        email = data.get('email')
        password = data.get('password')
        first_name = data.get('first_name')
        middle_name = data.get('middle_name')
        last_name = data.get('last_name')
        phone_number = data.get('phone_number')
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
            phone_number=phone_number,
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
        try:
            mail.send(msg)
        except UnicodeEncodeError as e:
            # Most likely caused by non-ASCII characters in MAIL_USERNAME or MAIL_PASSWORD
            print(f"Email send failed due to non-ASCII credentials: {e}")
            return {
                "message": (
                    "Failed to send verification email: non-ASCII characters detected in mail credentials. "
                    "Ensure MAIL_USERNAME and MAIL_PASSWORD contain only ASCII characters (0-127)."
                )
            }, 500
        except Exception as e:
            # Generic email send failure
            print(f"Error sending email: {e}")
            return {"message": "Failed to send verification email."}, 500
        
        # Send OTP to user's phone number via SMS if phone number is provided
        if phone_number:
            message = f"Your verification code for hunchØ.clothing is: {otp}"
            sms_sent = send_sms(phone_number, message)
            if not sms_sent:
                print(f"Failed to send SMS to {phone_number}")

        print(f"Verification OTP for {email}: {otp}")
        
        return{
            'Success': True,
            "message" : "User registered. Check email or SMS for OTP code."
        }, 201
        
# Verify User OTP
class VerifyUserResource(Resource):
        @validate_json(['email', 'otp'])
        @limiter.limit('5 per minute')
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
                

# Login Resource with JWT tokens and OTP
class LoginResource(Resource):
    @validate_json(['email', 'password'])
    @limiter.limit("3 per minute")
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
        access_token = create_access_token(identity=str(user.user_id))
        refresh_token = create_refresh_token(identity=str(user.user_id))
        
        # OTP section can be added here if needed for 2FA
        
        # return success message if successfull
        return{
            'success': f'Login successful, Welcome back {user.username} ',
            'access_token': access_token,
            'refresh_token': refresh_token
            
        }, 200

# Forgot Password Resource
# Sends reset OTP to user's email to reset password
class ForgotPasswordResource(Resource):
    @validate_json(['email'])
    def post(self):
        data = request.get_json()
        email = data.get('email') if data else None

        # validate required fields
        if not email:
            return {'message': 'Email is required'}, 400

        # find user by email
        user = User.query.filter_by(email=email).first()
        if not user:
            return {'message': 'User not found'}, 404

        # generate and save OTP
        otp = ''.join(random.choices(string.digits, k=6))
        user.reset_code = otp
        db.session.commit()

        # prepare and send email
        # Send  reset OTP to user's email and also print in the console for easy shit
        msg = Message(
            subject="Reset code for hunchØ.clothing.",
            recipients=[email],
            body=f"Good day {user.username}, \n\nYour reset code is: {otp}\n\nThanks for signing up with hunchØ.clothing, happy shopping"
        )
        try:
            mail.send(msg)
        except UnicodeEncodeError as e:
            # Most likely caused by non-ASCII characters in MAIL_USERNAME or MAIL_PASSWORD
            print(f"Email send failed due to non-ASCII credentials: {e}")
            return {
                "message": (
                    "Failed to send password reset email: non-ASCII characters detected in mail credentials. "
                    "Ensure MAIL_USERNAME and MAIL_PASSWORD contain only ASCII characters (0-127)."
                )
            }, 500
        except Exception as e:
            # Generic email send failure
            print(f"Error sending email: {e}")
            return {"message": "Failed to send password reset email."}, 500

        
        print(f"Password reset OTP for {email}: {otp}")

        return {
            'Success': True,
            'message': 'Password reset OTP sent to email (and printed to server log).'
        }, 200

# Reset Password Resource
    #  Resets user's password using the OTP sent to email
class ResetPasswordResource(Resource):
        @validate_json(['email', 'otp', 'new_password'])
        def post(self):
            data = request.get_json()
            email = data.get('email')
            otp = data.get('otp')
            new_password = data.get('new_password')
            
            # validate required fields
            if not email or not otp or not new_password:
                return {'message': 'Email, OTP and new password are required'}, 400
            
            # find user by email
            user = User.query.filter_by(email=email).first()
            if not user:
                return {'message': 'User not found'}, 404
            
            # check if OTP matches
            if user.reset_code != otp:
                return {'message': 'Invalid OTP code'}, 400
            
            # update password
            user.password_hash = generate_password_hash(new_password)
            user.reset_code = None  # clear reset code
            db.session.commit()
            return {
                'Success': True,
                'message': 'Password reset successfully, you can now login with your new password'
            }, 200