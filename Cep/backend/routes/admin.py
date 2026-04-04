# Admin Routes - Dashboard and management
from flask import Blueprint, request, jsonify
from agents.admin import admin_agent
from agents.tracking import tracking_agent
from routes.auth import admin_required

admin_bp = Blueprint('admin', __name__)


@admin_bp.route('/dashboard', methods=['GET'])
@admin_required
def get_dashboard(current_user):
    """Get admin dashboard statistics."""
    stats = admin_agent.get_dashboard_stats()
    return jsonify({'success': True, 'stats': stats})


@admin_bp.route('/users', methods=['GET'])
@admin_required
def get_users(current_user):
    """Get all registered users."""
    users = admin_agent.get_all_users()
    return jsonify({'success': True, 'users': users, 'count': len(users)})


@admin_bp.route('/orders', methods=['GET'])
@admin_required
def get_orders(current_user):
    """Get all orders."""
    status = request.args.get('status')
    orders = admin_agent.get_all_orders(status=status)
    return jsonify({'success': True, 'orders': orders, 'count': len(orders)})


@admin_bp.route('/orders/<int:order_id>/status', methods=['PUT'])
@admin_required
def update_order_status(current_user, order_id):
    """Update order status."""
    data = request.get_json()
    if not data or not data.get('status'):
        return jsonify({'success': False, 'message': 'Status is required'}), 400
    result = tracking_agent.update_status(order_id, data['status'])
    if result['success']:
        return jsonify(result)
    return jsonify(result), 400


@admin_bp.route('/orders/<int:order_id>/advance', methods=['PUT'])
@admin_required
def advance_order_status(current_user, order_id):
    """Advance order to next status."""
    result = tracking_agent.advance_status(order_id)
    if result['success']:
        return jsonify(result)
    return jsonify(result), 400


@admin_bp.route('/medicines', methods=['POST'])
@admin_required
def add_medicine(current_user):
    """Add a new medicine."""
    data = request.get_json()
    if not data or not data.get('name') or not data.get('price'):
        return jsonify({'success': False, 'message': 'Name and price are required'}), 400
    medicine = admin_agent.add_medicine(data)
    return jsonify({'success': True, 'medicine': medicine}), 201


@admin_bp.route('/medicines/<int:medicine_id>', methods=['PUT'])
@admin_required
def update_medicine(current_user, medicine_id):
    """Update medicine details."""
    data = request.get_json()
    medicine = admin_agent.update_medicine(medicine_id, data)
    if medicine:
        return jsonify({'success': True, 'medicine': medicine})
    return jsonify({'success': False, 'message': 'Medicine not found'}), 404


@admin_bp.route('/medicines/<int:medicine_id>', methods=['DELETE'])
@admin_required
def delete_medicine(current_user, medicine_id):
    """Delete a medicine."""
    if admin_agent.delete_medicine(medicine_id):
        return jsonify({'success': True, 'message': 'Medicine deleted'})
    return jsonify({'success': False, 'message': 'Medicine not found'}), 404
