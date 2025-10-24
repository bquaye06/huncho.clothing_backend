from app import create_app, db
from app.models import User, Product, Payment, Order, CartItem, Category

app = create_app()

if __name__ == '__main__':
    with app.app_context():
        db.create_all()
        
        
    app.run(debug=True, host='0.0.0.0', port=7000)