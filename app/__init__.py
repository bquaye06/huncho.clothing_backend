from flask import Flask
from flask_sqlalchemy import SQLAlchemy
from datetime import timedelta
from flask_mail import Mail
from flask_jwt_extended import JWTManager
from flask_cors import CORS
from flask_migrate import Migrate
from flask_restful import Api
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
    CORS(app)
    
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
    app.config['MAIL_USE_TLS'] = os.getenv('MAIL_USE_TLS') == 'True'
    app.config['MAIL_USERNAME'] = os.getenv('MAIL_USERNAME')
    app.config['MAIL_PASSWORD'] = os.getenv('MAIL_PASSWORD')
    
    # Initialize extensions
    db.init_app(app)
    mail.init_app(app)
    jwt.init_app(app)
    migrate.init_app(app, db)  
    
    api = Api(app)

    
    # Import and register resources
    from app.resources.auth_resource import RegisterResource
    
    
    # Auth Resource
    api.add_resource(RegisterResource, '/auth/register')
    
    
    return app