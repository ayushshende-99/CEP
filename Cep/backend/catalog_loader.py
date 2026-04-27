"""Utilities for loading the pharmacy catalog from a CSV dataset."""

from __future__ import annotations

import csv
import os
import re
from pathlib import Path
from statistics import mean


MEDICINE_DATASET_ENV = "MEDICINE_DATASET_PATH"
MEDICINE_DATASET_FILENAME = "dataset_with_severity_and_prescription.csv"

BOOLEAN_TRUE_VALUES = {"1", "true", "yes", "y"}

CATEGORY_KEYWORDS = {
    "Pain Relief": {"diclofenac", "ibuprofen", "naproxen", "paracetamol"},
    "Allergy": {"cetirizine", "levocetirizine", "loratadine"},
    "Cough & Cold": {"montelukast", "salbutamol"},
    "Digestive": {"omeprazole", "pantoprazole"},
    "Antibiotics": {"amoxicillin", "azithromycin", "ciprofloxacin"},
    "Diabetes": {"insulin", "metformin"},
    "Cardiovascular": {"amlodipine", "atorvastatin"},
    "Skin Care": {"hydrocortisone"},
    "Steroid & Inflammation": {"prednisone"},
}

CATEGORY_IMAGES = {
    "Pain Relief": "💊",
    "Allergy": "🌿",
    "Cough & Cold": "🫁",
    "Digestive": "🫃",
    "Antibiotics": "🧫",
    "Diabetes": "🩸",
    "Cardiovascular": "❤️",
    "Skin Care": "🧴",
    "Steroid & Inflammation": "🛡️",
    "General": "💊",
}

CATEGORY_SIDE_EFFECTS = {
    "Pain Relief": "May cause stomach upset, nausea, or dizziness.",
    "Allergy": "May cause drowsiness, dry mouth, or mild fatigue.",
    "Cough & Cold": "May cause tremor, headache, or restlessness.",
    "Digestive": "May cause headache, nausea, or abdominal discomfort.",
    "Antibiotics": "May cause nausea, diarrhea, or stomach discomfort.",
    "Diabetes": "Monitor blood sugar closely and follow clinician guidance.",
    "Cardiovascular": "May cause dizziness, fatigue, or swelling in some patients.",
    "Skin Care": "May cause skin irritation or thinning with prolonged use.",
    "Steroid & Inflammation": "Use carefully, as prolonged use can cause swelling or stomach upset.",
    "General": "Use carefully and review the label for side effects.",
}


def _normalize_text(value: str) -> str:
    value = value.lower()
    value = re.sub(r"[^a-z0-9\s]", " ", value)
    return re.sub(r"\s+", " ", value).strip()


def _extract_strength(name: str) -> str:
    match = re.search(r"\b\d+(?:\.\d+)?\s*(?:mg|mcg|g|ml)\b", name, flags=re.IGNORECASE)
    return match.group(0) if match else ""


def _strip_strength(name: str) -> str:
    stripped = re.sub(r"\b\d+(?:\.\d+)?\s*(?:mg|mcg|g|ml)\b", "", name, flags=re.IGNORECASE)
    return re.sub(r"\s+", " ", stripped).strip(" -")


def resolve_medicine_dataset_path(dataset_path: str | None = None) -> Path | None:
    """Resolve the CSV path for the medicine catalog dataset."""
    base_dir = Path(__file__).resolve().parent
    data_dir = base_dir / "data"
    env_path = os.environ.get(MEDICINE_DATASET_ENV)

    candidates = [
        Path(dataset_path) if dataset_path else None,
        Path(env_path) if env_path else None,
        data_dir / MEDICINE_DATASET_FILENAME,
        Path.home() / "Downloads" / MEDICINE_DATASET_FILENAME,
    ]

    for candidate in candidates:
        if candidate and candidate.exists():
            return candidate

    return None


def _infer_category(base_name: str) -> str:
    normalized = _normalize_text(base_name)
    for category, keywords in CATEGORY_KEYWORDS.items():
        if any(keyword in normalized for keyword in keywords):
            return category
    return "General"


def _infer_description(base_name: str, category: str, requires_prescription: bool) -> str:
    prescription_clause = (
        " Use only with clinician guidance."
        if requires_prescription
        else " Follow the pack label or pharmacist advice."
    )

    templates = {
        "Pain Relief": f"{base_name} is commonly used for pain and inflammation support.",
        "Allergy": f"{base_name} is commonly used for allergy symptom relief such as sneezing and itching.",
        "Cough & Cold": f"{base_name} is commonly used for breathing or respiratory symptom support.",
        "Digestive": f"{base_name} is commonly used for acidity or stomach-related symptom support.",
        "Antibiotics": f"{base_name} is an antibacterial medicine used when prescribed for infections.",
        "Diabetes": f"{base_name} is commonly used to support blood sugar management.",
        "Cardiovascular": f"{base_name} is commonly used to support blood pressure or cholesterol management.",
        "Skin Care": f"{base_name} is commonly used for skin irritation and inflammatory flare-ups.",
        "Steroid & Inflammation": f"{base_name} is commonly used to reduce inflammation and immune overactivity.",
        "General": f"{base_name} is available in the pharmacy catalog for guided symptom support.",
    }

    return templates.get(category, templates["General"]) + prescription_clause


def _infer_dosage(name: str, requires_prescription: bool) -> str:
    strength = _extract_strength(name)
    if requires_prescription:
        if strength:
            return f"Use {strength} exactly as prescribed by your clinician."
        return "Use exactly as prescribed by your clinician."

    if strength:
        return f"Follow the label directions for the {strength} strength."
    return "Follow the label directions or pharmacist guidance."


def _infer_stock(occurrences: int, requires_prescription: bool) -> int:
    baseline = 24 if requires_prescription else 40
    return min(baseline + (occurrences * 12), 120)


def load_medicine_catalog(dataset_path: str | None = None) -> tuple[list[dict], Path]:
    """Load and normalize the medicine catalog from the CSV dataset."""
    resolved_path = resolve_medicine_dataset_path(dataset_path)
    if not resolved_path:
        raise FileNotFoundError(
            "Medicine catalog dataset was not found. Set MEDICINE_DATASET_PATH or place "
            f"{MEDICINE_DATASET_FILENAME} in backend/data."
        )

    grouped_rows: dict[str, dict] = {}

    with resolved_path.open("r", newline="", encoding="utf-8-sig") as handle:
        reader = csv.DictReader(handle)
        for row in reader:
            medicine_name = (row.get("medicine_name") or "").strip()
            price_text = (row.get("price") or "").strip()
            if not medicine_name or not price_text:
                continue

            try:
                price = float(price_text)
            except ValueError:
                continue

            if price <= 0:
                continue

            key = _normalize_text(medicine_name)
            current = grouped_rows.setdefault(
                key,
                {
                    "name": medicine_name,
                    "prices": [],
                    "requires_prescription": False,
                    "occurrences": 0,
                },
            )
            current["prices"].append(price)
            current["occurrences"] += 1
            current["requires_prescription"] = current["requires_prescription"] or (
                (row.get("prescription_required") or "").strip().lower() in BOOLEAN_TRUE_VALUES
            )

    catalog = []
    for entry in sorted(grouped_rows.values(), key=lambda item: item["name"].lower()):
        generic_name = _strip_strength(entry["name"]) or entry["name"]
        category = _infer_category(generic_name)
        catalog.append(
            {
                "name": entry["name"],
                "generic_name": generic_name,
                "description": _infer_description(
                    generic_name,
                    category,
                    entry["requires_prescription"],
                ),
                "category": category,
                "dosage": _infer_dosage(entry["name"], entry["requires_prescription"]),
                "side_effects": CATEGORY_SIDE_EFFECTS.get(category, CATEGORY_SIDE_EFFECTS["General"]),
                "price": round(mean(entry["prices"]), 2),
                "stock": _infer_stock(entry["occurrences"], entry["requires_prescription"]),
                "image_url": CATEGORY_IMAGES.get(category, CATEGORY_IMAGES["General"]),
                "requires_prescription": entry["requires_prescription"],
            }
        )

    return catalog, resolved_path
