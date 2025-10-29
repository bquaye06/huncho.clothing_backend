from flask import Flask
from flask_sqlalchemy import SQLAlchemy
from datetime import timedelta
from flask_mail import Mail
from flask_jwt_extended import JWTManager
from flask_cors import CORS
from flask_migrate import Migrate
from flask_restful import Api
from flask_limiter import Limiter
from flask_limiter.util import get_remote_address
from dotenv import load_dotenv

import os

db = SQLAlchemy()
mail = Mail()
jwt = JWTManager()
api = Api()
migrate = Migrate()

def create_app():
    load_dotenv()
    app = Flask(__name__)
    CORS(app, resources={r"/*": {"origins": "*"}})
    
    limter = Limiter(
        key_func=get_remote_address,
        app=app,
        default_limits=["200 per day", "50 per hour"]
    )
    @app.errorhandler(429)
    def ratelimit_handler(e):
        return {"message": "ratelimit exceeded %s" % e.description}, 429
    
    
    app.config['JWT_ACCESS_TOKEN_EXPIRES'] = timedelta(days=3)  # Access token lasts 3 days
    app.config['JWT_REFRESH_TOKEN_EXPIRES'] = timedelta(days=30)  # Refresh token lasts 30 days

    
    # Flask configuration
    app.config['SECRET_KEY'] = os.getenv('SECRET_KEY')
    app.config['SQLALCHEMY_DATABASE_URI'] = os.getenv(
        'DATABASE_URL',
        'postgresql+pg8000://postgres:Benedicta%4022@172.29.176.1/huncho_clothing'
    )
    app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
    
    # Mail Configuration
    app.config['MAIL_SERVER'] = os.getenv('MAIL_SERVER')
    app.config['MAIL_PORT'] = int(os.getenv('MAIL_PORT'))
    app.config['MAIL_USE_TLS'] = os.getenv('MAIL_USE_TLS', 'False').lower() == 'true'
    app.config['MAIL_USE_SSL'] = os.getenv('MAIL_USE_SSL', 'False').lower() == 'true'
    app.config['MAIL_USERNAME'] = os.getenv('MAIL_USERNAME')
    app.config['MAIL_PASSWORD'] = os.getenv('MAIL_PASSWORD')
    app.config['MAIL_DEFAULT_SENDER'] = os.getenv('MAIL_DEFAULT_SENDER')
    
    # Payment Configuration
    app.config['PAYSTACK_SECRET_KEY'] = os.getenv('PAYSTACK_SECRET_KEY')
    app.config['PAYSTACK_PUBLIC_KEY'] = os.getenv('PAYSTACK_PUBLIC_KEY')
    app.config['PAYSTACK_BASE_URL'] = os.getenv('PAYSTACK_BASE_URL', "https://api.paystack.co")
    
    # Initialize extensions
    db.init_app(app)
    mail.init_app(app)
    jwt.init_app(app)
    migrate.init_app(app, db)  
    
   

    
    # Import and register resources
    from app.resources.auth_resource import RegisterResource, VerifyUserResource, LoginResource, ForgotPasswordResource, ResetPasswordResource
    from app.resources.user_resource import UserProfileResource
    from app.resources.product_resource import ProductListResource, ProductDetailResource
    from app.resources.cart_resource import CartResource, AddToCartResource,UpdateCartResource, RemoveFromCartResource, ClearCartResource
    from app.resources.orders_resource import OrderListResource, OrderDetailResource,OrderPaymentupdateResource
    from app.resources.payment_resource import InitializePaymentResource,VerifyPaymentResource, PaystackWebhookResource
    
    api = Api(app)
    
    # Auth Resource
    api.add_resource(RegisterResource, '/auth/register')
    api.add_resource(VerifyUserResource, '/auth/verify')
    api.add_resource(LoginResource, '/auth/login')
    api.add_resource(ForgotPasswordResource, '/auth/forgot-password')
    api.add_resource(ResetPasswordResource, '/auth/reset-password')
    
    # User Resource
    api.add_resource(UserProfileResource, '/user/profile')
    
    # Product Resource
    api.add_resource(ProductListResource, '/products')
    api.add_resource(ProductDetailResource, '/products/<int:product_id>')
    
    # Cart Resource
    api.add_resource(CartResource, '/cart')
    api.add_resource(AddToCartResource, '/cart/add')
    api.add_resource(UpdateCartResource, '/cart/update/<int:cart_item_id>')
    api.add_resource(RemoveFromCartResource, '/cart/remove/<int:cart_item_id>') 
    api.add_resource(ClearCartResource, '/cart/clear')
    
    # Orders Resource
    api.add_resource(OrderListResource, '/orders')
    api.add_resource(OrderDetailResource, '/orders/<int:order_id>')
    api.add_resource(OrderPaymentupdateResource, '/orders/payment-update')
    
    # Payment Resource
    api.add_resource(InitializePaymentResource, '/checkout')
    api.add_resource(VerifyPaymentResource, '/verify/<string:reference>')
    api.add_resource(PaystackWebhookResource, '/payment/webhook')
    
    return app