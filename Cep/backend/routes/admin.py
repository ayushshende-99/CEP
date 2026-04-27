# Admin Routes - Dashboard and management
from flask import Blueprint, request, jsonify
from agents.admin import admin_agent
from agents.tracking import tracking_agent
from routes.auth import admin_required
from models import db, Order, PharmacistMessage, PharmacistRequest, PrescriptionSubmission
from datetime import datetime

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


@admin_bp.route('/pharmacist/requests', methods=['GET'])
@admin_required
def pharmacist_requests(current_user):
    """View all pharmacist requests with optional status filter."""
    status = request.args.get('status')
    query = PharmacistRequest.query.order_by(PharmacistRequest.created_at.desc())
    if status:
        query = query.filter_by(status=status)
    rows = query.all()
    return jsonify({'success': True, 'requests': [row.to_dict() for row in rows], 'count': len(rows)})


@admin_bp.route('/pharmacist/orders', methods=['GET'])
@admin_required
def pharmacist_orders(current_user):
    """View all orders in pharmacist dashboard."""
    status = request.args.get('status')
    query = Order.query.order_by(Order.created_at.desc())
    if status:
        query = query.filter_by(status=status)
    rows = query.all()
    return jsonify({'success': True, 'orders': [row.to_dict() for row in rows], 'count': len(rows)})


@admin_bp.route('/pharmacist/requests/<int:request_id>/accept', methods=['PUT'])
@admin_required
def accept_pharmacist_request(current_user, request_id):
    row = PharmacistRequest.query.get(request_id)
    if not row:
        return jsonify({'success': False, 'message': 'Request not found'}), 404

    data = request.get_json() or {}
    row.status = 'accepted'
    row.message = data.get('message', row.message)
    row.updated_at = datetime.utcnow()

    if row.order_id:
        order = Order.query.get(row.order_id)
        if order:
            order.status = 'accepted'
            order.pharmacist_review_status = 'accepted'
            order.pharmacist_note = data.get('message', order.pharmacist_note)

    db.session.commit()
    return jsonify({'success': True, 'request': row.to_dict()})


@admin_bp.route('/pharmacist/requests/<int:request_id>/reject', methods=['PUT'])
@admin_required
def reject_pharmacist_request(current_user, request_id):
    row = PharmacistRequest.query.get(request_id)
    if not row:
        return jsonify({'success': False, 'message': 'Request not found'}), 404

    data = request.get_json() or {}
    reason = data.get('reason')
    if reason not in {'out_of_stock', 'invalid_prescription', 'not_available'}:
        return jsonify({'success': False, 'message': 'Valid reason is required'}), 400

    row.status = 'rejected'
    row.reason = reason
    row.message = data.get('message', row.message)
    row.updated_at = datetime.utcnow()

    if row.order_id:
        order = Order.query.get(row.order_id)
        if order:
            order.status = 'rejected'
            order.pharmacist_review_status = 'rejected'
            order.pharmacist_rejection_reason = reason
            order.pharmacist_note = data.get('message', order.pharmacist_note)

    db.session.commit()
    return jsonify({'success': True, 'request': row.to_dict()})


@admin_bp.route('/pharmacist/orders/<int:order_id>/accept', methods=['PUT'])
@admin_required
def accept_order(current_user, order_id):
    data = request.get_json() or {}
    order = Order.query.get(order_id)
    if not order:
        return jsonify({'success': False, 'message': 'Order not found'}), 404

    order.status = 'accepted'
    order.pharmacist_review_status = 'accepted'
    order.pharmacist_note = data.get('message', order.pharmacist_note)
    db.session.commit()
    return jsonify({'success': True, 'order': order.to_dict()})


@admin_bp.route('/pharmacist/orders/<int:order_id>/reject', methods=['PUT'])
@admin_required
def reject_order(current_user, order_id):
    data = request.get_json() or {}
    reason = data.get('reason')
    if reason not in {'out_of_stock', 'invalid_prescription', 'not_available'}:
        return jsonify({'success': False, 'message': 'Valid reason is required'}), 400

    order = Order.query.get(order_id)
    if not order:
        return jsonify({'success': False, 'message': 'Order not found'}), 404

    order.status = 'rejected'
    order.pharmacist_review_status = 'rejected'
    order.pharmacist_rejection_reason = reason
    order.pharmacist_note = data.get('message', order.pharmacist_note)
    db.session.commit()
    return jsonify({'success': True, 'order': order.to_dict()})


@admin_bp.route('/pharmacist/prescriptions/<int:submission_id>/approve', methods=['PUT'])
@admin_required
def approve_prescription(current_user, submission_id):
    data = request.get_json() or {}
    submission = PrescriptionSubmission.query.get(submission_id)
    if not submission:
        return jsonify({'success': False, 'message': 'Prescription submission not found'}), 404

    submission.validation_status = 'approved'
    submission.extraction_status = submission.extraction_status or 'readable'
    submission.pharmacist_note = data.get('message', submission.pharmacist_note)
    submission.reviewed_at = datetime.utcnow()
    db.session.commit()
    return jsonify({'success': True, 'prescription_submission': submission.to_dict()})


@admin_bp.route('/pharmacist/users/<int:user_id>/message', methods=['POST'])
@admin_required
def send_user_message(current_user, user_id):
    data = request.get_json() or {}
    message = (data.get('message') or '').strip()
    if not message:
        return jsonify({'success': False, 'message': 'message is required'}), 400

    row = PharmacistMessage(
        user_id=user_id,
        order_id=data.get('order_id'),
        request_id=data.get('request_id'),
        sender='pharmacist',
        message=message,
    )
    db.session.add(row)
    db.session.commit()
    return jsonify({'success': True, 'message_record': row.to_dict()}), 201
