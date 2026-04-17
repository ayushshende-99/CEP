"""Dataset-trained disease prediction engine."""

from __future__ import annotations

import csv
import math
import os
import pickle
import re
from collections import Counter
from pathlib import Path
from typing import Dict, List, Optional


STOPWORDS = {
    "a",
    "an",
    "and",
    "are",
    "at",
    "be",
    "been",
    "but",
    "do",
    "does",
    "feel",
    "feeling",
    "felt",
    "for",
    "got",
    "had",
    "has",
    "have",
    "having",
    "i",
    "im",
    "in",
    "is",
    "it",
    "its",
    "ive",
    "me",
    "my",
    "of",
    "on",
    "really",
    "since",
    "that",
    "the",
    "there",
    "to",
    "very",
    "was",
    "with",
}


COMMON_ALIASES = {
    "headache": ["headache", "frontal headache"],
    "head pain": ["headache", "frontal headache"],
    "migraine": ["headache", "frontal headache"],
    "feverish": ["fever", "feeling hot", "feeling hot and cold", "chills"],
    "temperature": ["fever"],
    "high temperature": ["fever"],
    "cold": ["nasal congestion", "coryza", "sneezing"],
    "runny nose": ["nasal congestion", "coryza"],
    "stuffy nose": ["nasal congestion", "sinus congestion"],
    "blocked nose": ["nasal congestion", "sinus congestion"],
    "coughing": ["cough"],
    "short of breath": ["shortness of breath", "difficulty breathing"],
    "breathless": ["shortness of breath", "difficulty breathing"],
    "sore throat": ["sore throat", "throat irritation"],
    "scratchy throat": ["sore throat", "throat irritation"],
    "throat hurts": ["sore throat", "throat irritation"],
    "stomach pain": ["sharp abdominal pain"],
    "stomach ache": ["sharp abdominal pain"],
    "stomach hurts": ["sharp abdominal pain"],
    "belly pain": ["sharp abdominal pain"],
    "abdominal pain": ["sharp abdominal pain"],
    "heartburn": ["heartburn", "burning abdominal pain"],
    "acid reflux": ["heartburn", "burning chest pain"],
    "bloating": ["stomach bloating", "abdominal distention"],
    "bloated": ["stomach bloating", "abdominal distention"],
    "throwing up": ["vomiting"],
    "threw up": ["vomiting"],
    "puking": ["vomiting"],
    "loose motion": ["diarrhea"],
    "loose motions": ["diarrhea"],
    "loose stool": ["diarrhea"],
    "body pain": ["ache all over", "muscle pain", "joint pain"],
    "body ache": ["ache all over", "muscle pain"],
    "aches all over": ["ache all over", "muscle pain"],
    "muscle ache": ["muscle pain"],
    "joint ache": ["joint pain"],
    "backache": ["back pain", "low back pain"],
    "cant sleep": ["insomnia"],
    "cannot sleep": ["insomnia"],
    "trouble sleeping": ["insomnia"],
    "not sleeping": ["insomnia"],
    "sleep problem": ["insomnia"],
    "anxious": ["anxiety and nervousness", "restlessness"],
    "anxiety": ["anxiety and nervousness", "restlessness"],
    "panic attack": ["anxiety and nervousness", "palpitations", "shortness of breath"],
    "stressed": ["anxiety and nervousness", "restlessness"],
    "stress": ["anxiety and nervousness", "restlessness"],
    "tired": ["fatigue"],
    "exhausted": ["fatigue", "weakness"],
    "drained": ["fatigue", "weakness"],
    "weak": ["weakness"],
    "rash": ["skin rash", "skin irritation"],
    "itching": ["itching of skin", "skin irritation"],
    "itchy skin": ["itching of skin", "skin irritation"],
}


RED_FLAG_SYMPTOMS = {
    "blood in stool",
    "blood in urine",
    "difficulty breathing",
    "fainting",
    "hemoptysis",
    "loss of sensation",
    "rectal bleeding",
    "seizures",
    "sharp chest pain",
    "shortness of breath",
    "slurring words",
    "vomiting blood",
}


class DiseasePredictor:
    """Train and serve a Bernoulli Naive Bayes model from the symptom dataset."""

    def __init__(self, dataset_path: Optional[str] = None, cache_path: Optional[str] = None, top_k: int = 3):
        base_dir = Path(__file__).resolve().parents[1]
        data_dir = base_dir / "data"
        self.dataset_path_override = Path(dataset_path) if dataset_path else None
        self.local_dataset_path = data_dir / "Final_Augmented_dataset_Diseases_and_Symptoms.csv"
        self.download_dataset_path = Path.home() / "Downloads" / "Final_Augmented_dataset_Diseases_and_Symptoms.csv"
        self.cache_path = Path(cache_path) if cache_path else data_dir / "disease_prediction_model.pkl"
        self.top_k = top_k

        self.model = None
        self.symptom_columns: List[str] = []
        self.symptom_indices: Dict[str, int] = {}
        self.normalized_symptom_lookup: Dict[str, str] = {}
        self.symptom_tokens: Dict[str, set[str]] = {}
        self.token_to_symptoms: Dict[str, set[str]] = {}
        self.alias_map: Dict[str, List[str]] = {}
        self.schema_loaded = False

    @staticmethod
    def _normalize_text(text: str) -> str:
        text = text.lower().replace(".1", "")
        text = re.sub(r"[^a-z0-9\s]", " ", text)
        return re.sub(r"\s+", " ", text).strip()

    @staticmethod
    def _singularize(token: str) -> str:
        if len(token) > 4 and token.endswith("ies"):
            return token[:-3] + "y"
        if len(token) > 4 and token.endswith("s"):
            return token[:-1]
        return token

    def _tokenize(self, text: str) -> set[str]:
        tokens = set()
        for raw_token in self._normalize_text(text).split():
            token = self._singularize(raw_token)
            if token and token not in STOPWORDS:
                tokens.add(token)
        return tokens

    @staticmethod
    def _edit_distance_limited(a: str, b: str, max_distance: int = 2) -> int:
        """Compute edit distance with an early cutoff for speed."""
        if a == b:
            return 0
        if abs(len(a) - len(b)) > max_distance:
            return max_distance + 1

        prev_row = list(range(len(b) + 1))
        for i, ca in enumerate(a, start=1):
            current_row = [i]
            min_in_row = i
            for j, cb in enumerate(b, start=1):
                insert_cost = current_row[j - 1] + 1
                delete_cost = prev_row[j] + 1
                replace_cost = prev_row[j - 1] + (0 if ca == cb else 1)
                cost = min(insert_cost, delete_cost, replace_cost)
                current_row.append(cost)
                if cost < min_in_row:
                    min_in_row = cost

            if min_in_row > max_distance:
                return max_distance + 1
            prev_row = current_row

        return prev_row[-1]

    def _token_fuzzy_match(self, token: str, input_tokens: set[str]) -> bool:
        if token in input_tokens:
            return True

        if len(token) <= 4:
            max_distance = 1
        else:
            max_distance = 2

        for input_token in input_tokens:
            if abs(len(input_token) - len(token)) > max_distance:
                continue
            if self._edit_distance_limited(token, input_token, max_distance) <= max_distance:
                return True
        return False

    def _semantic_symptom_scores(self, input_tokens: set[str], seen: set[str]) -> List[tuple[str, float]]:
        scores: List[tuple[str, float]] = []
        candidate_symptoms = set()

        for token in input_tokens:
            candidate_symptoms.update(self.token_to_symptoms.get(token, set()))

        if not candidate_symptoms:
            candidate_symptoms = set(self.symptom_columns)

        for symptom in candidate_symptoms:
            if symptom in seen:
                continue

            symptom_tokens = self.symptom_tokens.get(symptom, set())
            if not symptom_tokens:
                continue

            exact_overlap = len(symptom_tokens.intersection(input_tokens))
            fuzzy_overlap = 0
            if exact_overlap < len(symptom_tokens):
                for token in symptom_tokens:
                    if token in input_tokens:
                        continue
                    if self._token_fuzzy_match(token, input_tokens):
                        fuzzy_overlap += 1

            total_overlap = exact_overlap + (0.6 * fuzzy_overlap)
            score = total_overlap / max(len(symptom_tokens), 1)

            if exact_overlap > 0 and len(symptom_tokens) > 1:
                score += 0.1

            if score >= 0.55:
                scores.append((symptom, score))

        scores.sort(key=lambda item: item[1], reverse=True)
        return scores

    def _resolve_dataset_path(self) -> Path:
        env_path = os.environ.get("MEDICAL_DATASET_PATH")
        candidates = [
            self.dataset_path_override,
            Path(env_path) if env_path else None,
            self.local_dataset_path,
            self.download_dataset_path,
        ]

        for candidate in candidates:
            if candidate and candidate.exists():
                return candidate

        raise FileNotFoundError(
            "Disease prediction dataset was not found. Set MEDICAL_DATASET_PATH or place "
            "Final_Augmented_dataset_Diseases_and_Symptoms.csv in backend/data."
        )

    def _load_schema(self) -> None:
        if self.schema_loaded:
            return

        dataset_path = self._resolve_dataset_path()
        with dataset_path.open("r", newline="", encoding="utf-8-sig") as handle:
            reader = csv.reader(handle)
            header = next(reader)

        self.symptom_columns = [column.replace(".1", "").strip() for column in header[1:]]
        self.symptom_indices = {symptom: index for index, symptom in enumerate(self.symptom_columns)}
        self.normalized_symptom_lookup = {
            self._normalize_text(symptom): symptom for symptom in self.symptom_columns
        }
        self.symptom_tokens = {
            symptom: self._tokenize(symptom) for symptom in self.symptom_columns
        }
        self.token_to_symptoms = {}
        for symptom, tokens in self.symptom_tokens.items():
            for token in tokens:
                if token not in self.token_to_symptoms:
                    self.token_to_symptoms[token] = set()
                self.token_to_symptoms[token].add(symptom)

        self.alias_map = {}
        for alias, targets in COMMON_ALIASES.items():
            available_targets = [target for target in targets if target in self.symptom_indices]
            if available_targets:
                self.alias_map[self._normalize_text(alias)] = available_targets

        self.schema_loaded = True

    def _cache_matches_dataset(self, payload: dict, dataset_path: Path) -> bool:
        stats = dataset_path.stat()
        return (
            payload.get("dataset_path") == str(dataset_path)
            and payload.get("dataset_mtime") == stats.st_mtime
            and payload.get("dataset_size") == stats.st_size
        )

    def _load_cached_model(self, dataset_path: Path) -> Optional[dict]:
        if not self.cache_path.exists():
            return None

        try:
            with self.cache_path.open("rb") as handle:
                payload = pickle.load(handle)
        except Exception:
            return None

        if not self._cache_matches_dataset(payload, dataset_path):
            return None

        return payload

    def _train_model(self, dataset_path: Path) -> dict:
        class_counts: Counter[str] = Counter()
        positive_counts: Dict[str, List[int]] = {}

        with dataset_path.open("r", newline="", encoding="utf-8-sig") as handle:
            reader = csv.reader(handle)
            header = next(reader)
            symptom_columns = [column.replace(".1", "").strip() for column in header[1:]]
            feature_count = len(symptom_columns)
            total_rows = 0

            for row in reader:
                if not row:
                    continue

                disease = row[0].strip()
                if not disease:
                    continue

                class_counts[disease] += 1
                total_rows += 1
                counts_for_disease = positive_counts.setdefault(disease, [0] * feature_count)

                for index, value in enumerate(row[1 : feature_count + 1]):
                    if value == "1":
                        counts_for_disease[index] += 1

        diseases = sorted(class_counts)
        base_scores = {}
        feature_weights = {}

        for disease in diseases:
            disease_count = class_counts[disease]
            disease_positive_counts = positive_counts[disease]

            base_score = math.log(disease_count / total_rows)
            weights = [0.0] * len(symptom_columns)

            for index, positive_count in enumerate(disease_positive_counts):
                probability = (positive_count + 1.0) / (disease_count + 2.0)
                log_absent = math.log(1.0 - probability)
                base_score += log_absent
                weights[index] = math.log(probability) - log_absent

            base_scores[disease] = base_score
            feature_weights[disease] = weights

        stats = dataset_path.stat()
        return {
            "dataset_path": str(dataset_path),
            "dataset_mtime": stats.st_mtime,
            "dataset_size": stats.st_size,
            "model_name": "Bernoulli Naive Bayes",
            "row_count": total_rows,
            "disease_count": len(diseases),
            "feature_count": len(symptom_columns),
            "symptom_columns": symptom_columns,
            "diseases": diseases,
            "class_counts": dict(class_counts),
            "base_scores": base_scores,
            "feature_weights": feature_weights,
        }

    def _ensure_model(self) -> dict:
        if self.model is not None:
            return self.model

        self._load_schema()
        dataset_path = self._resolve_dataset_path()
        payload = self._load_cached_model(dataset_path)

        if payload is None:
            payload = self._train_model(dataset_path)
            self.cache_path.parent.mkdir(parents=True, exist_ok=True)
            with self.cache_path.open("wb") as handle:
                pickle.dump(payload, handle)

        self.model = payload
        self.symptom_columns = payload["symptom_columns"]
        self.symptom_indices = {symptom: index for index, symptom in enumerate(self.symptom_columns)}
        self.normalized_symptom_lookup = {
            self._normalize_text(symptom): symptom for symptom in self.symptom_columns
        }
        self.symptom_tokens = {
            symptom: self._tokenize(symptom) for symptom in self.symptom_columns
        }
        self.token_to_symptoms = {}
        for symptom, tokens in self.symptom_tokens.items():
            for token in tokens:
                if token not in self.token_to_symptoms:
                    self.token_to_symptoms[token] = set()
                self.token_to_symptoms[token].add(symptom)
        self.schema_loaded = True
        return self.model

    def get_supported_symptoms(self) -> List[str]:
        self._load_schema()
        return self.symptom_columns

    def extract_symptoms(self, user_input: str) -> List[str]:
        self._load_schema()
        normalized_input = self._normalize_text(user_input)
        input_tokens = self._tokenize(user_input)

        matches: List[str] = []
        seen = set()

        def add_match(symptom: str) -> None:
            if symptom in self.symptom_indices and symptom not in seen:
                matches.append(symptom)
                seen.add(symptom)

        for alias, targets in self.alias_map.items():
            if alias in normalized_input:
                for target in targets:
                    add_match(target)

        exact_candidates = sorted(
            self.normalized_symptom_lookup.items(),
            key=lambda item: len(item[0]),
            reverse=True,
        )
        for normalized_symptom, original_symptom in exact_candidates:
            if len(normalized_symptom) >= 4 and normalized_symptom in normalized_input:
                add_match(original_symptom)

        for symptom, symptom_tokens in self.symptom_tokens.items():
            if symptom in seen or not symptom_tokens:
                continue

            if len(symptom_tokens) == 1:
                token = next(iter(symptom_tokens))
                if token in input_tokens:
                    add_match(symptom)
                continue

            if len(symptom_tokens) <= 4 and symptom_tokens.issubset(input_tokens):
                add_match(symptom)

        if len(matches) < 8 and input_tokens:
            semantic_matches = self._semantic_symptom_scores(input_tokens, seen)
            for symptom, _score in semantic_matches:
                add_match(symptom)
                if len(matches) >= 8:
                    break

        return matches[:8]

    def predict(self, user_input: str, top_k: Optional[int] = None) -> dict:
        model = self._ensure_model()
        matched_symptoms = self.extract_symptoms(user_input)

        if not matched_symptoms:
            return {
                "matched_symptoms": [],
                "predictions": [],
                "model": self.get_model_info(),
                "urgent_warning": None,
            }

        active_indices = [self.symptom_indices[symptom] for symptom in matched_symptoms]
        scored_predictions = []

        for disease in model["diseases"]:
            score = model["base_scores"][disease]
            weights = model["feature_weights"][disease]
            for index in active_indices:
                score += weights[index]
            scored_predictions.append((disease, score))

        scored_predictions.sort(key=lambda item: item[1], reverse=True)
        top_k = top_k or self.top_k
        top_predictions = scored_predictions[:top_k]

        max_global_score = max(score for _, score in scored_predictions)
        global_exp_scores = {
            disease: math.exp(score - max_global_score) for disease, score in scored_predictions
        }
        global_total = sum(global_exp_scores.values())

        max_top_score = max(score for _, score in top_predictions)
        top_exp_scores = {
            disease: math.exp(score - max_top_score) for disease, score in top_predictions
        }
        top_total = sum(top_exp_scores.values())

        formatted_predictions = []
        for disease, score in top_predictions:
            supporting_symptoms = sorted(
                matched_symptoms,
                key=lambda symptom: model["feature_weights"][disease][self.symptom_indices[symptom]],
                reverse=True,
            )
            formatted_predictions.append(
                {
                    "disease": disease.title(),
                    "match_score": round((top_exp_scores[disease] / top_total) * 100, 1),
                    "probability": round((global_exp_scores[disease] / global_total) * 100, 3),
                    "supporting_symptoms": [symptom.title() for symptom in supporting_symptoms[:5]],
                }
            )

        red_flags = [symptom.title() for symptom in matched_symptoms if symptom in RED_FLAG_SYMPTOMS]
        urgent_warning = None
        if red_flags:
            urgent_warning = (
                "Some of the symptoms you mentioned can need urgent medical attention: "
                + ", ".join(red_flags)
                + ". Please contact a clinician promptly."
            )

        return {
            "matched_symptoms": [symptom.title() for symptom in matched_symptoms],
            "predictions": formatted_predictions,
            "model": self.get_model_info(),
            "urgent_warning": urgent_warning,
        }

    def get_model_info(self) -> dict:
        model = self._ensure_model()
        return {
            "name": model["model_name"],
            "rows": model["row_count"],
            "diseases": model["disease_count"],
            "symptom_features": model["feature_count"],
            "dataset_path": model["dataset_path"],
        }
