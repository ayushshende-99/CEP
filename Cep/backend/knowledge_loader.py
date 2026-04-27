"""Dataset loader for symptom->disease->medicine pharmacy workflows."""

from __future__ import annotations

import csv
import os
import re
from collections import defaultdict
from pathlib import Path

from models import db, DiseaseMedicine, Medicine, SymptomKnowledge

DATASET_ENV = "SYMPTOM_DATASET_PATH"
DATASET_FILENAME = "dataset_with_severity_and_prescription.csv"
TRUE_VALUES = {"1", "true", "yes", "y"}


def _normalize_text(value: str) -> str:
    value = (value or "").lower()
    value = re.sub(r"[^a-z0-9\s]", " ", value)
    return re.sub(r"\s+", " ", value).strip()


def _split_medicines(value: str) -> list[str]:
    if not value:
        return []
    parts = [item.strip() for item in value.split(",")]
    return [item for item in parts if item]


def resolve_symptom_dataset_path(dataset_path: str | None = None) -> Path | None:
    base_dir = Path(__file__).resolve().parent
    data_dir = base_dir / "data"
    env_path = os.environ.get(DATASET_ENV)

    candidates = [
        Path(dataset_path) if dataset_path else None,
        Path(env_path) if env_path else None,
        data_dir / DATASET_FILENAME,
        Path.home() / "Downloads" / DATASET_FILENAME,
    ]

    for candidate in candidates:
        if candidate and candidate.exists():
            return candidate

    return None


def load_symptom_knowledge(dataset_path: str | None = None) -> tuple[dict, Path]:
    resolved_path = resolve_symptom_dataset_path(dataset_path)
    if not resolved_path:
        raise FileNotFoundError(
            "Symptom dataset was not found. Set SYMPTOM_DATASET_PATH or place "
            f"{DATASET_FILENAME} in backend/data."
        )

    symptom_rows: list[dict] = []
    disease_medicine_map: dict[tuple[str, str], bool] = {}

    with resolved_path.open("r", newline="", encoding="utf-8-sig") as handle:
        reader = csv.DictReader(handle)
        for row in reader:
            symptom_text = (row.get("Symptoms/Question") or "").strip()
            disease_name = (row.get("Disease Prediction") or "").strip()
            severity = ((row.get("severity") or "unknown").strip() or "unknown").lower()
            advice = (row.get("Advice") or "").strip()
            needs_rx_text = (row.get("needs_prescription") or "").strip().lower()
            needs_rx = needs_rx_text in TRUE_VALUES

            if not symptom_text or not disease_name:
                continue

            symptom_rows.append(
                {
                    "symptom_text": symptom_text,
                    "symptom_text_normalized": _normalize_text(symptom_text),
                    "disease_name": disease_name,
                    "severity": severity if severity in {"mild", "serious", "unknown"} else "unknown",
                    "advice": advice,
                }
            )

            for medicine_name in _split_medicines((row.get("Recommended Medicines") or "").strip()):
                key = (disease_name, medicine_name)
                current = disease_medicine_map.get(key, False)
                disease_medicine_map[key] = current or needs_rx

    db.session.query(SymptomKnowledge).delete()
    db.session.query(DiseaseMedicine).delete()

    for row in symptom_rows:
        db.session.add(SymptomKnowledge(**row))

    for (disease_name, medicine_name), requires_prescription in disease_medicine_map.items():
        db.session.add(
            DiseaseMedicine(
                disease_name=disease_name,
                medicine_name=medicine_name,
                requires_prescription=requires_prescription,
            )
        )

    existing_name_map = {
        medicine.name.strip().lower(): medicine
        for medicine in Medicine.query.all()
        if medicine.name
    }
    avg_price = db.session.query(db.func.avg(Medicine.price)).scalar() or 100.0
    avg_stock = db.session.query(db.func.avg(Medicine.stock)).scalar() or 50

    for (_disease_name, medicine_name), requires_prescription in disease_medicine_map.items():
        key = medicine_name.strip().lower()
        existing = existing_name_map.get(key)
        if existing:
            existing.requires_prescription = existing.requires_prescription or requires_prescription
            continue

        new_medicine = Medicine(
            name=medicine_name,
            generic_name=medicine_name,
            description=f"Dataset-linked medicine for {medicine_name}",
            category="Dataset",
            dosage="Use as advised by clinician or pharmacist.",
            side_effects="Refer to package insert and pharmacist guidance.",
            price=round(float(avg_price), 2),
            stock=max(int(avg_stock), 1),
            image_url="💊",
            requires_prescription=requires_prescription,
        )
        db.session.add(new_medicine)
        existing_name_map[key] = new_medicine

    stats = {
        "symptom_rows": len(symptom_rows),
        "disease_medicine_rows": len(disease_medicine_map),
        "medicines_total": Medicine.query.count(),
    }

    return stats, resolved_path
