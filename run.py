from app import create_app, db
from app.models import User, Product, Payment, Order, CartItem, Category
from dotenv import load_dotenv
import os

load_dotenv()

app = create_app()

# Run only in development mode
if __name__ == '__main__':
    with app.app_context():
        db.create_all()

    port = int(os.getenv("PORT", 7000))  # Render assigns a PORT dynamically
    app.run(debug=True, host='0.0.0.0', port=port)
