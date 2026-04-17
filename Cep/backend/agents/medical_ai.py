"""Medical AI agent that predicts diseases and recommends medicines from symptoms."""

import csv
import os
import random
import re
from collections import Counter, defaultdict
from pathlib import Path

from agents.disease_predictor import DiseasePredictor


ORDER_KEYWORDS = [
    "order",
    "buy",
    "purchase",
    "i want",
    "i need",
    "get me",
    "can i get",
    "i d like",
    "give me",
    "need to order",
    "want to buy",
]
ORDER_NOISE_TOKENS = {
    "order",
    "buy",
    "purchase",
    "want",
    "need",
    "get",
    "give",
    "tablet",
    "tablets",
    "pill",
    "pills",
    "unit",
    "units",
    "box",
    "boxes",
    "pack",
    "packs",
    "capsule",
    "capsules",
    "bottle",
    "bottles",
}

GREETING_KEYWORDS = [
    "hello",
    "hi",
    "hey",
    "good morning",
    "good afternoon",
    "good evening",
    "howdy",
    "hola",
    "sup",
    "what s up",
    "greetings",
]
THANK_KEYWORDS = ["thank", "thanks", "thx", "appreciate", "helpful", "great help"]
BYE_KEYWORDS = ["bye", "goodbye", "see you", "take care", "later", "goodnight"]
HELP_KEYWORDS = ["help", "what can you do", "how does this work", "what do you do", "how to use"]
FEELING_KEYWORDS = ["not feeling well", "feel sick", "feeling bad", "unwell", "not well", "feel terrible", "feeling awful", "feel awful"]

EMPATHY_SINGLE = [
    "I am sorry you are not feeling well. I checked your symptoms and here is the closest match.",
    "That sounds uncomfortable. I checked your symptoms against the trained predictor.",
    "I can help with that. Here are the strongest disease matches from the symptom model.",
]

EMPATHY_MULTIPLE = [
    "You mentioned multiple symptoms, so I used the trained model to rank likely diseases.",
    "There are several symptoms here, which helps the model narrow the disease ranking.",
    "I ran this symptom combination through the predictor and ranked the closest disease patterns.",
]

SYMPTOM_CATEGORY_HINTS = {
    "headache": ["Pain Relief"],
    "frontal headache": ["Pain Relief"],
    "muscle pain": ["Pain Relief"],
    "joint pain": ["Pain Relief"],
    "back pain": ["Pain Relief"],
    "low back pain": ["Pain Relief"],
    "ache all over": ["Pain Relief"],
    "fever": ["Cough & Cold", "Pain Relief"],
    "cough": ["Cough & Cold"],
    "sore throat": ["Cough & Cold"],
    "throat irritation": ["Cough & Cold"],
    "nasal congestion": ["Cough & Cold"],
    "sinus congestion": ["Cough & Cold"],
    "coryza": ["Cough & Cold"],
    "diarrhea": ["Digestive"],
    "nausea": ["Digestive"],
    "vomiting": ["Digestive"],
    "sharp abdominal pain": ["Digestive"],
    "burning abdominal pain": ["Digestive"],
    "heartburn": ["Digestive"],
    "stomach bloating": ["Digestive"],
    "skin rash": ["Skin Care"],
    "skin irritation": ["Skin Care"],
    "itching of skin": ["Skin Care", "Allergy"],
    "anxiety and nervousness": ["Sleep & Wellness"],
    "restlessness": ["Sleep & Wellness"],
    "insomnia": ["Sleep & Wellness"],
    "fatigue": ["Vitamins"],
    "weakness": ["Vitamins"],
    "sneezing": ["Allergy", "Cough & Cold"],
}

DISEASE_CATEGORY_HINTS = {
    "allergy": ["Allergy"],
    "eczema": ["Skin Care"],
    "dermatitis": ["Skin Care"],
    "rash": ["Skin Care"],
    "gastro": ["Digestive"],
    "diarrhea": ["Digestive"],
    "ulcer": ["Digestive"],
    "reflux": ["Digestive"],
    "sinus": ["Cough & Cold"],
    "cold": ["Cough & Cold"],
    "flu": ["Cough & Cold"],
    "bronch": ["Cough & Cold"],
    "pain": ["Pain Relief"],
    "arthritis": ["Pain Relief"],
    "migraine": ["Pain Relief"],
    "insomnia": ["Sleep & Wellness"],
    "anxiety": ["Sleep & Wellness"],
    "deficiency": ["Vitamins"],
}


class MedicalAIAgent:
    """Friendly wrapper around disease prediction and medicine recommendation."""

    DISCLAIMER = (
        "This is a machine learning prediction based on symptom patterns in the training data. "
        "It is not a medical diagnosis, and you should confirm any concern with a qualified clinician."
    )

    def __init__(self):
        self.predictor = DiseasePredictor()
        self.recommendation_data = self._load_recommendation_knowledge()

    @staticmethod
    def _contains_phrase(text, phrase):
        return f" {phrase} " in f" {text} "

    def _score_medicine_match(self, query_text, medicine):
        query_tokens = {
            token
            for token in self.predictor._tokenize(query_text)
            if not token.isdigit() and token not in ORDER_NOISE_TOKENS and len(token) >= 3
        }
        if not query_tokens:
            return 0.0

        name_key = self.predictor._normalize_text(medicine.name)
        generic_key = self.predictor._normalize_text(medicine.generic_name or "")
        combined_tokens = self.predictor._tokenize(f"{medicine.name} {medicine.generic_name or ''}")

        score = 0.0
        if name_key and name_key in query_text:
            score += 8.0
        if generic_key and generic_key in query_text:
            score += 6.0

        overlap = len(query_tokens.intersection(combined_tokens))
        score += overlap * 2.0

        for token in query_tokens:
            if token in combined_tokens:
                continue
            for med_token in combined_tokens:
                if len(token) >= 5 and len(med_token) >= 5 and token[:3] == med_token[:3]:
                    score += 0.4
                if self.predictor._edit_distance_limited(token, med_token, 2) <= 1:
                    score += 2.4
                    break
                if len(token) > 5 and self.predictor._edit_distance_limited(token, med_token, 2) <= 2:
                    score += 1.4
                    break

        return score

    def _recommendation_dataset_path(self):
        base_dir = Path(__file__).resolve().parents[1]
        local_data = base_dir / "data" / "medical_question_answer_dataset_50000.csv"
        download_data = Path("/Users/rutujabarde/Downloads/medical_question_answer_dataset_50000.csv")
        env_data = os.environ.get("MEDICAL_QA_DATASET_PATH")

        candidates = [Path(env_data) if env_data else None, local_data, download_data]
        for candidate in candidates:
            if candidate and candidate.exists():
                return candidate
        return None

    def _load_recommendation_knowledge(self):
        dataset_path = self._recommendation_dataset_path()
        if not dataset_path:
            return None

        disease_to_medicines = defaultdict(Counter)
        disease_to_advice = defaultdict(Counter)
        token_to_medicines = defaultdict(Counter)

        with dataset_path.open("r", newline="", encoding="utf-8-sig") as handle:
            reader = csv.DictReader(handle)
            for row in reader:
                disease = (row.get("Disease Prediction") or "").strip()
                medicine_text = (row.get("Recommended Medicines") or "").strip()
                advice = (row.get("Advice") or "").strip()
                symptom_question = (row.get("Symptoms/Question") or "").strip()

                if not disease:
                    continue

                disease_key = self.predictor._normalize_text(disease)
                medicines = self._split_medicines(medicine_text)
                if not medicines:
                    continue

                for medicine_name in medicines:
                    disease_to_medicines[disease_key][medicine_name] += 1

                if advice:
                    disease_to_advice[disease_key][advice] += 1

                for token in self.predictor._tokenize(symptom_question):
                    if len(token) < 4:
                        continue
                    for medicine_name in medicines:
                        token_to_medicines[token][medicine_name] += 1

        return {
            "path": str(dataset_path),
            "disease_to_medicines": disease_to_medicines,
            "disease_to_advice": disease_to_advice,
            "token_to_medicines": token_to_medicines,
        }

    @staticmethod
    def _split_medicines(medicine_text):
        if not medicine_text:
            return []
        parts = re.split(r",|;|\band\b", medicine_text, flags=re.IGNORECASE)
        unique = []
        seen = set()
        for part in parts:
            clean = re.sub(r"\s+", " ", part).strip(" .")
            if len(clean) < 2:
                continue
            key = clean.lower()
            if key in seen:
                continue
            seen.add(key)
            unique.append(clean)
        return unique

    def _check_order_intent(self, user_input_lower):
        """Detect if the user wants to order a medicine and find the best match."""
        has_order_intent = any(self._contains_phrase(user_input_lower, keyword) for keyword in ORDER_KEYWORDS)
        if not has_order_intent:
            return None

        quantity = 1
        qty_patterns = [
            r"(\d+)\s+(?:tablets?|pills?|units?|boxes?|packs?|capsules?|bottles?)",
            r"(?:order|buy|get|need|want)\s+(\d+)",
            r"(\d+)\s+\w",
        ]
        for pattern in qty_patterns:
            match = re.search(pattern, user_input_lower)
            if match:
                parsed_qty = int(match.group(1))
                if 1 <= parsed_qty <= 999:
                    quantity = parsed_qty
                    break

        medicine_query_text = user_input_lower
        medicine_query_text = re.sub(r"\b\d+\b", " ", medicine_query_text)
        medicine_query_text = re.sub(
            r"\b(order|buy|purchase|want|need|get|give|can i|get me|i want|i need|want to buy|need to order)\b",
            " ",
            medicine_query_text,
        )
        medicine_query_text = re.sub(r"\s+", " ", medicine_query_text).strip()

        from models import Medicine

        all_medicines = Medicine.query.all()
        best_match = None
        best_score = 0.0
        scored_candidates = []

        for medicine in all_medicines:
            score = self._score_medicine_match(medicine_query_text, medicine)
            if score > 0:
                scored_candidates.append((medicine, score))
            if score > best_score:
                best_match = medicine
                best_score = score

        scored_candidates.sort(key=lambda item: item[1], reverse=True)

        if not best_match or best_score < 1.5:
            suggestions = [candidate.name for candidate, score in scored_candidates[:3] if score >= 1.0]
            suggestion_text = ""
            if suggestions:
                suggestion_text = "\n\nDid you mean:\n" + "\n".join([f"• {name}" for name in suggestions])
            return {
                "success": False,
                "is_order": True,
                "message": (
                    "I can help place that order, but I could not confidently identify the medicine name.\n\n"
                    "Try something like:\n"
                    "• \"I want to order 5 Paracetamol\"\n"
                    "• \"Buy 2 Omeprazole\"\n"
                    "• \"I need 3 Cetirizine\"\n\n"
                    "You can also open the Medicine Shop and pick from the catalog."
                    f"{suggestion_text}"
                ).strip(),
                "disclaimer": self.DISCLAIMER,
            }

        total_price = best_match.price * quantity
        return {
            "success": True,
            "is_order": True,
            "medicine": best_match.to_dict(),
            "quantity": quantity,
            "requires_prescription": best_match.requires_prescription,
            "message": (
                f"I found **{best_match.name}** in the pharmacy.\n\n"
                f"Price: Rs {best_match.price:.2f} each\n"
                f"Quantity: **{quantity}**\n"
                f"Total: **Rs {total_price:.2f}**\n"
                f"In Stock: {best_match.stock} units\n"
                f"{'Prescription required' if best_match.requires_prescription else 'No prescription needed'}"
            ),
            "disclaimer": self.DISCLAIMER,
        }

    def _check_casual_chat(self, user_input_lower):
        """Handle greetings, thanks, and general conversation."""
        if any(self._contains_phrase(user_input_lower, keyword) for keyword in GREETING_KEYWORDS):
            return {
                "success": False,
                "is_chat": True,
                "message": (
                    "Hello! I can analyze symptoms with a trained disease predictor, show likely diseases, "
                    "and suggest medicines you can order.\n\n"
                    "Try messages like:\n"
                    "• \"I have a headache and fever\"\n"
                    "• \"My throat is sore and I am coughing\"\n"
                    "• \"I cannot sleep and feel anxious\"\n"
                    "• \"I want to order Paracetamol\""
                ),
                "disclaimer": self.DISCLAIMER,
            }

        if any(self._contains_phrase(user_input_lower, keyword) for keyword in THANK_KEYWORDS):
            return {
                "success": False,
                "is_chat": True,
                "message": "You are welcome. If symptoms persist or worsen, please see a doctor.",
                "disclaimer": self.DISCLAIMER,
            }

        if any(self._contains_phrase(user_input_lower, keyword) for keyword in BYE_KEYWORDS):
            return {
                "success": False,
                "is_chat": True,
                "message": "Take care. I am here any time you want to check symptoms or place an order.",
                "disclaimer": self.DISCLAIMER,
            }

        if any(self._contains_phrase(user_input_lower, keyword) for keyword in HELP_KEYWORDS):
            return {
                "success": False,
                "is_chat": True,
                "message": (
                    "I can do two things here:\n"
                    "• Predict likely diseases from symptoms\n"
                    "• Suggest medicines and let you order from the pharmacy\n\n"
                    "The more specific your symptoms are, the better the ranking."
                ),
                "disclaimer": self.DISCLAIMER,
            }

        if any(self._contains_phrase(user_input_lower, keyword) for keyword in FEELING_KEYWORDS):
            return {
                "success": False,
                "is_chat": True,
                "message": "I am sorry you are feeling unwell. Share exact symptoms and I will suggest diseases and medicines.",
                "disclaimer": self.DISCLAIMER,
            }

        return None

    def _category_recommendations(self, matched_symptoms, disease_predictions):
        from models import Medicine

        category_scores = Counter()

        for symptom in matched_symptoms:
            symptom_key = self.predictor._normalize_text(symptom)
            for category in SYMPTOM_CATEGORY_HINTS.get(symptom_key, []):
                category_scores[category] += 3

        for prediction in disease_predictions:
            disease_key = self.predictor._normalize_text(prediction.get("disease", ""))
            weight = max(prediction.get("match_score", 0.0), 1.0) / 20.0
            for keyword, categories in DISEASE_CATEGORY_HINTS.items():
                if keyword in disease_key:
                    for category in categories:
                        category_scores[category] += weight

        top_categories = [name for name, _score in category_scores.most_common(3)]
        query = Medicine.query.filter(Medicine.stock > 0).filter(Medicine.requires_prescription.is_(False))
        if top_categories:
            query = query.filter(Medicine.category.in_(top_categories))
        medicines = query.order_by(Medicine.price.asc()).limit(5).all()

        suggestions = []
        for medicine in medicines:
            reason = f"Catalog suggestion for {medicine.category or 'General'} symptom relief"
            suggestions.append(self._format_shop_suggestion(medicine, reason))
        return suggestions

    @staticmethod
    def _format_shop_suggestion(medicine, reason):
        return {
            "name": medicine.name,
            "generic_name": medicine.generic_name or "",
            "category": medicine.category or "General",
            "dosage": medicine.dosage or "Use as directed by label/doctor.",
            "price": round(float(medicine.price), 2),
            "requires_prescription": bool(medicine.requires_prescription),
            "in_shop": True,
            "medicine_id": medicine.id,
            "reason": reason,
        }

    @staticmethod
    def _format_external_suggestion(name, reason):
        return {
            "name": name,
            "generic_name": "",
            "category": "General",
            "dosage": "Consult label/doctor before use.",
            "price": None,
            "requires_prescription": None,
            "in_shop": False,
            "medicine_id": None,
            "reason": reason,
        }

    def _match_catalog_by_name(self, suggested_name, catalog):
        suggested_key = self.predictor._normalize_text(suggested_name)
        best = None
        best_score = 0

        for medicine in catalog:
            name_key = self.predictor._normalize_text(medicine.name)
            generic_key = self.predictor._normalize_text(medicine.generic_name or "")

            if suggested_key in name_key or name_key in suggested_key:
                score = min(len(suggested_key), len(name_key))
                if score > best_score:
                    best = medicine
                    best_score = score
            if generic_key and (suggested_key in generic_key or generic_key in suggested_key):
                score = min(len(suggested_key), len(generic_key))
                if score > best_score:
                    best = medicine
                    best_score = score

        return best

    def _recommend_medicines(self, user_input, matched_symptoms, disease_predictions):
        from models import Medicine

        medicine_scores = Counter()
        medicine_reasons = defaultdict(set)
        advice_scores = Counter()

        if self.recommendation_data:
            disease_to_medicines = self.recommendation_data["disease_to_medicines"]
            disease_to_advice = self.recommendation_data["disease_to_advice"]
            token_to_medicines = self.recommendation_data["token_to_medicines"]

            for prediction in disease_predictions[:3]:
                disease_name = prediction.get("disease", "")
                disease_key = self.predictor._normalize_text(disease_name)
                weight = max(prediction.get("match_score", 0.0), 1.0) / 10.0

                for medicine_name, frequency in disease_to_medicines.get(disease_key, Counter()).most_common(15):
                    medicine_scores[medicine_name] += weight * frequency
                    medicine_reasons[medicine_name].add(f"Commonly used for {disease_name}")

                for advice, frequency in disease_to_advice.get(disease_key, Counter()).most_common(5):
                    advice_scores[advice] += weight * frequency

            for token in self.predictor._tokenize(user_input):
                if len(token) < 4:
                    continue
                for medicine_name, frequency in token_to_medicines.get(token, Counter()).most_common(12):
                    medicine_scores[medicine_name] += 0.25 * frequency
                    medicine_reasons[medicine_name].add(f"Related to symptom keyword '{token}'")

        suggestions = []
        seen_shop_ids = set()
        seen_external_names = set()
        catalog = Medicine.query.filter(Medicine.stock > 0).all()

        for medicine_name, _score in medicine_scores.most_common(16):
            match = self._match_catalog_by_name(medicine_name, catalog)
            reason = "; ".join(sorted(medicine_reasons[medicine_name])) or "Suggested from symptom-treatment data"

            if match:
                if match.id in seen_shop_ids:
                    continue
                seen_shop_ids.add(match.id)
                suggestions.append(self._format_shop_suggestion(match, reason))
            else:
                key = self.predictor._normalize_text(medicine_name)
                if key in seen_external_names:
                    continue
                seen_external_names.add(key)
                suggestions.append(self._format_external_suggestion(medicine_name, reason))

            if len(suggestions) >= 6:
                break

        if not suggestions:
            suggestions = self._category_recommendations(matched_symptoms, disease_predictions)

        care_advice = [advice for advice, _score in advice_scores.most_common(3)]
        if not care_advice and matched_symptoms:
            care_advice = [
                "Stay hydrated and rest as much as possible.",
                "Follow medicine labels carefully and avoid self-medicating beyond recommended doses.",
            ]

        return suggestions, care_advice

    def analyze_symptoms(self, user_input):
        """Analyze symptoms with disease prediction and medicine recommendation."""
        user_input_lower = self.predictor._normalize_text(user_input)

        if not user_input_lower:
            return {
                "success": False,
                "message": "Type the symptoms you are having and I will suggest diseases and medicines.",
                "disclaimer": self.DISCLAIMER,
            }

        order_response = self._check_order_intent(user_input_lower)
        if order_response:
            return order_response

        chat_response = self._check_casual_chat(user_input_lower)
        if chat_response:
            return chat_response

        try:
            prediction = self.predictor.predict(user_input)
        except FileNotFoundError as error:
            return {
                "success": False,
                "message": str(error),
                "disclaimer": self.DISCLAIMER,
            }

        matched_symptoms = prediction["matched_symptoms"]
        disease_predictions = prediction["predictions"]

        if not matched_symptoms:
            return {
                "success": False,
                "message": (
                    "I could not confidently map your text to known symptoms.\n\n"
                    "Try being more explicit, for example:\n"
                    "• \"I have fever, cough, and sore throat\"\n"
                    "• \"I feel anxious, dizzy, and shortness of breath\"\n"
                    "• \"I have a skin rash with itching\"\n"
                    "• \"I have stomach pain, nausea, and diarrhea\""
                ),
                "disclaimer": self.DISCLAIMER,
            }

        medicine_suggestions, care_advice = self._recommend_medicines(user_input, matched_symptoms, disease_predictions)

        empathy_message = random.choice(EMPATHY_MULTIPLE if len(matched_symptoms) > 1 else EMPATHY_SINGLE)
        follow_up = None
        if len(matched_symptoms) < 2:
            follow_up = "Add one or two more symptoms if possible. The model gets more reliable with richer details."

        return {
            "success": True,
            "empathy_message": empathy_message,
            "symptoms_detected": matched_symptoms,
            "results": disease_predictions,
            "medicine_suggestions": medicine_suggestions,
            "care_advice": care_advice,
            "urgent_warning": prediction["urgent_warning"],
            "follow_up": follow_up,
            "model": prediction["model"],
            "disclaimer": self.DISCLAIMER,
        }

    def get_supported_symptoms(self):
        """Return list of symptom features available in the trained disease dataset."""
        try:
            return self.predictor.get_supported_symptoms()
        except FileNotFoundError:
            return []


medical_agent = MedicalAIAgent()
