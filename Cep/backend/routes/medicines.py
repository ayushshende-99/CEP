# Medicine Routes - Medicine catalog
from flask import Blueprint, request, jsonify
from agents.ecommerce import ecommerce_agent

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
