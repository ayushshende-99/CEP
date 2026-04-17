# Medical AI Agent - Rule-based symptom analysis engine

MEDICAL_DATABASE = {
    "headache": {
        "conditions": ["Tension Headache", "Migraine", "Sinusitis", "Dehydration"],
        "medicines": [
            {
                "name": "Paracetamol (Tylenol)",
                "generic": "Acetaminophen",
                "dosage": "500mg-1000mg every 4-6 hours, max 4g/day",
                "usage": "Take with water, can be taken with or without food",
                "side_effects": ["Nausea", "Liver damage (overdose)"],
                "precautions": ["Avoid alcohol", "Do not exceed recommended dose"]
            },
            {
                "name": "Ibuprofen (Advil)",
                "generic": "Ibuprofen",
                "dosage": "200mg-400mg every 4-6 hours",
                "usage": "Take with food to reduce stomach upset",
                "side_effects": ["Stomach upset", "Dizziness", "Heartburn"],
                "precautions": ["Take with food", "Avoid if you have stomach ulcers"]
            }
        ],
        "home_remedies": ["Rest in a dark, quiet room", "Apply cold compress to forehead", "Stay hydrated", "Practice relaxation techniques"],
        "when_to_see_doctor": "If headache is severe, sudden, or accompanied by fever, stiff neck, confusion, or vision changes"
    },
    "fever": {
        "conditions": ["Common Cold", "Flu (Influenza)", "Viral Infection", "Bacterial Infection"],
        "medicines": [
            {
                "name": "Paracetamol (Tylenol)",
                "generic": "Acetaminophen",
                "dosage": "500mg-1000mg every 4-6 hours, max 4g/day",
                "usage": "Take with water for fever reduction",
                "side_effects": ["Nausea", "Liver damage (overdose)"],
                "precautions": ["Stay hydrated", "Do not exceed recommended dose"]
            },
            {
                "name": "Ibuprofen (Advil)",
                "generic": "Ibuprofen",
                "dosage": "200mg-400mg every 4-6 hours",
                "usage": "Take with food, helps reduce fever and inflammation",
                "side_effects": ["Stomach upset", "Dizziness"],
                "precautions": ["Take with food", "Not recommended for children under 6 months"]
            }
        ],
        "home_remedies": ["Rest and sleep", "Drink plenty of fluids", "Use a light blanket", "Sponge bath with lukewarm water"],
        "when_to_see_doctor": "If fever exceeds 103°F (39.4°C), lasts more than 3 days, or is accompanied by severe symptoms"
    },
    "cold": {
        "conditions": ["Common Cold", "Upper Respiratory Infection", "Allergic Rhinitis"],
        "medicines": [
            {
                "name": "Cetirizine (Zyrtec)",
                "generic": "Cetirizine Hydrochloride",
                "dosage": "10mg once daily",
                "usage": "Take in the evening, may cause drowsiness",
                "side_effects": ["Drowsiness", "Dry mouth", "Fatigue"],
                "precautions": ["Avoid driving if drowsy", "Avoid alcohol"]
            },
            {
                "name": "Phenylephrine (Sudafed PE)",
                "generic": "Phenylephrine",
                "dosage": "10mg every 4 hours, max 60mg/day",
                "usage": "Decongestant, take during the day",
                "side_effects": ["Insomnia", "Nervousness", "Increased blood pressure"],
                "precautions": ["Not for those with high blood pressure", "Avoid before bedtime"]
            },
            {
                "name": "Vitamin C Supplement",
                "generic": "Ascorbic Acid",
                "dosage": "500mg-1000mg daily",
                "usage": "Take with food to boost immunity",
                "side_effects": ["Stomach upset at high doses"],
                "precautions": ["Do not exceed 2000mg/day"]
            }
        ],
        "home_remedies": ["Steam inhalation", "Warm salt water gargle", "Honey and lemon in warm water", "Rest"],
        "when_to_see_doctor": "If symptoms last more than 10 days, or include high fever, severe sinus pain, or difficulty breathing"
    },
    "cough": {
        "conditions": ["Common Cold", "Bronchitis", "Allergies", "Post-nasal Drip"],
        "medicines": [
            {
                "name": "Dextromethorphan (Robitussin)",
                "generic": "Dextromethorphan",
                "dosage": "10-20mg every 4 hours or 30mg every 6-8 hours",
                "usage": "Cough suppressant, take as needed",
                "side_effects": ["Dizziness", "Drowsiness", "Nausea"],
                "precautions": ["Do not use with MAO inhibitors", "Avoid alcohol"]
            },
            {
                "name": "Honey & Lemon Cough Syrup",
                "generic": "Natural remedy",
                "dosage": "1-2 teaspoons as needed",
                "usage": "Soothes throat, natural cough relief",
                "side_effects": ["None for most adults"],
                "precautions": ["Not for children under 1 year"]
            }
        ],
        "home_remedies": ["Warm honey and lemon water", "Steam inhalation", "Keep head elevated while sleeping", "Stay hydrated"],
        "when_to_see_doctor": "If cough lasts more than 3 weeks, produces blood, or is accompanied by shortness of breath"
    },
    "stomach pain": {
        "conditions": ["Indigestion", "Gastritis", "Food Poisoning", "Acid Reflux (GERD)"],
        "medicines": [
            {
                "name": "Antacid (Tums/Maalox)",
                "generic": "Calcium Carbonate / Magnesium Hydroxide",
                "dosage": "1-2 tablets as needed after meals",
                "usage": "Chew tablets thoroughly, take after meals",
                "side_effects": ["Constipation", "Gas"],
                "precautions": ["Do not exceed recommended dose", "Not for prolonged use"]
            },
            {
                "name": "Omeprazole (Prilosec)",
                "generic": "Omeprazole",
                "dosage": "20mg once daily before breakfast",
                "usage": "Take 30 minutes before first meal of the day",
                "side_effects": ["Headache", "Nausea", "Diarrhea"],
                "precautions": ["Not for long-term use without doctor supervision", "May affect B12 absorption"]
            },
            {
                "name": "Simethicone (Gas-X)",
                "generic": "Simethicone",
                "dosage": "40-125mg after meals and at bedtime",
                "usage": "Relieves gas and bloating",
                "side_effects": ["Rarely causes side effects"],
                "precautions": ["Safe for most adults"]
            }
        ],
        "home_remedies": ["Ginger tea", "Peppermint tea", "Warm compress on abdomen", "BRAT diet (bananas, rice, applesauce, toast)"],
        "when_to_see_doctor": "If pain is severe, persistent, accompanied by vomiting blood, or black stools"
    },
    "sore throat": {
        "conditions": ["Pharyngitis", "Tonsillitis", "Common Cold", "Strep Throat"],
        "medicines": [
            {
                "name": "Throat Lozenges (Strepsils)",
                "generic": "Amylmetacresol/Dichlorobenzyl alcohol",
                "dosage": "1 lozenge every 2-3 hours",
                "usage": "Dissolve slowly in mouth",
                "side_effects": ["Mild mouth irritation"],
                "precautions": ["Do not exceed 12 lozenges per day"]
            },
            {
                "name": "Ibuprofen (Advil)",
                "generic": "Ibuprofen",
                "dosage": "200-400mg every 4-6 hours",
                "usage": "Reduces pain and inflammation",
                "side_effects": ["Stomach upset", "Dizziness"],
                "precautions": ["Take with food"]
            }
        ],
        "home_remedies": ["Warm salt water gargle", "Honey and warm water", "Rest your voice", "Use a humidifier"],
        "when_to_see_doctor": "If sore throat is severe, lasts more than a week, or is accompanied by difficulty swallowing or breathing"
    },
    "allergy": {
        "conditions": ["Allergic Rhinitis", "Hay Fever", "Seasonal Allergies", "Skin Allergy"],
        "medicines": [
            {
                "name": "Cetirizine (Zyrtec)",
                "generic": "Cetirizine",
                "dosage": "10mg once daily",
                "usage": "Take in the evening",
                "side_effects": ["Drowsiness", "Dry mouth"],
                "precautions": ["Avoid driving if drowsy"]
            },
            {
                "name": "Loratadine (Claritin)",
                "generic": "Loratadine",
                "dosage": "10mg once daily",
                "usage": "Non-drowsy antihistamine, take any time",
                "side_effects": ["Headache", "Dry mouth"],
                "precautions": ["Generally well-tolerated"]
            },
            {
                "name": "Fluticasone Nasal Spray (Flonase)",
                "generic": "Fluticasone Propionate",
                "dosage": "1-2 sprays per nostril once daily",
                "usage": "Shake well before use, spray into each nostril",
                "side_effects": ["Nasal irritation", "Nosebleed"],
                "precautions": ["Use regularly for best results"]
            }
        ],
        "home_remedies": ["Avoid known allergens", "Use HEPA air filters", "Nasal saline rinse", "Keep windows closed during high pollen times"],
        "when_to_see_doctor": "If symptoms are severe, don't respond to OTC medications, or you develop difficulty breathing"
    },
    "body pain": {
        "conditions": ["Muscle Strain", "Arthritis", "Fibromyalgia", "Overexertion"],
        "medicines": [
            {
                "name": "Ibuprofen (Advil)",
                "generic": "Ibuprofen",
                "dosage": "200-400mg every 4-6 hours",
                "usage": "Take with food for pain and inflammation",
                "side_effects": ["Stomach upset", "Dizziness"],
                "precautions": ["Take with food", "Avoid long-term use"]
            },
            {
                "name": "Diclofenac Gel (Voltaren)",
                "generic": "Diclofenac",
                "dosage": "Apply to affected area 3-4 times daily",
                "usage": "Topical pain relief, rub gently into skin",
                "side_effects": ["Skin irritation at application site"],
                "precautions": ["Do not apply to broken skin", "Wash hands after application"]
            },
            {
                "name": "Muscle Relaxant Balm",
                "generic": "Menthol/Methyl Salicylate",
                "dosage": "Apply to affected area as needed",
                "usage": "Massage gently into sore muscles",
                "side_effects": ["Skin irritation"],
                "precautions": ["For external use only", "Avoid contact with eyes"]
            }
        ],
        "home_remedies": ["Hot or cold compress", "Gentle stretching", "Epsom salt bath", "Rest the affected area"],
        "when_to_see_doctor": "If pain is severe, persistent, or accompanied by swelling, redness, or inability to move"
    },
    "diarrhea": {
        "conditions": ["Food Poisoning", "Viral Gastroenteritis", "IBS", "Bacterial Infection"],
        "medicines": [
            {
                "name": "Loperamide (Imodium)",
                "generic": "Loperamide",
                "dosage": "4mg initially, then 2mg after each loose stool, max 16mg/day",
                "usage": "Take with fluid to prevent dehydration",
                "side_effects": ["Constipation", "Abdominal cramps"],
                "precautions": ["Do not use if fever or bloody stools", "Stay hydrated"]
            },
            {
                "name": "ORS (Oral Rehydration Salts)",
                "generic": "Electrolyte Solution",
                "dosage": "1 sachet dissolved in 1 liter of clean water",
                "usage": "Sip frequently throughout the day",
                "side_effects": ["Very safe when prepared correctly"],
                "precautions": ["Use clean drinking water", "Discard after 24 hours"]
            }
        ],
        "home_remedies": ["BRAT diet", "Drink clear fluids", "Avoid dairy and fatty foods", "Probiotics (yogurt)"],
        "when_to_see_doctor": "If diarrhea lasts more than 2 days, contains blood, or you show signs of severe dehydration"
    },
    "skin rash": {
        "conditions": ["Contact Dermatitis", "Eczema", "Allergic Reaction", "Heat Rash"],
        "medicines": [
            {
                "name": "Hydrocortisone Cream (1%)",
                "generic": "Hydrocortisone",
                "dosage": "Apply thin layer to affected area 1-2 times daily",
                "usage": "For external use only, rub in gently",
                "side_effects": ["Skin thinning with prolonged use"],
                "precautions": ["Do not use on face for extended periods", "Not for infected areas"]
            },
            {
                "name": "Calamine Lotion",
                "generic": "Calamine/Zinc Oxide",
                "dosage": "Apply to affected area as needed",
                "usage": "Shake well, apply with cotton ball",
                "side_effects": ["Rarely causes side effects"],
                "precautions": ["For external use only"]
            },
            {
                "name": "Cetirizine (Zyrtec)",
                "generic": "Cetirizine",
                "dosage": "10mg once daily",
                "usage": "Oral antihistamine to reduce itching",
                "side_effects": ["Drowsiness", "Dry mouth"],
                "precautions": ["Avoid driving if drowsy"]
            }
        ],
        "home_remedies": ["Cool compress", "Oatmeal bath", "Aloe vera gel", "Avoid scratching"],
        "when_to_see_doctor": "If rash spreads rapidly, is accompanied by fever, or shows signs of infection"
    },
    "insomnia": {
        "conditions": ["Stress-related Insomnia", "Anxiety", "Poor Sleep Hygiene", "Caffeine Effects"],
        "medicines": [
            {
                "name": "Melatonin Supplement",
                "generic": "Melatonin",
                "dosage": "1-5mg 30-60 minutes before bedtime",
                "usage": "Take in a dark room before sleep",
                "side_effects": ["Daytime drowsiness", "Headache"],
                "precautions": ["Start with lowest dose", "Not for long-term use without guidance"]
            },
            {
                "name": "Diphenhydramine (Benadryl)",
                "generic": "Diphenhydramine",
                "dosage": "25-50mg at bedtime",
                "usage": "Take 30 minutes before desired sleep time",
                "side_effects": ["Drowsiness", "Dry mouth", "Dizziness"],
                "precautions": ["Not for regular use", "Avoid in elderly"]
            }
        ],
        "home_remedies": ["Maintain regular sleep schedule", "Avoid screens before bed", "Chamomile tea", "Dark, cool bedroom environment"],
        "when_to_see_doctor": "If insomnia persists for more than 4 weeks or significantly impacts daily life"
    },
    "anxiety": {
        "conditions": ["Generalized Anxiety", "Stress Response", "Panic Symptoms"],
        "medicines": [
            {
                "name": "Chamomile Tea Supplement",
                "generic": "Chamomile Extract",
                "dosage": "1-2 cups of tea or 200-400mg capsule daily",
                "usage": "Natural calming supplement",
                "side_effects": ["Rarely causes allergic reaction in people allergic to ragweed"],
                "precautions": ["Generally safe for most adults"]
            },
            {
                "name": "Magnesium Supplement",
                "generic": "Magnesium Glycinate",
                "dosage": "200-400mg daily",
                "usage": "Take with food, preferably in the evening",
                "side_effects": ["Loose stools at high doses"],
                "precautions": ["Check with doctor if you have kidney disease"]
            }
        ],
        "home_remedies": ["Deep breathing exercises", "Regular physical exercise", "Meditation and mindfulness", "Limit caffeine intake"],
        "when_to_see_doctor": "Anxiety is a medical condition. Please consult a mental health professional for proper evaluation and treatment"
    }
}

# Symptom keyword mapping for fuzzy matching
SYMPTOM_KEYWORDS = {
    "headache": ["headache", "head pain", "head ache", "migraine", "head hurts", "head pounding"],
    "fever": ["fever", "temperature", "hot", "chills", "feverish", "high temperature"],
    "cold": ["cold", "runny nose", "sneezing", "nasal congestion", "stuffy nose", "blocked nose"],
    "cough": ["cough", "coughing", "dry cough", "wet cough", "persistent cough"],
    "stomach pain": ["stomach pain", "stomach ache", "abdominal pain", "belly pain", "cramps", "indigestion", "bloating", "gas", "acidity", "heartburn"],
    "sore throat": ["sore throat", "throat pain", "throat hurts", "difficulty swallowing", "scratchy throat"],
    "allergy": ["allergy", "allergic", "itchy eyes", "sneezing", "hives", "allergic reaction", "hay fever"],
    "body pain": ["body pain", "muscle pain", "back pain", "joint pain", "body ache", "muscle ache", "sore muscles"],
    "diarrhea": ["diarrhea", "loose motions", "loose stool", "watery stool", "upset stomach", "food poisoning"],
    "skin rash": ["skin rash", "rash", "itching", "itchy skin", "skin irritation", "red skin", "bumps on skin"],
    "insomnia": ["insomnia", "can't sleep", "cannot sleep", "sleepless", "trouble sleeping", "sleep problem"],
    "anxiety": ["anxiety", "anxious", "nervous", "panic", "stressed", "worry", "worried", "restless"]
}


# Order intent keywords
ORDER_KEYWORDS = ["order", "buy", "purchase", "i want", "i need", "get me", "can i get", "i'd like", "give me", "need to order", "want to buy"]

# Greetings and casual conversation patterns
GREETING_KEYWORDS = ["hello", "hi", "hey", "good morning", "good afternoon", "good evening", "howdy", "hola", "sup", "what's up", "greetings"]
THANK_KEYWORDS = ["thank", "thanks", "thx", "appreciate", "helpful", "great help"]
BYE_KEYWORDS = ["bye", "goodbye", "see you", "take care", "later", "goodnight"]
HELP_KEYWORDS = ["help", "what can you do", "how does this work", "what do you do", "how to use"]
FEELING_KEYWORDS = ["not feeling well", "feel sick", "feeling bad", "unwell", "not well", "feel terrible", "feeling awful", "feel awful"]

# Empathetic intro messages based on symptom count
EMPATHY_SINGLE = [
    "I'm sorry to hear you're not feeling well. 💙 Let me help you out!",
    "Oh no, that doesn't sound fun! Let me see what I can suggest. 🤗",
    "I hear you! Let's figure this out together. 💪",
    "I understand that must be uncomfortable. Here's what I found for you:",
]

EMPATHY_MULTIPLE = [
    "I'm sorry you're dealing with multiple symptoms. 💙 Let me give you a thorough breakdown!",
    "That sounds like a rough time! Let me check everything for you. 🤗",
    "I can see you've got a few things going on. Don't worry — let's tackle them one by one! 💪",
]

import random


class MedicalAIAgent:
    """
    Friendly, rule-based Medical AI Agent that analyzes symptoms
    and provides OTC medicine suggestions with empathy and safety disclaimers.
    """

    DISCLAIMER = (
        "Gentle reminder: This is AI-generated guidance based on common symptoms. "
        "It's NOT a medical diagnosis. Please always consult a qualified healthcare "
        "professional before taking any medication. Your health matters to us! 💙"
    )

    def __init__(self):
        self.database = MEDICAL_DATABASE
        self.keywords = SYMPTOM_KEYWORDS

    def _check_order_intent(self, user_input_lower):
        """Detect if user wants to order a medicine and find a match."""
        import re

        has_order_intent = False
        for kw in ORDER_KEYWORDS:
            if kw in user_input_lower:
                has_order_intent = True
                break

        if not has_order_intent:
            return None

        # Extract quantity from user input (e.g. "6 paracetamol", "order 10 omeprazole")
        quantity = 1
        qty_patterns = [
            r'(\d+)\s+(?:tablets?|pills?|units?|boxes?|packs?|capsules?|bottles?)',
            r'(?:order|buy|get|need|want)\s+(\d+)',
            r'(\d+)\s+\w',  # generic: any number followed by a word
        ]
        for pattern in qty_patterns:
            match = re.search(pattern, user_input_lower)
            if match:
                parsed_qty = int(match.group(1))
                if 1 <= parsed_qty <= 999:
                    quantity = parsed_qty
                    break

        # Import here to avoid circular imports at module level
        from models import Medicine

        # Try to find the medicine name in the user input
        all_medicines = Medicine.query.all()
        best_match = None
        best_match_len = 0

        for med in all_medicines:
            med_name_lower = med.name.lower()
            # Check if any significant part of the medicine name is in the user input
            # Try full name first, then first word (brand name)
            if med_name_lower in user_input_lower:
                if len(med_name_lower) > best_match_len:
                    best_match = med
                    best_match_len = len(med_name_lower)
            else:
                # Try matching the first significant word (at least 4 chars)
                words = med_name_lower.split()
                for word in words:
                    clean_word = word.strip('®™().,')
                    if len(clean_word) >= 4 and clean_word in user_input_lower:
                        if len(clean_word) > best_match_len:
                            best_match = med
                            best_match_len = len(clean_word)

        if best_match:
            total_price = best_match.price * quantity
            return {
                "success": True,
                "is_order": True,
                "medicine": best_match.to_dict(),
                "quantity": quantity,
                "requires_prescription": best_match.requires_prescription,
                "message": (
                    f"I found **{best_match.name}** in our pharmacy! 💊\n\n"
                    f"💰 Price: ₹{best_match.price:.2f} each\n"
                    f"🔢 Quantity: **{quantity}**\n"
                    f"💵 Total: **₹{total_price:.2f}**\n"
                    f"📦 In Stock: {best_match.stock} units\n"
                    f"{'⚠️ **Prescription Required**' if best_match.requires_prescription else '✅ No prescription needed'}"
                ),
                "disclaimer": self.DISCLAIMER
            }
        else:
            return {
                "success": False,
                "is_order": True,
                "message": (
                    "I'd love to help you order medicine! 🛒\n\n"
                    "However, I couldn't identify the exact medicine you want. "
                    "Could you please try again with the medicine name? For example:\n\n"
                    "• \"I want to order 5 Paracetamol\"\n"
                    "• \"Buy 2 NORSAN Omega-3 Total\"\n"
                    "• \"I need 3 Omeprazole\"\n\n"
                    "You can also browse our full catalog in the **Medicine Shop**! 🏪"
                ),
                "disclaimer": self.DISCLAIMER
            }

    def _check_casual_chat(self, user_input_lower):
        """Handle greetings, thanks, and general conversation."""
        # Greetings
        for kw in GREETING_KEYWORDS:
            if kw in user_input_lower:
                user = "there"
                return {
                    "success": False,
                    "is_chat": True,
                    "message": (
                        f"Hey {user}! 👋😊 I'm your friendly MedAdvisor assistant!\n\n"
                        "I'm here to help you understand your symptoms and suggest "
                        "safe over-the-counter remedies.\n\n"
                        "Just tell me how you're feeling, for example:\n"
                        "• \"I have a headache and feel tired\"\n"
                        "• \"My throat is sore and I'm coughing\"\n"
                        "• \"I've got a stomach ache after eating\"\n\n"
                        "I'm all ears! What's been bothering you? 💙"
                    ),
                    "disclaimer": self.DISCLAIMER
                }

        # Thanks
        for kw in THANK_KEYWORDS:
            if kw in user_input_lower:
                return {
                    "success": False,
                    "is_chat": True,
                    "message": (
                        "You're very welcome! 😊💙 I'm glad I could help!\n\n"
                        "Remember to take care of yourself and don't hesitate to "
                        "reach out if you need anything else.\n\n"
                        "If your symptoms persist or get worse, please do visit a doctor. "
                        "Wishing you a speedy recovery! 🌟"
                    ),
                    "disclaimer": self.DISCLAIMER
                }

        # Goodbye
        for kw in BYE_KEYWORDS:
            if kw in user_input_lower:
                return {
                    "success": False,
                    "is_chat": True,
                    "message": (
                        "Take care of yourself! 👋💙\n\n"
                        "Remember: rest well, stay hydrated, and don't skip meals. "
                        "I'm always here whenever you need me!\n\n"
                        "Wishing you good health! 🌈✨"
                    ),
                    "disclaimer": self.DISCLAIMER
                }

        # Help
        for kw in HELP_KEYWORDS:
            if kw in user_input_lower:
                supported = ', '.join([s.title() for s in self.database.keys()])
                return {
                    "success": False,
                    "is_chat": True,
                    "message": (
                        "Great question! Here's how I can help you: 🤗\n\n"
                        "1️⃣ **Tell me your symptoms** — just describe how you feel in plain words\n"
                        "2️⃣ **I'll analyze them** — and suggest possible conditions\n"
                        "3️⃣ **Get medicine suggestions** — with dosage, side effects & precautions\n"
                        "4️⃣ **Home remedies** — natural ways to feel better\n"
                        "5️⃣ **When to see a doctor** — I'll tell you when it's important\n\n"
                        f"I can help with: {supported}\n\n"
                        "Just type how you're feeling and I'll do my best! 💪"
                    ),
                    "disclaimer": self.DISCLAIMER
                }

        # Vague feeling unwell
        for kw in FEELING_KEYWORDS:
            if kw in user_input_lower:
                return {
                    "success": False,
                    "is_chat": True,
                    "message": (
                        "I'm sorry to hear you're not feeling well! 😟💙\n\n"
                        "To help you better, could you describe your specific symptoms? "
                        "For example:\n\n"
                        "• Do you have a **headache**, **fever**, or **body aches**?\n"
                        "• Any **cough**, **sore throat**, or **runny nose**?\n"
                        "• Experiencing **stomach pain**, **nausea**, or **diarrhea**?\n"
                        "• Any **skin rash**, **itching**, or **allergies**?\n"
                        "• Having trouble **sleeping** or feeling **anxious**?\n\n"
                        "The more you tell me, the better I can help! 🤗"
                    ),
                    "disclaimer": self.DISCLAIMER
                }

        return None

    def analyze_symptoms(self, user_input):
        """Analyze user input and return medical suggestions with a friendly tone."""
        user_input_lower = user_input.lower().strip()

        if not user_input_lower:
            return {
                "success": False,
                "message": "Hey there! 👋 Just type in how you're feeling and I'll do my best to help!",
                "disclaimer": self.DISCLAIMER
            }

        # Check for order intent first
        order_response = self._check_order_intent(user_input_lower)
        if order_response:
            return order_response

        # Check for casual conversation first
        chat_response = self._check_casual_chat(user_input_lower)
        if chat_response:
            return chat_response

        # Find matching symptoms
        matched_symptoms = []
        for symptom, keywords in self.keywords.items():
            for keyword in keywords:
                if keyword in user_input_lower:
                    if symptom not in matched_symptoms:
                        matched_symptoms.append(symptom)
                    break

        if not matched_symptoms:
            return {
                "success": False,
                "message": (
                    "Hmm, I wasn't quite able to pinpoint specific symptoms from what you said. 🤔\n\n"
                    "No worries though! Could you try describing it a bit differently? "
                    "Here are some examples:\n\n"
                    "• \"I have a headache and fever\"\n"
                    "• \"My stomach hurts and I feel bloated\"\n"
                    "• \"I have a cough and sore throat\"\n"
                    "• \"I can't sleep at night\"\n"
                    "• \"I have a skin rash with itching\"\n\n"
                    "If your symptoms feel serious or unusual, please visit a doctor right away. "
                    "Your safety always comes first! 💙"
                ),
                "disclaimer": self.DISCLAIMER
            }

        # Pick a friendly intro
        if len(matched_symptoms) > 1:
            empathy_msg = random.choice(EMPATHY_MULTIPLE)
        else:
            empathy_msg = random.choice(EMPATHY_SINGLE)

        # Build response
        results = []
        all_medicines_suggested = []

        for symptom in matched_symptoms:
            data = self.database.get(symptom, {})
            if data:
                result = {
                    "symptom": symptom.title(),
                    "possible_conditions": data.get("conditions", []),
                    "medicines": data.get("medicines", []),
                    "home_remedies": data.get("home_remedies", []),
                    "when_to_see_doctor": data.get("when_to_see_doctor", "")
                }
                results.append(result)
                all_medicines_suggested.extend(data.get("medicines", []))

        return {
            "success": True,
            "empathy_message": empathy_msg,
            "symptoms_detected": [s.title() for s in matched_symptoms],
            "results": results,
            "total_medicines_suggested": len(all_medicines_suggested),
            "disclaimer": self.DISCLAIMER
        }

    def get_supported_symptoms(self):
        """Return list of symptoms the agent can analyze."""
        return list(self.database.keys())


# Singleton instance
medical_agent = MedicalAIAgent()
