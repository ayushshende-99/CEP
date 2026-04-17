# Medical Routes - AI symptom analysis + chat-based ordering
from flask import Blueprint, request, jsonify, current_app
from agents.medical_ai import medical_agent
from agents.ecommerce import ecommerce_agent
from routes.auth import token_required
from models import db, Medicine
from datetime import datetime
import os
from werkzeug.utils import secure_filename

medical_bp = Blueprint('medical', __name__)

ALLOWED_EXTENSIONS = {'png', 'jpg', 'jpeg', 'gif', 'bmp', 'webp', 'pdf'}


def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS


@medical_bp.route('/analyze', methods=['POST'])
@token_required
def analyze_symptoms(current_user):
    """Analyze symptoms and provide medical suggestions."""
    data = request.get_json()

    if not data or not data.get('symptoms'):
        return jsonify({
            'success': False,
            'message': 'Please provide your symptoms',
            'disclaimer': medical_agent.DISCLAIMER
        }), 400

    result = medical_agent.analyze_symptoms(data['symptoms'])
    return jsonify(result)


@medical_bp.route('/symptoms', methods=['GET'])
def get_supported_symptoms():
    """Get list of symptoms the AI can analyze."""
    symptoms = medical_agent.get_supported_symptoms()
    return jsonify({
        'success': True,
        'symptoms': symptoms
    })


@medical_bp.route('/chat-order', methods=['POST'])
@token_required
def chat_order(current_user):
    """Place an order for a medicine via chat."""
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

    if medicine.requires_prescription:
        return jsonify({
            'success': False,
            'requires_prescription': True,
            'medicine_id': medicine.id,
            'medicine_name': medicine.name,
            'message': (
                f'⚠️ **Prescription Required**\n\n'
                f'**{medicine.name}** requires a valid prescription to order.\n\n'
                f'Please upload your prescription image below. '
                f'We will verify the medicine name and date on it.'
            )
        })

    # No prescription needed — place order automatically
    result = ecommerce_agent.place_order(
        user_id=current_user.id,
        cart_items=[{'id': medicine_id, 'quantity': quantity}],
        shipping_address=data.get('address', ''),
        payment_method=data.get('payment_method', 'Cash on Delivery')
    )

    if result['success']:
        result['message'] = (
            f'✅ **Order Placed Successfully!**\n\n'
            f'**{medicine.name}** x{quantity} has been ordered.\n'
            f'💰 Total: ₹{medicine.price * quantity:.2f}\n'
            f'📦 Tracking ID: **{result["order"]["tracking_id"]}**\n\n'
            f'You can track your order anytime! 🚚'
        )
    return jsonify(result)


@medical_bp.route('/upload-prescription', methods=['POST'])
@token_required
def upload_prescription(current_user):
    """Upload and validate a prescription, then place the order."""
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

    medicine = Medicine.query.get(int(medicine_id))
    if not medicine:
        return jsonify({'success': False, 'message': 'Medicine not found'}), 404

    # Save the file
    upload_folder = current_app.config.get('UPLOAD_FOLDER', 'uploads/prescriptions')
    os.makedirs(upload_folder, exist_ok=True)

    filename = secure_filename(file.filename)
    timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
    saved_filename = f"rx_{current_user.id}_{timestamp}_{filename}"
    filepath = os.path.join(upload_folder, saved_filename)
    file.save(filepath)

    # ====== Prescription Validation (Simulated) ======
    # In production, this would use OCR (Tesseract/Google Vision).
    # For now, we validate based on filename containing medicine name + date.
    today = datetime.now()
    today_str_1 = today.strftime('%Y-%m-%d')  # 2026-04-02
    today_str_2 = today.strftime('%d-%m-%Y')  # 02-04-2026
    today_str_3 = today.strftime('%d/%m/%Y')  # 02/04/2026
    today_str_4 = today.strftime('%Y%m%d')    # 20260402

    filename_lower = filename.lower()

    # Check medicine name in filename
    med_name_lower = medicine.name.lower()
    # Try matching first significant word (brand name) of medicine
    med_words = med_name_lower.split()
    med_name_found = False

    if med_name_lower in filename_lower:
        med_name_found = True
    else:
        for word in med_words:
            clean_word = word.strip('®™().,')
            if len(clean_word) >= 3 and clean_word in filename_lower:
                med_name_found = True
                break

    # Check date in filename
    date_found = any(d in filename_lower for d in [today_str_1, today_str_2, today_str_3, today_str_4])

    if not med_name_found and not date_found:
        return jsonify({
            'success': False,
            'prescription_rejected': True,
            'message': (
                f'❌ **Prescription Rejected**\n\n'
                f'We could not verify your prescription. Please ensure:\n\n'
                f'1. The prescription contains the medicine name: **{medicine.name}**\n'
                f'2. The prescription date is today: **{today_str_1}**\n\n'
                f'💡 **Tip:** Name your prescription file like:\n'
                f'`{med_words[0]}_{today_str_1}.jpg`\n\n'
                f'Please upload a valid prescription and try again.'
            )
        })

    if not med_name_found:
        return jsonify({
            'success': False,
            'prescription_rejected': True,
            'message': (
                f'❌ **Medicine Name Mismatch**\n\n'
                f'The prescription does not appear to be for **{medicine.name}**.\n'
                f'Please upload a prescription that matches the medicine you want to order.\n\n'
                f'💡 **Tip:** Name your file like: `{med_words[0]}_{today_str_1}.jpg`'
            )
        })

    if not date_found:
        return jsonify({
            'success': False,
            'prescription_rejected': True,
            'message': (
                f'❌ **Prescription Date Invalid**\n\n'
                f'The prescription date could not be verified.\n'
                f'Please ensure the prescription is dated today: **{today_str_1}**\n\n'
                f'💡 **Tip:** Include today\'s date in the filename like: `{med_words[0]}_{today_str_1}.jpg`'
            )
        })

    # ====== Prescription Valid — Place Order ======
    quantity = int(request.form.get('quantity', 1))

    result = ecommerce_agent.place_order(
        user_id=current_user.id,
        cart_items=[{'id': int(medicine_id), 'quantity': quantity}],
        shipping_address=request.form.get('address', ''),
        payment_method=request.form.get('payment_method', 'Cash on Delivery')
    )

    if result['success']:
        result['message'] = (
            f'✅ **Prescription Verified & Order Placed!**\n\n'
            f'Your prescription for **{medicine.name}** has been verified successfully! ✔️\n\n'
            f'**{medicine.name}** x{quantity} has been ordered.\n'
            f'💰 Total: ₹{medicine.price * quantity:.2f}\n'
            f'📦 Tracking ID: **{result["order"]["tracking_id"]}**\n\n'
            f'You can track your order anytime! 🚚'
        )
        result['prescription_verified'] = True

    return jsonify(result)
