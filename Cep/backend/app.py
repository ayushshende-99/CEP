"""
Smart Agentic Medical Advisor & Pharmacy - Main Flask Application
"""
from flask import Flask, send_from_directory
from flask_cors import CORS
from config import Config
from models import db, User, Medicine
import os
import csv

def create_app():
    frontend_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', 'frontend'))
    app = Flask(__name__, static_folder=None)
    app.config.from_object(Config)

    # Enable CORS
    CORS(app)

    # Upload config for prescriptions
    upload_folder = os.path.join(os.path.dirname(__file__), 'uploads', 'prescriptions')
    app.config['UPLOAD_FOLDER'] = upload_folder
    app.config['MAX_CONTENT_LENGTH'] = 5 * 1024 * 1024  # 5MB max
    os.makedirs(upload_folder, exist_ok=True)

    # Initialize database
    db.init_app(app)

    # Register blueprints
    from routes.auth import auth_bp
    from routes.medical import medical_bp
    from routes.medicines import medicines_bp
    from routes.orders import orders_bp
    from routes.admin import admin_bp


    app.register_blueprint(auth_bp, url_prefix='/api/auth')
    app.register_blueprint(medical_bp, url_prefix='/api/medical')
    app.register_blueprint(medicines_bp, url_prefix='/api/medicines')
    app.register_blueprint(orders_bp, url_prefix='/api/orders')
    app.register_blueprint(admin_bp, url_prefix='/api/admin')


    # Serve frontend pages
    @app.route('/')
    def serve_index():
        return send_from_directory(frontend_dir, 'index.html')

    @app.route('/<path:path>')
    def serve_frontend(path):
        file_path = os.path.join(frontend_dir, path)
        if os.path.isfile(file_path):
            return send_from_directory(frontend_dir, path)
        return send_from_directory(frontend_dir, 'index.html')

    # Create tables and seed data
    with app.app_context():
        db.create_all()
        seed_data()

    return app


def seed_data():
    """Seed the database with initial data."""
    # Check if already seeded
    if Medicine.query.first():
        return

    # Create admin user
    admin = User(name='Admin', email='admin@medadvisor.com', is_admin=True)
    admin.set_password('admin123')
    db.session.add(admin)

    # Create demo user
    demo = User(name='Demo User', email='demo@medadvisor.com')
    demo.set_password('demo123')
    db.session.add(demo)

    # Seed medicines
    medicines = [
        Medicine(
            name="Paracetamol 500mg",
            generic_name="Acetaminophen",
            description="Pain reliever and fever reducer. Effective for headaches, muscle aches, arthritis, backache, toothaches, colds, and fevers.",
            category="Pain Relief",
            dosage="1-2 tablets every 4-6 hours. Max 8 tablets/day.",
            side_effects="Nausea, stomach pain, loss of appetite, headache",
            price=4.99,
            stock=200,
            image_url="💊",
            requires_prescription=False
        ),
        Medicine(
            name="Ibuprofen 200mg",
            generic_name="Ibuprofen",
            description="Nonsteroidal anti-inflammatory drug. Treats pain, fever, and inflammation from arthritis or injury.",
            category="Pain Relief",
            dosage="1 tablet every 4-6 hours with food. Max 3 tablets/day.",
            side_effects="Stomach upset, dizziness, mild heartburn",
            price=6.49,
            stock=150,
            image_url="💊",
            requires_prescription=False
        ),
        Medicine(
            name="Cetirizine 10mg",
            generic_name="Cetirizine Hydrochloride",
            description="Antihistamine for allergies. Relieves sneezing, itchy eyes, runny nose, and hives.",
            category="Allergy",
            dosage="1 tablet daily in the evening.",
            side_effects="Drowsiness, dry mouth, fatigue",
            price=5.99,
            stock=180,
            image_url="🤧",
            requires_prescription=False
        ),
        Medicine(
            name="Omeprazole 20mg",
            generic_name="Omeprazole",
            description="Proton pump inhibitor. Treats heartburn, acid reflux, and stomach ulcers.",
            category="Digestive",
            dosage="1 capsule daily before breakfast for 14 days.",
            side_effects="Headache, nausea, diarrhea, stomach pain",
            price=8.99,
            stock=120,
            image_url="💚",
            requires_prescription=False
        ),
        Medicine(
            name="Dextromethorphan Syrup",
            generic_name="Dextromethorphan",
            description="Cough suppressant that reduces the urge to cough. For dry, irritating coughs.",
            category="Cough & Cold",
            dosage="10ml every 4 hours. Max 60ml/day.",
            side_effects="Dizziness, drowsiness, nausea",
            price=7.49,
            stock=90,
            image_url="🍯",
            requires_prescription=False
        ),
        Medicine(
            name="Loratadine 10mg",
            generic_name="Loratadine",
            description="Non-drowsy antihistamine for allergy relief. 24-hour effectiveness.",
            category="Allergy",
            dosage="1 tablet daily.",
            side_effects="Headache, dry mouth, fatigue",
            price=7.99,
            stock=160,
            image_url="🌸",
            requires_prescription=False
        ),
        Medicine(
            name="Antacid Tablets",
            generic_name="Calcium Carbonate",
            description="Fast-acting antacid for heartburn, acid indigestion, and sour stomach.",
            category="Digestive",
            dosage="1-2 tablets as needed after meals. Max 7 tablets/day.",
            side_effects="Constipation, gas",
            price=3.99,
            stock=250,
            image_url="💛",
            requires_prescription=False
        ),
        Medicine(
            name="Loperamide 2mg",
            generic_name="Loperamide",
            description="Anti-diarrheal medication. Controls symptoms of diarrhea.",
            category="Digestive",
            dosage="2 capsules initially, then 1 after each loose stool. Max 8/day.",
            side_effects="Constipation, dizziness, nausea",
            price=5.49,
            stock=100,
            image_url="💊",
            requires_prescription=False
        ),
        Medicine(
            name="Hydrocortisone Cream 1%",
            generic_name="Hydrocortisone",
            description="Topical anti-itch cream. Treats skin irritation, rashes, eczema, and insect bites.",
            category="Skin Care",
            dosage="Apply thin layer to affected area 1-2 times daily.",
            side_effects="Skin thinning with prolonged use",
            price=6.99,
            stock=80,
            image_url="🧴",
            requires_prescription=False
        ),
        Medicine(
            name="Vitamin C 500mg",
            generic_name="Ascorbic Acid",
            description="Immune system booster. Supports overall health and speeds recovery from colds.",
            category="Vitamins",
            dosage="1 tablet daily with food.",
            side_effects="Stomach upset at high doses",
            price=9.99,
            stock=300,
            image_url="🍊",
            requires_prescription=False
        ),
        Medicine(
            name="Melatonin 3mg",
            generic_name="Melatonin",
            description="Natural sleep aid supplement. Helps regulate sleep-wake cycles and supports healthy sleep.",
            category="Sleep & Wellness",
            dosage="1 tablet 30-60 minutes before bedtime.",
            side_effects="Daytime drowsiness, headache",
            price=8.49,
            stock=110,
            image_url="🌙",
            requires_prescription=False
        ),
        Medicine(
            name="ORS Sachets (Pack of 10)",
            generic_name="Oral Rehydration Salts",
            description="Electrolyte replacement for dehydration due to diarrhea, vomiting, or illness.",
            category="Digestive",
            dosage="1 sachet dissolved in 1 liter of clean water. Sip frequently.",
            side_effects="Very safe when prepared correctly",
            price=4.49,
            stock=200,
            image_url="💧",
            requires_prescription=False
        ),
        Medicine(
            name="Throat Lozenges (Pack of 24)",
            generic_name="Amylmetacresol / Dichlorobenzyl Alcohol",
            description="Soothing throat lozenges for sore throat relief with antiseptic action.",
            category="Cough & Cold",
            dosage="1 lozenge every 2-3 hours. Max 12/day.",
            side_effects="Mild mouth irritation",
            price=5.99,
            stock=140,
            image_url="🍬",
            requires_prescription=False
        ),
        Medicine(
            name="Diclofenac Gel 1%",
            generic_name="Diclofenac Sodium",
            description="Topical NSAID gel for joint and muscle pain relief. Reduces inflammation.",
            category="Pain Relief",
            dosage="Apply to affected area 3-4 times daily.",
            side_effects="Skin irritation at application site",
            price=9.49,
            stock=70,
            image_url="🩹",
            requires_prescription=False
        ),
        Medicine(
            name="Multivitamin Daily",
            generic_name="Multivitamin Complex",
            description="Complete daily multivitamin with essential vitamins and minerals for overall health.",
            category="Vitamins",
            dosage="1 tablet daily with breakfast.",
            side_effects="Mild stomach upset if taken without food",
            price=12.99,
            stock=180,
            image_url="✨",
            requires_prescription=False
        ),
        Medicine(
            name="Calamine Lotion",
            generic_name="Calamine / Zinc Oxide",
            description="Soothing lotion for itchy skin, sunburn, insect bites, and minor skin irritations.",
            category="Skin Care",
            dosage="Apply to affected area as needed.",
            side_effects="Rarely causes side effects",
            price=4.29,
            stock=90,
            image_url="🧴",
            requires_prescription=False
        ),
        Medicine(
            name="Magnesium 400mg",
            generic_name="Magnesium Glycinate",
            description="Supports muscle relaxation, sleep quality, and stress relief. Essential mineral supplement.",
            category="Sleep & Wellness",
            dosage="1 capsule daily with food, preferably in the evening.",
            side_effects="Loose stools at high doses",
            price=10.99,
            stock=130,
            image_url="💫",
            requires_prescription=False
        ),
        Medicine(
            name="Nasal Saline Spray",
            generic_name="Sodium Chloride Solution",
            description="Natural saline spray for nasal congestion relief. Moisturizes dry nasal passages.",
            category="Cough & Cold",
            dosage="2-3 sprays in each nostril as needed.",
            side_effects="None known",
            price=6.49,
            stock=160,
            image_url="💨",
            requires_prescription=False
        )
    ]

    for medicine in medicines:
        db.session.add(medicine)

    # Import medicines from medicine_master.csv
    csv_path = os.path.join(os.path.dirname(__file__), 'data', 'medicine_master.csv')
    if os.path.exists(csv_path):
        with open(csv_path, 'r', encoding='utf-8') as f:
            reader = csv.DictReader(f)
            csv_count = 0
            for row in reader:
                price = float(row['price']) if row['price'] else 0.0
                if price <= 0:
                    continue  # Skip invalid entries

                stock = int(float(row['stock'])) if row['stock'] else 0
                requires_rx = row.get('prescription_required', 'No').strip() == 'Yes'

                med = Medicine(
                    name=row['medicine_name'].strip(),
                    generic_name='',
                    description='',
                    category='General',
                    dosage='',
                    side_effects='',
                    price=price,
                    stock=stock,
                    image_url='💊',
                    requires_prescription=requires_rx
                )
                db.session.add(med)
                csv_count += 1
        print(f"[OK] Imported {csv_count} medicines from CSV.")
    else:
        print("[WARN] medicine_master.csv not found, skipping CSV import.")

    db.session.commit()
    print("[OK] Database seeded successfully!")


if __name__ == '__main__':
    app = create_app()
    app.run(debug=True, port=5000)
