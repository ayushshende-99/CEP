# Tracking Agent - Manages order tracking and status updates
from models import db, Order
from datetime import datetime

ORDER_STATUSES = [
    "pending_verification",
    "accepted",
    "Packed",
    "Shipped",
    "Out for Delivery",
    "Delivered",
    "rejected",
]

STATUS_DESCRIPTIONS = {
    "pending_verification": "Your order is pending pharmacist verification.",
    "accepted": "Your order has been accepted by the pharmacist and is being prepared.",
    "Packed": "Your order has been packed and is ready for shipping.",
    "Shipped": "Your order is on its way! It has been handed to the delivery partner.",
    "Out for Delivery": "Your order is out for delivery. It will arrive soon!",
    "Delivered": "Your order has been delivered successfully. Thank you!",
    "rejected": "Your order was rejected by pharmacist verification."
}


class TrackingAgent:
    """Manages order tracking and status progression."""

    def __init__(self):
        self.statuses = ORDER_STATUSES
        self.descriptions = STATUS_DESCRIPTIONS

    def track_order(self, tracking_id):
        """Get tracking information for an order."""
        order = Order.query.filter_by(tracking_id=tracking_id).first()

        if not order:
            return {
                'success': False,
                'message': 'Order not found. Please check your tracking ID.'
            }

        current_status_index = self.statuses.index(order.status) if order.status in self.statuses else 0

        timeline = []
        for i, status in enumerate(self.statuses):
            timeline.append({
                'status': status,
                'description': self.descriptions[status],
                'completed': i <= current_status_index,
                'current': i == current_status_index
            })

        if order.status == 'rejected':
            timeline = [
                {
                    'status': 'pending_verification',
                    'description': self.descriptions['pending_verification'],
                    'completed': True,
                    'current': False,
                },
                {
                    'status': 'rejected',
                    'description': self.descriptions['rejected'],
                    'completed': True,
                    'current': True,
                },
            ]

        return {
            'success': True,
            'order': order.to_dict(),
            'timeline': timeline,
            'progress_percentage': int((current_status_index / (len(self.statuses) - 1)) * 100)
        }

    def update_status(self, order_id, new_status):
        """Update order status (admin function)."""
        if new_status not in self.statuses:
            return {
                'success': False,
                'message': f'Invalid status. Valid statuses: {", ".join(self.statuses)}'
            }

        order = Order.query.get(order_id)
        if not order:
            return {
                'success': False,
                'message': 'Order not found.'
            }

        order.status = new_status
        order.updated_at = datetime.utcnow()
        db.session.commit()

        return {
            'success': True,
            'message': f'Order status updated to {new_status}',
            'order': order.to_dict()
        }

    def advance_status(self, order_id):
        """Advance order to next status."""
        order = Order.query.get(order_id)
        if not order:
            return {'success': False, 'message': 'Order not found.'}

        current_index = self.statuses.index(order.status) if order.status in self.statuses else 0

        if current_index >= len(self.statuses) - 1:
            return {'success': False, 'message': 'Order is already delivered.'}

        next_status = self.statuses[current_index + 1]
        return self.update_status(order_id, next_status)


tracking_agent = TrackingAgent()
