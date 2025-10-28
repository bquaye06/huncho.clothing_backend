from flask import request
from flask_restful import Resource
from app.models import db, Product, Category
from flask_jwt_extended import jwt_required

# This is an admin only resource

# Product List Resource
class ProductListResource(Resource):
    @jwt_required(optional=True)
    def get(self):
        """
        Get all products with optional filtering
        """
        categories_id = request.args.get('categories_id')
        size = request.args.get('size')
        color = request.args.get('color')
        brand = request.args.get('brand')
        
        query = Product.query
        
        if categories_id:
            query = query.filter_by(categories_id=categories_id)
        if size:
            query = query.filter(Product.size.ilike(f"%{size}%"))
        if brand:
            query = query.filter(Product.brand.ilike(f"%{brand}%"))
        if color:
            query = query.filter(Product.color.ilike(f"%{color}%"))

        products = query.all()
        return {'products': [p.to_dict() for p in products]}, 200

    @jwt_required()
    def post(self):
        """
        create new products (admins only)
        """
        data = request.get_json()
        
        required_fields = ['name', 'price']
        for field in required_fields:
            if field not in data:
                return {'message': f"'{field}' is required"}, 400
            
        
        if data.get('categories_id'):
            category = Category.query.get(data['categories_id'])
            if not category:
                return {'message': 'Invalid category ID'}, 400
        
        new_product = Product(
            name=data["name"],
            description=data.get("description"),
            price=data["price"],
            stock=data.get("stock", 0),
            categories_id=data.get("categories_id"),
            brand=data.get("brand"),
            size=data.get("size"),
            color=data.get("color"),
            image_url=data.get("image_url"),
        )
        db.session.add(new_product)
        db.session.commit()
        return {'message': 'Product created', 'product': new_product.to_dict()}, 201

class ProductDetailResource(Resource):
    @jwt_required(optional=True)
    def get(self, product_id):
        """
        Get a specific product
        """
        product = Product.query.get(product_id)
        if not product:
            return {'message': "Product not found"}, 404
        return product.to_dict(), 200

    @jwt_required()
    def put(self, product_id):
        """
        Only admins can update products
        """
        product = Product.query.get(product_id)
        if not product:
            return {'message': "Product not found"}, 404

        data = request.get_json() or {}

        for key, value in data.items():
            if hasattr(product, key):
                setattr(product, key, value)

        db.session.commit()
        return {'message': 'Product updated successfully.', "product": product.to_dict()}, 200

    @jwt_required()
    def delete(self, product_id):
        """
        only admins can delete products
        """
        product = Product.query.get(product_id)
        if not product:
            return {"message": "Product not found"}, 404

        db.session.delete(product)
        db.session.commit()
        return {"message": "Product deleted successfully"}, 200