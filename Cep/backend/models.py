from flask_sqlalchemy import SQLAlchemy
from werkzeug.security import generate_password_hash, check_password_hash
from datetime import datetime
import json

db = SQLAlchemy()

class User(db.Model):
    __tablename__ = 'users'
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    email = db.Column(db.String(120), unique=True, nullable=False)
    password_hash = db.Column(db.String(256), nullable=False)
    is_admin = db.Column(db.Boolean, default=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    orders = db.relationship('Order', backref='user', lazy=True)

    def set_password(self, password):
        self.password_hash = generate_password_hash(password)

    def check_password(self, password):
        return check_password_hash(self.password_hash, password)

    def to_dict(self):
        return {
            'id': self.id,
            'name': self.name,
            'email': self.email,
            'is_admin': self.is_admin,
            'created_at': self.created_at.isoformat()
        }


class Medicine(db.Model):
    __tablename__ = 'medicines'
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(200), nullable=False)
    generic_name = db.Column(db.String(200), nullable=False)
    description = db.Column(db.Text, nullable=True)
    category = db.Column(db.String(100), nullable=True)
    dosage = db.Column(db.String(200), nullable=True)
    side_effects = db.Column(db.Text, nullable=True)
    price = db.Column(db.Float, nullable=False)
    stock = db.Column(db.Integer, default=0)
    image_url = db.Column(db.String(500), nullable=True)
    requires_prescription = db.Column(db.Boolean, default=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    def to_dict(self):
        return {
            'id': self.id,
            'name': self.name,
            'generic_name': self.generic_name,
            'description': self.description,
            'category': self.category,
            'dosage': self.dosage,
            'side_effects': self.side_effects,
            'price': self.price,
            'stock': self.stock,
            'image_url': self.image_url,
            'requires_prescription': self.requires_prescription
        }


class Order(db.Model):
    __tablename__ = 'orders'
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    items = db.Column(db.Text, nullable=False)  # JSON string
    total_price = db.Column(db.Float, nullable=False)
    status = db.Column(db.String(50), default='Ordered')
    tracking_id = db.Column(db.String(20), unique=True, nullable=False)
    shipping_address = db.Column(db.Text, nullable=True)
    payment_method = db.Column(db.String(50), default='Cash on Delivery')
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    def get_items(self):
        return json.loads(self.items)

    def to_dict(self):
        return {
            'id': self.id,
            'user_id': self.user_id,
            'user_name': self.user.name if self.user else 'Unknown',
            'items': self.get_items(),
            'total_price': self.total_price,
            'status': self.status,
            'tracking_id': self.tracking_id,
            'shipping_address': self.shipping_address,
            'payment_method': self.payment_method,
            'created_at': self.created_at.isoformat(),
            'updated_at': self.updated_at.isoformat()
        }
