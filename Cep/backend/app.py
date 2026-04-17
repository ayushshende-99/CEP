"""
Smart Agentic Medical Advisor & Pharmacy - Main Flask Application
"""

from flask import Flask, send_from_directory
from flask_cors import CORS
from config import Config
from models import db, User, Medicine
from catalog_loader import load_medicine_catalog
import os


LEGACY_CATALOG_MARKERS = {
    "Antacid Tablets",
    "Calamine Lotion",
    "Dextromethorphan Syrup",
    "Melatonin 3mg",
    "Multivitamin Daily",
    "Nasal Saline Spray",
    "ORS Sachets (Pack of 10)",
}


def create_app():
    frontend_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "frontend"))
    app = Flask(__name__, static_folder=None)
    app.config.from_object(Config)

    CORS(app)

    upload_folder = os.path.join(os.path.dirname(__file__), "uploads", "prescriptions")
    app.config["UPLOAD_FOLDER"] = upload_folder
    app.config["MAX_CONTENT_LENGTH"] = 5 * 1024 * 1024
    os.makedirs(upload_folder, exist_ok=True)

    db.init_app(app)

    from routes.auth import auth_bp
    from routes.medical import medical_bp
    from routes.medicines import medicines_bp
    from routes.orders import orders_bp
    from routes.admin import admin_bp

    app.register_blueprint(auth_bp, url_prefix="/api/auth")
    app.register_blueprint(medical_bp, url_prefix="/api/medical")
    app.register_blueprint(medicines_bp, url_prefix="/api/medicines")
    app.register_blueprint(orders_bp, url_prefix="/api/orders")
    app.register_blueprint(admin_bp, url_prefix="/api/admin")

    @app.route("/")
    def serve_index():
        return send_from_directory(frontend_dir, "index.html")

    @app.route("/<path:path>")
    def serve_frontend(path):
        file_path = os.path.join(frontend_dir, path)
        if os.path.isfile(file_path):
            return send_from_directory(frontend_dir, path)
        return send_from_directory(frontend_dir, "index.html")

    with app.app_context():
        db.create_all()
        seed_data()

    return app


def ensure_default_users():
    """Create default users if they do not exist yet."""
    admin = User.query.filter_by(email="admin@medadvisor.com").first()
    if not admin:
        admin = User(name="Admin", email="admin@medadvisor.com", is_admin=True)
        admin.set_password("admin123")
        db.session.add(admin)

    demo = User.query.filter_by(email="demo@medadvisor.com").first()
    if not demo:
        demo = User(name="Demo User", email="demo@medadvisor.com")
        demo.set_password("demo123")
        db.session.add(demo)


def medicine_catalog_needs_refresh():
    """Refresh when the DB is empty or still contains the legacy hardcoded catalog."""
    current_names = {name for (name,) in db.session.query(Medicine.name).all()}
    if not current_names:
        return True

    return any(name in LEGACY_CATALOG_MARKERS for name in current_names)


def refresh_medicine_catalog():
    """Load the medicine catalog from the dataset and replace the legacy seed data."""
    catalog_rows, dataset_path = load_medicine_catalog()

    db.session.query(Medicine).delete()
    for row in catalog_rows:
        db.session.add(Medicine(**row))

    print(
        f"[OK] Imported {len(catalog_rows)} medicines from dataset: {dataset_path}"
    )


def seed_data():
    """Seed users and load the medicine catalog."""
    ensure_default_users()

    if medicine_catalog_needs_refresh():
        try:
            refresh_medicine_catalog()
        except FileNotFoundError as error:
            if Medicine.query.count() == 0:
                raise
            print(f"[WARN] {error}. Keeping the existing medicine catalog.")
    else:
        print("[OK] Medicine catalog already initialized; keeping existing records.")

    db.session.commit()
    print("[OK] Database seeded successfully!")


if __name__ == "__main__":
    app = create_app()
    app.run(debug=True, port=5000)
