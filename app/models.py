from app import db
from datetime import datetime
from werkzeug.security import generate_password_hash, check_password_hash


class User(db.Model):
    __tablename__ = 'users_table'
    user_id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(50), unique=True, nullable=False)
    email = db.Column(db.String(120), unique=True, nullable=False)
    first_name = db.Column(db.String(150))
    middle_name = db.Column(db.String(150))
    last_name = db.Column(db.String(150))
    date_of_birth = db.Column(db.Date)
    country = db.Column(db.String(150))
    password_hash = db.Column(db.Text, nullable=False)
    role = db.Column(db.String(20), default="customer")
    is_verified = db.Column(db.Boolean, default=False)
    verification_code = db.Column(db.String(6), nullable=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    # Relationships
    orders = db.relationship("Order", backref="user", lazy=True)
    # cart_items = db.relationship("CartItem", backref="user", lazy=True)
    payments = db.relationship("Payment", backref="user", lazy=True)
    # reviews = db.relationship("Review", backref="user", lazy=True)

    def __repr__(self):
        return f"<User {self.username}>"
    
    def set_password(self, password):
        self.password_hash = generate_password_hash(password)
    
    def check_password(self, password):
        return check_password_hash(self.password_hash, password)
    
    def to_dict(self):
        return {
            "user_id": self.user_id,
            "username": self.username,
            "email": self.email,
            "is_verified": self.is_verified,
            "created_at": self.created_at.isoformat(),
        }
        
class Product(db.Model):
    __tablename__ = "products_table"

    product_id = db.Column(db.BigInteger, primary_key=True)
    name = db.Column(db.String(150), nullable=False)
    description = db.Column(db.Text, nullable=True)
    price = db.Column(db.Numeric(10, 2), nullable=False)
    stock = db.Column(db.Integer, nullable=False)
    quantity = db.Column(db.Integer, nullable=False)
    brand = db.Column(db.String(100), nullable=True)
    size = db.Column(db.String(50), nullable=True)
    image_url = db.Column(db.String(255), nullable=True)
    category_id = db.Column(db.BigInteger, db.ForeignKey("categories_table.category_id", ondelete="CASCADE"))
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    def to_dict(self):
        return {
            "product_id": self.product_id,
            "name": self.name,
            "description": self.description,
            "price": float(self.price),
            "stock": self.stock,
            "quantity": self.quantity,
            "brand": self.brand,
            "size": self.size,
            "image_url": self.image_url,
            "category_id": self.category_id,
            "created_at": self.created_at.isoformat(),
        }

class Payment(db.Model):
    __tablename__ = "payment_table"

    payment_id = db.Column(db.BigInteger, primary_key=True)
    order_id = db.Column(db.BigInteger, db.ForeignKey("order_table.order_id", ondelete="CASCADE"))
    user_id = db.Column(db.BigInteger, db.ForeignKey("users_table.user_id", ondelete="CASCADE"))  # <-- ADD THIS
    amount = db.Column(db.Numeric(10, 2), nullable=False)
    status = db.Column(db.String(50), default="pending")  # pending, successful, failed
    payment_method = db.Column(db.String(50), nullable=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    def to_dict(self):
        return {
            "payment_id": self.payment_id,
            "order_id": self.order_id,
            "user_id": self.user_id,
            "amount": float(self.amount),
            "status": self.status,
            "payment_method": self.payment_method,
            "created_at": self.created_at.isoformat(),
        }


class Order(db.Model):
    __tablename__ = "order_table"

    order_id = db.Column(db.BigInteger, primary_key=True)
    user_id = db.Column(db.BigInteger, db.ForeignKey("users_table.user_id", ondelete="CASCADE"))
    total_amount = db.Column(db.Numeric(10, 2), nullable=False)
    status = db.Column(db.String(50), default="pending")  # pending, paid, shipped, delivered, cancelled
    shipping_address = db.Column(db.Text, nullable=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    order_items = db.relationship("Order", backref="order", lazy=True)
    payment = db.relationship("Payment", backref="order", uselist=False)

    def to_dict(self):
        return {
            "order_id": self.order_id,
            "user_id": self.user_id,
            "total_amount": float(self.total_amount),
            "status": self.status,
            "shipping_address": self.shipping_address,
            "created_at": self.created_at.isoformat(),
        }

class Category(db.Model):
    __tablename__ = "categories_table"

    category_id = db.Column(db.BigInteger, primary_key=True)
    name = db.Column(db.String(100), unique=True, nullable=False)
    description = db.Column(db.Text, nullable=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    products = db.relationship("Product", backref="category", lazy=True)

    def to_dict(self):
        return {
            "category_id": self.category_id,
            "name": self.name,
            "description": self.description,
            "created_at": self.created_at.isoformat(),
        }

class Cart(db.Model):
    __tablename__ = "cart_items"

    cart_id = db.Column(db.BigInteger, primary_key=True)
    user_id = db.Column(db.BigInteger, db.ForeignKey("users_table.user_id", ondelete="CASCADE"), nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    items = db.relationship("CartItem", backref="cart", lazy=True, cascade="all, delete-orphan")

    def to_dict(self):
        return {
            "cart_id": self.cart_id,
            "user_id": self.user_id,
            "created_at": self.created_at.isoformat(),
            "items": [item.to_dict() for item in self.items],
        }
