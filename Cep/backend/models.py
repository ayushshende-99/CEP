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
    pharmacist_requests = db.relationship('PharmacistRequest', backref='user', lazy=True)
    prescriptions = db.relationship('PrescriptionSubmission', backref='user', lazy=True)
    pharmacist_messages = db.relationship('PharmacistMessage', backref='user', lazy=True)

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
    prescriptions = db.relationship('PrescriptionSubmission', backref='medicine', lazy=True)

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
    status = db.Column(db.String(50), default='pending_verification')
    pharmacist_review_status = db.Column(db.String(50), default='pending')
    pharmacist_rejection_reason = db.Column(db.String(50), nullable=True)
    pharmacist_note = db.Column(db.Text, nullable=True)
    prescription_submission_id = db.Column(db.Integer, db.ForeignKey('prescription_submissions.id'), nullable=True)
    tracking_id = db.Column(db.String(20), unique=True, nullable=False)
    shipping_address = db.Column(db.Text, nullable=True)
    payment_method = db.Column(db.String(50), default='Cash on Delivery')
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    pharmacist_requests = db.relationship('PharmacistRequest', backref='order', lazy=True)
    messages = db.relationship('PharmacistMessage', backref='order', lazy=True)

    def get_items(self):
        try:
            return json.loads(self.items)
        except (TypeError, json.JSONDecodeError):
            return []

    def to_dict(self):
        return {
            'id': self.id,
            'user_id': self.user_id,
            'user_name': self.user.name if self.user else 'Unknown',
            'items': self.get_items(),
            'total_price': self.total_price,
            'status': self.status,
            'pharmacist_review_status': self.pharmacist_review_status,
            'pharmacist_rejection_reason': self.pharmacist_rejection_reason,
            'pharmacist_note': self.pharmacist_note,
            'prescription_submission_id': self.prescription_submission_id,
            'tracking_id': self.tracking_id,
            'shipping_address': self.shipping_address,
            'payment_method': self.payment_method,
            'created_at': self.created_at.isoformat(),
            'updated_at': self.updated_at.isoformat()
        }


class SymptomKnowledge(db.Model):
    __tablename__ = 'symptom_knowledge'
    id = db.Column(db.Integer, primary_key=True)
    symptom_text = db.Column(db.Text, nullable=False, index=True)
    symptom_text_normalized = db.Column(db.Text, nullable=False, index=True)
    disease_name = db.Column(db.String(200), nullable=False, index=True)
    severity = db.Column(db.String(30), nullable=False, index=True)
    advice = db.Column(db.Text, nullable=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    def to_dict(self):
        return {
            'id': self.id,
            'symptom_text': self.symptom_text,
            'disease_name': self.disease_name,
            'severity': self.severity,
            'advice': self.advice,
            'created_at': self.created_at.isoformat()
        }


class DiseaseMedicine(db.Model):
    __tablename__ = 'disease_medicines'
    id = db.Column(db.Integer, primary_key=True)
    disease_name = db.Column(db.String(200), nullable=False, index=True)
    medicine_name = db.Column(db.String(200), nullable=False, index=True)
    requires_prescription = db.Column(db.Boolean, default=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    def to_dict(self):
        return {
            'id': self.id,
            'disease_name': self.disease_name,
            'medicine_name': self.medicine_name,
            'requires_prescription': self.requires_prescription,
            'created_at': self.created_at.isoformat()
        }


class PrescriptionSubmission(db.Model):
    __tablename__ = 'prescription_submissions'
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    medicine_id = db.Column(db.Integer, db.ForeignKey('medicines.id'), nullable=False)
    file_path = db.Column(db.String(500), nullable=False)
    extracted_text = db.Column(db.Text, nullable=True)
    extraction_status = db.Column(db.String(50), default='pending')
    validation_status = db.Column(db.String(50), default='pending')
    pharmacist_note = db.Column(db.Text, nullable=True)
    reviewed_at = db.Column(db.DateTime, nullable=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    orders = db.relationship('Order', backref='prescription_submission', lazy=True)
    pharmacist_requests = db.relationship('PharmacistRequest', backref='prescription_submission', lazy=True)

    def to_dict(self):
        return {
            'id': self.id,
            'user_id': self.user_id,
            'medicine_id': self.medicine_id,
            'medicine_name': self.medicine.name if self.medicine else None,
            'file_path': self.file_path,
            'extracted_text': self.extracted_text,
            'extraction_status': self.extraction_status,
            'validation_status': self.validation_status,
            'pharmacist_note': self.pharmacist_note,
            'reviewed_at': self.reviewed_at.isoformat() if self.reviewed_at else None,
            'created_at': self.created_at.isoformat()
        }


class PharmacistRequest(db.Model):
    __tablename__ = 'pharmacist_requests'
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    request_type = db.Column(db.String(100), nullable=False, index=True)
    status = db.Column(db.String(50), default='pending', index=True)
    severity = db.Column(db.String(30), nullable=True)
    disease_name = db.Column(db.String(200), nullable=True)
    reason = db.Column(db.String(50), nullable=True)
    message = db.Column(db.Text, nullable=True)
    context_data = db.Column(db.Text, nullable=True)
    order_id = db.Column(db.Integer, db.ForeignKey('orders.id'), nullable=True)
    prescription_submission_id = db.Column(db.Integer, db.ForeignKey('prescription_submissions.id'), nullable=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    messages = db.relationship('PharmacistMessage', backref='request', lazy=True)

    def get_context_data(self):
        if not self.context_data:
            return {}
        try:
            return json.loads(self.context_data)
        except (TypeError, json.JSONDecodeError):
            return {}

    def to_dict(self):
        return {
            'id': self.id,
            'user_id': self.user_id,
            'user_name': self.user.name if self.user else None,
            'request_type': self.request_type,
            'status': self.status,
            'severity': self.severity,
            'disease_name': self.disease_name,
            'reason': self.reason,
            'message': self.message,
            'context_data': self.get_context_data(),
            'order_id': self.order_id,
            'prescription_submission_id': self.prescription_submission_id,
            'created_at': self.created_at.isoformat(),
            'updated_at': self.updated_at.isoformat()
        }


class PharmacistMessage(db.Model):
    __tablename__ = 'pharmacist_messages'
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    order_id = db.Column(db.Integer, db.ForeignKey('orders.id'), nullable=True)
    request_id = db.Column(db.Integer, db.ForeignKey('pharmacist_requests.id'), nullable=True)
    sender = db.Column(db.String(30), default='pharmacist')
    message = db.Column(db.Text, nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    def to_dict(self):
        return {
            'id': self.id,
            'user_id': self.user_id,
            'order_id': self.order_id,
            'request_id': self.request_id,
            'sender': self.sender,
            'message': self.message,
            'created_at': self.created_at.isoformat()
        }
