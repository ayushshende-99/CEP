import json
import importlib
import os
import re
from collections import defaultdict
from datetime import datetime

from flask import current_app
from sqlalchemy import or_
from werkzeug.utils import secure_filename

from models import (
    db,
    DiseaseMedicine,
    Medicine,
    Order,
    PharmacistRequest,
    PrescriptionSubmission,
    SymptomKnowledge,
)


class PharmacyAI:
    REJECTION_REASONS = {"out_of_stock", "invalid_prescription", "not_available"}
    SYMPTOM_STOPWORDS = {
        "a", "an", "and", "are", "at", "be", "for", "from", "have", "i", "im", "is",
        "it", "my", "of", "on", "or", "the", "to", "with", "you", "your",
    }

    @staticmethod
    def _normalize_text(value: str) -> str:
        value = (value or "").lower()
        value = re.sub(r"[^a-z0-9\s]", " ", value)
        return re.sub(r"\s+", " ", value).strip()

    def _score_symptom_row(self, symptoms: list[str], row: SymptomKnowledge) -> float:
        row_tokens = set(self._normalize_text(row.symptom_text).split())
        if not row_tokens:
            return 0.0

        score = 0.0
        for symptom in symptoms:
            symptom_norm = self._normalize_text(symptom)
            if not symptom_norm:
                continue
            symptom_tokens = set(symptom_norm.split())
            if not symptom_tokens:
                continue
            if symptom_norm in row.symptom_text_normalized:
                score += 2.5
            overlap = len(symptom_tokens.intersection(row_tokens))
            score += overlap

        return score

    def _parse_symptoms_input(self, symptoms_input) -> list[str]:
        if isinstance(symptoms_input, list):
            base_items = [str(item).strip() for item in symptoms_input if str(item).strip()]
            merged_text = " ".join(base_items)
        elif isinstance(symptoms_input, str):
            merged_text = symptoms_input.strip()
            base_items = [item.strip() for item in re.split(r"[,;\n]+", merged_text) if item.strip()]
        else:
            return []

        terms: list[str] = []
        if merged_text:
            terms.append(merged_text)

        terms.extend(base_items)

        normalized_tokens = self._normalize_text(merged_text).split()
        token_terms = [
            token
            for token in normalized_tokens
            if len(token) >= 3 and token not in self.SYMPTOM_STOPWORDS
        ]
        terms.extend(token_terms)

        unique_terms: list[str] = []
        seen: set[str] = set()
        for term in terms:
            normalized = self._normalize_text(term)
            if not normalized or normalized in seen:
                continue
            seen.add(normalized)
            unique_terms.append(term)

        return unique_terms

    def create_pharmacist_request(
        self,
        *,
        user_id: int,
        request_type: str,
        status: str = "pending",
        severity: str | None = None,
        disease_name: str | None = None,
        reason: str | None = None,
        message: str | None = None,
        order_id: int | None = None,
        prescription_submission_id: int | None = None,
        context_data: dict | None = None,
    ) -> PharmacistRequest:
        request_row = PharmacistRequest(
            user_id=user_id,
            request_type=request_type,
            status=status,
            severity=severity,
            disease_name=disease_name,
            reason=reason,
            message=message,
            order_id=order_id,
            prescription_submission_id=prescription_submission_id,
            context_data=json.dumps(context_data or {}),
        )
        db.session.add(request_row)
        db.session.flush()
        return request_row

    def analyze_symptoms_flow(self, *, user_id: int, symptoms_input):
        symptoms = self._parse_symptoms_input(symptoms_input)

        if not symptoms:
            return {
                "success": False,
                "message": "Please provide a list of symptoms.",
            }, 400

        symptom_filters = []
        for symptom in symptoms:
            symptom_norm = self._normalize_text(symptom)
            if not symptom_norm:
                continue
            if len(symptom_norm) < 3 and " " not in symptom_norm:
                continue
            symptom_filters.append(SymptomKnowledge.symptom_text_normalized.ilike(f"%{symptom_norm}%"))

        if symptom_filters:
            candidate_rows = SymptomKnowledge.query.filter(or_(*symptom_filters)).limit(3000).all()
        else:
            candidate_rows = []

        if not candidate_rows:
            req = self.create_pharmacist_request(
                user_id=user_id,
                request_type="unknown_symptoms_review",
                severity="unknown",
                message="No dataset match for provided symptoms.",
                context_data={"symptoms": symptoms},
            )
            db.session.commit()
            return {
                "success": True,
                "severity": "unknown",
                "message": "Symptoms are uncertain. Pharmacist review has been requested.",
                "pharmacist_request": req.to_dict(),
            }, 200

        disease_scores = defaultdict(lambda: {"score": 0.0, "rows": []})
        for row in candidate_rows:
            score = self._score_symptom_row(symptoms, row)
            key = f"{row.disease_name}::{row.severity}"
            disease_scores[key]["score"] += score
            disease_scores[key]["rows"].append(row)

        ranked = sorted(
            disease_scores.items(),
            key=lambda item: item[1]["score"],
            reverse=True,
        )

        if not ranked or ranked[0][1]["score"] <= 0:
            req = self.create_pharmacist_request(
                user_id=user_id,
                request_type="unknown_symptoms_review",
                severity="unknown",
                message="Low confidence symptom mapping.",
                context_data={"symptoms": symptoms},
            )
            db.session.commit()
            return {
                "success": True,
                "severity": "unknown",
                "message": "Symptoms are uncertain. Pharmacist review has been requested.",
                "pharmacist_request": req.to_dict(),
            }, 200

        top_key, top_data = ranked[0]
        disease_name, severity = top_key.split("::", 1)
        advice = top_data["rows"][0].advice if top_data["rows"] else ""

        if severity == "serious":
            return {
                "success": True,
                "severity": severity,
                "disease": disease_name,
                "message": "Consult doctor",
                "advice": advice,
            }, 200

        if severity == "unknown":
            req = self.create_pharmacist_request(
                user_id=user_id,
                request_type="severity_unknown_review",
                severity=severity,
                disease_name=disease_name,
                message="Predicted severity is unknown.",
                context_data={"symptoms": symptoms, "advice": advice},
            )
            db.session.commit()
            return {
                "success": True,
                "severity": severity,
                "disease": disease_name,
                "message": "Severity is unknown. Pharmacist review requested.",
                "advice": advice,
                "pharmacist_request": req.to_dict(),
            }, 200

        disease_medicines = DiseaseMedicine.query.filter_by(disease_name=disease_name).all()
        otc_medicines = []
        prescription_medicines = []

        for disease_medicine in disease_medicines:
            medicine = Medicine.query.filter(Medicine.name.ilike(disease_medicine.medicine_name)).first()
            requires_rx = disease_medicine.requires_prescription or (medicine.requires_prescription if medicine else False)

            entry = {
                "name": disease_medicine.medicine_name,
                "requires_prescription": requires_rx,
                "medicine_id": medicine.id if medicine else None,
            }
            if medicine:
                entry["catalog"] = medicine.to_dict()

            if requires_rx:
                prescription_medicines.append(entry)
            else:
                otc_medicines.append(entry)

        response = {
            "success": True,
            "severity": severity,
            "disease": disease_name,
            "advice": advice,
            "otc_medicines": otc_medicines,
            "prescription_medicines": prescription_medicines,
        }

        if prescription_medicines:
            response["message"] = "Prescription medicines found. Upload prescription to continue."
            response["requires_prescription_upload"] = True
        else:
            response["message"] = "OTC medicines available for this disease."

        db.session.commit()
        return response, 200

    def extract_prescription_text(self, file_path: str) -> tuple[str, str]:
        extension = os.path.splitext(file_path)[1].lower()

        if extension in {".txt", ".csv", ".md"}:
            with open(file_path, "r", encoding="utf-8", errors="ignore") as handle:
                text = handle.read().strip()
            if text:
                return "readable", text
            return "unreadable", ""

        if extension == ".pdf":
            try:
                pdf_module = importlib.import_module("pypdf")
                PdfReader = getattr(pdf_module, "PdfReader")
                reader = PdfReader(file_path)
                text = "\n".join((page.extract_text() or "") for page in reader.pages).strip()
                if text:
                    return "readable", text
            except Exception:
                return "unreadable", ""
            return "unreadable", ""

        if extension in {".png", ".jpg", ".jpeg", ".bmp", ".gif", ".webp"}:
            try:
                pytesseract = importlib.import_module("pytesseract")
                pil_image = importlib.import_module("PIL.Image")
                image = pil_image.open(file_path)
                text = pytesseract.image_to_string(image).strip()
                if text:
                    return "readable", text
            except Exception:
                return "unreadable", ""
            return "unreadable", ""

        return "unreadable", ""

    def handle_prescription_upload(self, *, user_id: int, medicine_id: int, upload_file):
        medicine = Medicine.query.get(medicine_id)
        if not medicine:
            return {"success": False, "message": "Medicine not found"}, 404

        upload_folder = current_app.config.get("UPLOAD_FOLDER", "uploads/prescriptions")
        os.makedirs(upload_folder, exist_ok=True)

        filename = secure_filename(upload_file.filename)
        timestamp = datetime.utcnow().strftime("%Y%m%d_%H%M%S")
        final_name = f"rx_{user_id}_{timestamp}_{filename}"
        file_path = os.path.join(upload_folder, final_name)
        upload_file.save(file_path)

        extraction_status, extracted_text = self.extract_prescription_text(file_path)
        extracted_text_norm = self._normalize_text(extracted_text)
        medicine_name_norm = self._normalize_text(medicine.name)

        submission = PrescriptionSubmission(
            user_id=user_id,
            medicine_id=medicine.id,
            file_path=file_path,
            extracted_text=extracted_text,
            extraction_status=extraction_status,
            validation_status="pending",
        )
        db.session.add(submission)
        db.session.flush()

        if extraction_status == "unreadable":
            submission.validation_status = "escalated"
            req = self.create_pharmacist_request(
                user_id=user_id,
                request_type="unreadable_prescription_review",
                prescription_submission_id=submission.id,
                message="Prescription OCR unreadable. Pharmacist review required.",
                context_data={"medicine_id": medicine.id, "medicine_name": medicine.name},
            )
            db.session.commit()
            return {
                "success": True,
                "prescription_readable": False,
                "message": "Prescription unreadable. Sent to pharmacist for review.",
                "prescription_submission": submission.to_dict(),
                "pharmacist_request": req.to_dict(),
            }, 200

        if medicine_name_norm and medicine_name_norm in extracted_text_norm:
            submission.validation_status = "approved"
            db.session.commit()
            return {
                "success": True,
                "prescription_readable": True,
                "prescription_valid": True,
                "message": "Prescription is machine-readable and valid.",
                "prescription_submission": submission.to_dict(),
            }, 200

        submission.validation_status = "rejected"
        submission.pharmacist_note = "Medicine name not found in extracted prescription text."
        db.session.commit()
        return {
            "success": False,
            "prescription_readable": True,
            "prescription_valid": False,
            "message": "Prescription is readable but invalid for this medicine.",
            "prescription_submission": submission.to_dict(),
        }, 400

    def medicine_search_flow(self, *, user_id: int, medicine_name: str, prescription_submission_id=None):
        medicine = Medicine.query.filter(Medicine.name.ilike(f"%{medicine_name}%")).first()

        if not medicine:
            return {
                "success": False,
                "available": False,
                "message": "Medicine unavailable",
            }, 404

        if not medicine.requires_prescription:
            return {
                "success": True,
                "available": True,
                "allow_order": True,
                "medicine": medicine.to_dict(),
                "message": "Medicine available. No prescription needed.",
            }, 200

        if not prescription_submission_id:
            return {
                "success": False,
                "available": True,
                "allow_order": False,
                "requires_prescription": True,
                "message": "Prescription required. Upload prescription first.",
            }, 400

        submission = PrescriptionSubmission.query.filter_by(
            id=prescription_submission_id,
            user_id=user_id,
            medicine_id=medicine.id,
        ).first()

        if not submission:
            return {
                "success": False,
                "allow_order": False,
                "message": "Prescription submission not found for this medicine.",
            }, 404

        if submission.validation_status == "approved":
            return {
                "success": True,
                "available": True,
                "allow_order": True,
                "medicine": medicine.to_dict(),
                "prescription_submission": submission.to_dict(),
                "message": "Prescription is valid. Order is allowed.",
            }, 200

        if submission.extraction_status == "unreadable" or submission.validation_status == "escalated":
            req = self.create_pharmacist_request(
                user_id=user_id,
                request_type="medicine_search_prescription_review",
                prescription_submission_id=submission.id,
                message="Unreadable prescription during medicine search.",
                context_data={"medicine_id": medicine.id, "medicine_name": medicine.name},
            )
            db.session.commit()
            return {
                "success": True,
                "available": True,
                "allow_order": False,
                "sent_to_pharmacist": True,
                "prescription_submission": submission.to_dict(),
                "pharmacist_request": req.to_dict(),
                "message": "Prescription unreadable. Sent to pharmacist.",
            }, 202

        return {
            "success": False,
            "allow_order": False,
            "message": "Prescription invalid. Order rejected.",
            "prescription_submission": submission.to_dict(),
        }, 400

    def create_order_verification_request(self, order: Order):
        request_row = self.create_pharmacist_request(
            user_id=order.user_id,
            request_type="order_verification",
            order_id=order.id,
            message="New order requires pharmacist verification.",
            context_data={
                "tracking_id": order.tracking_id,
                "order_status": order.status,
                "total_price": order.total_price,
            },
        )
        return request_row


pharmacy_ai = PharmacyAI()
