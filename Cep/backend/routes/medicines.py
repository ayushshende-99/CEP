# Medicine Routes - Medicine catalog
from flask import Blueprint, request, jsonify
from agents.ecommerce import ecommerce_agent
from agents.pharmacy_ai import pharmacy_ai
from routes.auth import token_required

medicines_bp = Blueprint('medicines', __name__)


@medicines_bp.route('/', methods=['GET'])
def get_medicines():
    """Get all medicines with optional search/filter."""
    category = request.args.get('category')
    search = request.args.get('search')
    medicines = ecommerce_agent.get_all_medicines(category=category, search=search)
    return jsonify({
        'success': True,
        'medicines': medicines,
        'count': len(medicines)
    })


@medicines_bp.route('/<int:medicine_id>', methods=['GET'])
def get_medicine(medicine_id):
    """Get a single medicine by ID."""
    medicine = ecommerce_agent.get_medicine_by_id(medicine_id)
    if not medicine:
        return jsonify({'success': False, 'message': 'Medicine not found'}), 404
    return jsonify({'success': True, 'medicine': medicine})


@medicines_bp.route('/search-flow', methods=['POST'])
@token_required
def medicine_search_flow(current_user):
    """Medicine search flow with prescription checks and escalation handling."""
    data = request.get_json() or {}
    medicine_name = (data.get('medicine_name') or '').strip()

    if not medicine_name:
        return jsonify({'success': False, 'message': 'medicine_name is required'}), 400

    result, status = pharmacy_ai.medicine_search_flow(
        user_id=current_user.id,
        medicine_name=medicine_name,
        prescription_submission_id=data.get('prescription_submission_id'),
    )
    return jsonify(result), status
