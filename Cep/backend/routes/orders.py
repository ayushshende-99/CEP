# Order Routes - Order management and tracking
from flask import Blueprint, request, jsonify
from agents.ecommerce import ecommerce_agent
from agents.tracking import tracking_agent
from routes.auth import token_required

orders_bp = Blueprint('orders', __name__)


@orders_bp.route('/place', methods=['POST'])
@token_required
def place_order(current_user):
    """Place a new order."""
    data = request.get_json()

    if not data or not data.get('items'):
        return jsonify({'success': False, 'message': 'Cart items are required'}), 400

    result = ecommerce_agent.place_order(
        user_id=current_user.id,
        cart_items=data['items'],
        shipping_address=data.get('address', ''),
        payment_method=data.get('payment_method', 'Cash on Delivery'),
        prescription_submission_id=data.get('prescription_submission_id'),
    )

    if result['success']:
        return jsonify(result), 201
    return jsonify(result), 400


@orders_bp.route('/my-orders', methods=['GET'])
@token_required
def get_my_orders(current_user):
    """Get all orders for the current user."""
    orders = ecommerce_agent.get_user_orders(current_user.id)
    return jsonify({
        'success': True,
        'orders': orders,
        'count': len(orders)
    })


@orders_bp.route('/track/<tracking_id>', methods=['GET'])
def track_order(tracking_id):
    """Track an order by tracking ID."""
    result = tracking_agent.track_order(tracking_id)
    if result['success']:
        return jsonify(result)
    return jsonify(result), 404
