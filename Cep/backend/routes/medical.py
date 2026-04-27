from flask import Blueprint, request, jsonify

from agents.ecommerce import ecommerce_agent
from agents.pharmacy_ai import pharmacy_ai
from routes.auth import token_required
from models import Medicine, SymptomKnowledge

medical_bp = Blueprint('medical', __name__)

ALLOWED_EXTENSIONS = {'png', 'jpg', 'jpeg', 'gif', 'bmp', 'webp', 'pdf'}


def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS


@medical_bp.route('/analyze', methods=['POST'])
@token_required
def analyze_symptoms(current_user):
    """DB-backed symptom flow: map symptoms -> disease/severity -> actions."""
    data = request.get_json()

    if not data or 'symptoms' not in data:
        return jsonify({'success': False, 'message': 'Please provide symptoms'}), 400

    result, status = pharmacy_ai.analyze_symptoms_flow(
        user_id=current_user.id,
        symptoms_input=data.get('symptoms'),
    )
    return jsonify(result), status


@medical_bp.route('/symptoms', methods=['GET'])
def get_supported_symptoms():
    """Return known symptom texts from dataset knowledge table."""
    symptoms = [
        text
        for (text,) in SymptomKnowledge.query.with_entities(SymptomKnowledge.symptom_text).distinct().limit(500).all()
    ]
    return jsonify({
        'success': True,
        'symptoms': symptoms
    })


@medical_bp.route('/chat-order', methods=['POST'])
@token_required
def chat_order(current_user):
    """Place order while enforcing prescription and pharmacist workflow."""
    data = request.get_json()

    if not data or not data.get('medicine_id'):
        return jsonify({'success': False, 'message': 'Medicine ID is required'}), 400

    medicine_id = data['medicine_id']
    quantity = data.get('quantity', 1)

    medicine = Medicine.query.get(medicine_id)
    if not medicine:
        return jsonify({'success': False, 'message': 'Medicine not found'}), 404

    if medicine.stock < quantity:
        return jsonify({
            'success': False,
            'message': f'Sorry, only {medicine.stock} units of {medicine.name} are available.'
        }), 400

    if medicine.requires_prescription and not data.get('prescription_submission_id'):
        return jsonify({
            'success': False,
            'requires_prescription': True,
            'medicine_id': medicine.id,
            'medicine_name': medicine.name,
            'message': 'Prescription required. Upload and validate prescription first.'
        }), 400

    if medicine.requires_prescription and data.get('prescription_submission_id'):
        search_result, search_status = pharmacy_ai.medicine_search_flow(
            user_id=current_user.id,
            medicine_name=medicine.name,
            prescription_submission_id=data.get('prescription_submission_id'),
        )
        if search_status != 200 or not search_result.get('allow_order'):
            return jsonify(search_result), search_status

    result = ecommerce_agent.place_order(
        user_id=current_user.id,
        cart_items=[{'id': medicine_id, 'quantity': quantity}],
        shipping_address=data.get('address', ''),
        payment_method=data.get('payment_method', 'Cash on Delivery'),
        prescription_submission_id=data.get('prescription_submission_id'),
    )

    return jsonify(result), (201 if result.get('success') else 400)


@medical_bp.route('/upload-prescription', methods=['POST'])
@token_required
def upload_prescription(current_user):
    """Upload prescription file, OCR/parse, and validate or escalate."""
    if 'file' not in request.files:
        return jsonify({'success': False, 'message': 'No prescription file uploaded'}), 400

    file = request.files['file']
    medicine_id = request.form.get('medicine_id')

    if not medicine_id:
        return jsonify({'success': False, 'message': 'Medicine ID is required'}), 400

    if file.filename == '':
        return jsonify({'success': False, 'message': 'No file selected'}), 400

    if not allowed_file(file.filename):
        return jsonify({
            'success': False,
            'message': 'Invalid file type. Please upload an image (PNG, JPG, JPEG, GIF, BMP, WebP) or PDF.'
        }), 400

    result, status = pharmacy_ai.handle_prescription_upload(
        user_id=current_user.id,
        medicine_id=int(medicine_id),
        upload_file=file,
    )
    return jsonify(result), status
