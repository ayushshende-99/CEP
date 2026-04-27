# Admin Agent - Dashboard analytics and management
from models import db, User, Medicine, Order
from sqlalchemy import func
from datetime import datetime, timedelta


class AdminAgent:
    """Handles admin dashboard analytics and management operations."""

    def get_dashboard_stats(self):
        """Get overview statistics for admin dashboard."""
        total_users = User.query.filter_by(is_admin=False).count()
        total_orders = Order.query.count()
        total_medicines = Medicine.query.count()

        # Revenue
        total_revenue = db.session.query(func.sum(Order.total_price)).scalar() or 0

        # Orders by status
        status_counts = {
            status: count
            for status, count in db.session.query(Order.status, func.count(Order.id)).group_by(Order.status).all()
        }

        # Recent orders (last 10)
        recent_orders = Order.query.order_by(Order.created_at.desc()).limit(10).all()

        # Low stock medicines (stock < 10)
        low_stock = Medicine.query.filter(Medicine.stock < 10).all()

        return {
            'total_users': total_users,
            'total_orders': total_orders,
            'total_medicines': total_medicines,
            'total_revenue': round(total_revenue, 2),
            'order_status_counts': status_counts,
            'recent_orders': [o.to_dict() for o in recent_orders],
            'low_stock_medicines': [m.to_dict() for m in low_stock]
        }

    def get_all_users(self):
        """Get all registered users."""
        users = User.query.filter_by(is_admin=False).order_by(User.created_at.desc()).all()
        return [u.to_dict() for u in users]

    def get_all_orders(self, status=None):
        """Get all orders with optional status filter."""
        query = Order.query.order_by(Order.created_at.desc())
        if status:
            query = query.filter_by(status=status)
        orders = query.all()
        return [o.to_dict() for o in orders]

    def add_medicine(self, data):
        """Add a new medicine to inventory."""
        medicine = Medicine(
            name=data['name'],
            generic_name=data.get('generic_name', ''),
            description=data.get('description', ''),
            category=data.get('category', 'General'),
            dosage=data.get('dosage', ''),
            side_effects=data.get('side_effects', ''),
            price=float(data['price']),
            stock=int(data.get('stock', 0)),
            image_url=data.get('image_url', ''),
            requires_prescription=data.get('requires_prescription', False)
        )
        db.session.add(medicine)
        db.session.commit()
        return medicine.to_dict()

    def update_medicine(self, medicine_id, data):
        """Update medicine details."""
        medicine = Medicine.query.get(medicine_id)
        if not medicine:
            return None

        for key, value in data.items():
            if hasattr(medicine, key):
                setattr(medicine, key, value)

        db.session.commit()
        return medicine.to_dict()

    def delete_medicine(self, medicine_id):
        """Delete a medicine from inventory."""
        medicine = Medicine.query.get(medicine_id)
        if not medicine:
            return False
        db.session.delete(medicine)
        db.session.commit()
        return True


admin_agent = AdminAgent()
