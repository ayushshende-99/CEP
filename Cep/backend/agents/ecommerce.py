# E-commerce Agent - Handles cart operations and order management
import json
import random
import string
from datetime import datetime
from models import db, Medicine, Order
from agents.pharmacy_ai import pharmacy_ai


class EcommerceAgent:
    """Handles medicine shopping, cart operations, and order placement."""

    def __init__(self):
        pass

    @staticmethod
    def generate_tracking_id():
        """Generate a unique tracking ID."""
        prefix = "MED"
        timestamp = datetime.utcnow().strftime("%y%m%d")
        random_part = ''.join(random.choices(string.ascii_uppercase + string.digits, k=6))
        return f"{prefix}{timestamp}{random_part}"

    @staticmethod
    def get_all_medicines(category=None, search=None):
        """Get all medicines with optional filters."""
        query = Medicine.query
        if category:
            query = query.filter(Medicine.category == category)
        if search:
            query = query.filter(
                db.or_(
                    Medicine.name.ilike(f"%{search}%"),
                    Medicine.generic_name.ilike(f"%{search}%"),
                    Medicine.description.ilike(f"%{search}%")
                )
            )
        medicines = query.all()
        return [m.to_dict() for m in medicines]

    @staticmethod
    def get_medicine_by_id(medicine_id):
        """Get a single medicine by ID."""
        medicine = Medicine.query.get(medicine_id)
        if medicine:
            return medicine.to_dict()
        return None

    @staticmethod
    def validate_cart(cart_items):
        """Validate cart items and calculate totals."""
        validated_items = []
        total_price = 0
        errors = []

        for item in cart_items:
            medicine = Medicine.query.get(item.get('id'))
            if not medicine:
                errors.append(f"Medicine with ID {item.get('id')} not found")
                continue

            quantity = item.get('quantity', 1)
            if quantity <= 0:
                errors.append(f"Invalid quantity for {medicine.name}")
                continue

            if quantity > medicine.stock:
                errors.append(f"Insufficient stock for {medicine.name}. Available: {medicine.stock}")
                continue

            validated_items.append({
                'id': medicine.id,
                'name': medicine.name,
                'price': medicine.price,
                'quantity': quantity,
                'subtotal': round(medicine.price * quantity, 2)
            })
            total_price += medicine.price * quantity

        return {
            'items': validated_items,
            'total_price': round(total_price, 2),
            'errors': errors,
            'valid': len(errors) == 0
        }

    @staticmethod
    def place_order(
        user_id,
        cart_items,
        shipping_address="",
        payment_method="Cash on Delivery",
        prescription_submission_id=None,
    ):
        """Place an order and update stock."""
        validation = EcommerceAgent.validate_cart(cart_items)

        if not validation['valid']:
            return {
                'success': False,
                'errors': validation['errors']
            }

        if not validation['items']:
            return {
                'success': False,
                'errors': ['Cart is empty']
            }

        # Update stock
        for item in validation['items']:
            medicine = Medicine.query.get(item['id'])
            medicine.stock -= item['quantity']

        # Create order
        tracking_id = EcommerceAgent.generate_tracking_id()
        order = Order(
            user_id=user_id,
            items=json.dumps(validation['items']),
            total_price=validation['total_price'],
            status='pending_verification',
            pharmacist_review_status='pending',
            prescription_submission_id=prescription_submission_id,
            tracking_id=tracking_id,
            shipping_address=shipping_address,
            payment_method=payment_method
        )

        db.session.add(order)
        db.session.flush()
        pharmacy_ai.create_order_verification_request(order)
        db.session.commit()

        return {
            'success': True,
            'order': order.to_dict(),
            'message': f'Order created with pending verification. Tracking ID is {tracking_id}'
        }

    @staticmethod
    def get_user_orders(user_id):
        """Get all orders for a user."""
        orders = Order.query.filter_by(user_id=user_id).order_by(Order.created_at.desc()).all()
        return [o.to_dict() for o in orders]


ecommerce_agent = EcommerceAgent()
