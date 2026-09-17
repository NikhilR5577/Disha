import re
import csv
import os
from typing import Optional, List, Dict, Any
from app.models.graph import Node
from app.services.graph_service import get_graph_from_db

CSV_PATH = os.path.join(os.path.dirname(__file__), '..', '..', 'data', 'rooms_data.csv')

# Carrier words to strip out
BUNDELI_CARRIER_WORDS = [
    "kya", "kaay", "ka", "ki", "ke", "kahan", "kaan", "kiten", "yahan", "iten",
    "vahan", "uten", "kaise", "kaiso", "hum", "main", "apun",
    "tum", "tumao", "yeh", "jo", "voh", "vo", "je",
    "jaana", "jaabo", "aana", "aabo", "batao", "mataav",
    "hai", "hain", "mujhe", "me", "mein", "ko", "le", "chalo",
    "take", "to", "where", "is", "tell", "go", "want",
    "kaha", "kahaa", "jaha", "jana", "bata", "bataiye",
    "kidhar", "dikha", "dikhao", "chahiye", "chahte",
    "milega", "mil", "wala", "wali", "vale",
    "karna", "karana", "karwana", "karni", "karwani", "karo",
    "lena", "leni", "dena", "deni", "do", "lo",
    "lagi", "laga", "lagti", "lagte", "raha", "rahi", "rahe",
    "pada", "padi", "pade", "hota", "hoti", "hote",
    "dikhaye", "bataye", "le_jao", "pahunchao"
]

def load_csv_metadata() -> Dict[str, Dict[str, Any]]:
    meta = {}
    with open(CSV_PATH, 'r', encoding='utf-8-sig') as f:
        reader = csv.DictReader(f)
        for row in reader:
            eng_name = str(row.get('English Name', '')).strip()
            keywords = str(row.get('Keywords (order-independent)', '')).lower()
            if keywords == 'nan' or not keywords: keywords = ''
            
            disambig = str(row.get('Disambiguation Group', ''))
            if disambig == 'nan' or not disambig: disambig = ''
            
            meta[eng_name] = {
                "keywords": set(keywords.split()),
                "disambiguation_group": disambig
            }
    return meta

# Global cache for metadata
_metadata_cache = None

def get_metadata():
    global _metadata_cache
    if _metadata_cache is None:
        _metadata_cache = load_csv_metadata()
    return _metadata_cache

def search_destination(query: str, db) -> Optional[Node]:
    """
    NLP fuzzy search for destination based on Bundeli/Hindi voice queries.
    """
    graph = get_graph_from_db(db)
    meta = get_metadata()
    
    # 1. Clean query
    query = query.lower()
    
    # Simple regex to strip carrier words
    words = query.split()
    cleaned_words = [w for w in words if w not in BUNDELI_CARRIER_WORDS]
    
    if not cleaned_words:
        cleaned_words = words # Fallback if everything was stripped
    
    # Normalize common multi-word terms that voice splits apart
    # "x ray" -> "xray", "x-ray" -> "xray", "e c g" -> "ecg", "o p d" -> "opd"
    cleaned_text = " ".join(cleaned_words)
    cleaned_text = re.sub(r'\bx[\s\-]?ray\b', 'xray', cleaned_text)
    cleaned_text = re.sub(r'\be[\s\-]?c[\s\-]?g\b', 'ecg', cleaned_text)
    cleaned_text = re.sub(r'\bo[\s\-]?p[\s\-]?d\b', 'opd', cleaned_text)
    cleaned_text = re.sub(r'\bi[\s\-]?c[\s\-]?u\b', 'icu', cleaned_text)
    cleaned_text = re.sub(r'\bn[\s\-]?c[\s\-]?d\b', 'ncd', cleaned_text)
    cleaned_text = re.sub(r'\bc[\s\-]?t\b', 'ct', cleaned_text)
    cleaned_text = re.sub(r'\be[\s\-]?n[\s\-]?t\b', 'ent', cleaned_text)
    cleaned_text = re.sub(r'\ba[\s\-]?n[\s\-]?c\b', 'anc', cleaned_text)
    cleaned_text = re.sub(r'\bs[\s\-]?t[\s\-]?i\b', 'sti', cleaned_text)
    cleaned_text = re.sub(r'\br[\s\-]?t[\s\-]?i\b', 'rti', cleaned_text)
    cleaned_text = re.sub(r'\bs[\s\-]?n[\s\-]?c[\s\-]?u\b', 'sncu', cleaned_text)
    cleaned_text = re.sub(r'\bp[\s\-]?i[\s\-]?c[\s\-]?u\b', 'picu', cleaned_text)
    cleaned_text = re.sub(r'\bn[\s\-]?r[\s\-]?c\b', 'nrc', cleaned_text)
    cleaned_words = cleaned_text.split()
    
    # Hindi-to-Latin synonym expansion for Devanagari voice transcripts
    # When hi-IN SpeechRecognition sends Devanagari, we inject the Latin keyword equivalents
    # so the keyword scorer can match them against rooms_data.csv keywords.
    # Format: Devanagari word -> Latin keyword(s) to inject (space-separated for multi-inject)
    HINDI_SYNONYMS = {
        # ===== WARD TYPES =====
        "वार्ड": "ward", "वर्ड": "ward",
        "मैटरनिटी": "maternity", "मेटर्निटी": "maternity", "प्रसूति": "maternity",
        "एएनसी": "anc", "ए.एन.सी.": "anc",
        "डिलीवरी": "delivery",
        "लेबर": "labour", "लेबोर": "labour", "प्रसव": "labour delivery",
        "डायलिसिस": "dialysis",
        "पीआईसीयू": "picu", "पी.आई.सी.यू.": "picu",
        "एसएनसीयू": "sncu", "नवजात": "newborn sncu",
        "एनआरसी": "nrc", "कुपोषण": "malnutrition nrc", "पोषण": "nutrition nrc",
        "बाल": "pediatric", "बच्चों": "pediatric", "बच्चे": "pediatric", "बच्चा": "pediatric",
        "जच्चा": "maternity delivery",
        
        # ===== DEPARTMENTS & CLINICS =====
        "आईसीयू": "icu", "आई.सी.यू.": "icu", "गहन": "icu intensive",
        "ओपीडी": "opd", "ओ.पी.डी.": "opd",
        "ईसीजी": "ecg", "ई.सी.जी.": "ecg",
        "सीटी": "ct", "स्कैन": "scan ct",
        "ईएनटी": "ent", "ई.एन.टी.": "ent",
        "एक्सरे": "xray", "एक्स-रे": "xray", "एक्स": "xray",
        "एसटीआई": "sti", "आरटीआई": "rti", "गुप्त": "sti rti",
        "एनसीडी": "ncd",
        "डीईआईसी": "deic",
        "आरएमओ": "rmo",
        "सीएमओ": "cmo civil surgeon",
        
        # ===== COMMON NEEDS (intent-based) =====
        # Washroom
        "शौचालय": "shauchalay toilet washroom", "सौचालय": "shauchalay toilet washroom",
        "टॉयलेट": "toilet washroom", "बाथरूम": "bathroom washroom",
        "संडास": "sandas washroom", "पेशाब": "peshab washroom",
        "लैट्रिन": "latrine washroom",
        
        # Food / Kitchen
        "भूख": "bhook kitchen", "खाना": "khana kitchen", "भोजन": "bhojan kitchen",
        "नाश्ता": "nashta kitchen", "किचन": "kitchen", "रसोई": "kitchen",
        "कैंटीन": "canteen kitchen", "चाय": "chai kitchen", "पानी": "pani kitchen",
        
        # Pharmacy / Medicine
        "फार्मेसी": "pharmacy", "दवाई": "dabai pharmacy", "दवा": "dabai pharmacy",
        "दवाखाना": "pharmacy dispensary", "औषधालय": "pharmacy", "मेडिकल": "medical",
        "केमिस्ट": "chemist pharmacy",
        
        # Emergency
        "इमरजेंसी": "emergency", "आपातकाल": "emergency", "आपातकालीन": "emergency",
        "कैजुअल्टी": "casualty emergency", "हादसा": "casualty accident",
        "दुर्घटना": "casualty accident",
        
        # Reception / Help
        "रिसेप्शन": "reception", "पूछताछ": "reception inquiry help",
        "हेल्प": "help desk", "सहायता": "help desk",
        "पर्ची": "reception registration slip", "काउंटर": "counter registration",
        "रजिस्ट्रेशन": "registration",
        
        # Vaccination
        "टीकाकरण": "vaccination teeka", "टीका": "vaccination teeka",
        "इंजेक्शन": "injection vaccination",
        
        # ===== BODY PARTS & SYMPTOMS → DEPARTMENT MAPPING =====
        "हड्डी": "haddi ortho orthopedic bone", "ऑर्थो": "ortho orthopedic",
        "टूट": "fracture ortho", "फ्रैक्चर": "fracture ortho",
        "प्लास्टर": "plaster cast",
        
        "दांत": "dental dentist tooth", "डेंटल": "dental",
        "दंत": "dental",
        
        "नाक": "nose ent", "कान": "ear ent", "गला": "throat ent",
        
        "दिल": "heart ecg", "छाती": "chest ecg heart",
        "सांस": "breathing emergency",
        
        "आंख": "eye opd", "आँख": "eye opd",
        
        "पेट": "stomach emergency medicine", "दर्द": "pain emergency",
        "बुखार": "fever medicine opd", "ज्वर": "fever medicine",
        "सिर": "head medicine", "सिरदर्द": "headache medicine",
        "उल्टी": "vomiting emergency", "दस्त": "diarrhea emergency",
        "खांसी": "cough medicine", "जुकाम": "cold medicine",
        
        "कुत्ता": "kutta dog rabies", "कुत्ते": "kutta dog rabies",
        "काटा": "bite rabies", "काटने": "bite rabies",
        "रेबीज": "rabies",
        
        "शुगर": "sugar diabetes ncd", "मधुमेह": "diabetes ncd madhumeh",
        "बीपी": "bp blood pressure ncd", "ब्लडप्रेशर": "blood pressure ncd",
        
        "गुर्दा": "kidney dialysis", "गुर्दे": "kidney dialysis", "किडनी": "kidney dialysis",
        
        "पागल": "pagal psychiatry mental", "दिमाग": "dimag psychiatry mental",
        "मानसिक": "mental psychiatry", "मनोरोग": "psychiatry",
        
        # ===== SURGERY & OT =====
        "सर्जरी": "surgery surgical", "सर्जिकल": "surgical surgery",
        "ऑपरेशन": "operation surgery ot", "ओटी": "ot operation theatre",
        
        # ===== DIAGNOSTICS =====
        "पैथोलॉजी": "pathology lab", "जांच": "jaanch test pathology",
        "टेस्ट": "test pathology lab", "लैब": "lab pathology",
        "सोनोग्राफी": "sonography ultrasound", "अल्ट्रासाउंड": "ultrasound sonography",
        "प्रेगनेंसी": "pregnancy pregnant sonography",
        
        # ===== BLOOD =====
        "ब्लड": "blood", "रक्त": "blood rakt", "खून": "khoon blood",
        "बैंक": "bank",
        
        # ===== STAFF =====
        "नर्स": "nurse nursing", "नर्सिंग": "nursing nurse",
        "डॉक्टर": "doctor", "सर्जन": "surgeon civil",
        "विशेषज्ञ": "specialist senior",
        
        # ===== GENDER =====
        "गर्भवती": "pregnant pregnancy garbhvati",
        "महिला": "female women ladies", "स्त्री": "female women gynae",
        "लेडी": "lady women gynae", "लेडीज": "ladies female women",
        "पुरुष": "male",
        
        # ===== GYNAE / OBS =====
        "स्त्री": "gynae obs female", "गायनी": "gynae obs",
        
        # ===== LOCATIONS =====
        "गेट": "gate entrance", "द्वार": "gate entrance", "प्रवेश": "entrance gate",
        "पार्क": "park garden", "बगीचा": "park garden",
        "सीढ़ी": "stairs staircase", "सीढ़ियाँ": "stairs staircase", "रैंप": "ramp",
        "बोर्ड": "board medical",
        "ऑफिस": "office", "कार्यालय": "office",
        "रिकॉर्ड": "record file", "फाइल": "file record",
        "फोकल": "focal point",
        "बैडमिंटन": "badminton sports", "खेल": "sports badminton",
        "वेटिंग": "waiting lobby", "प्रतीक्षा": "waiting lobby",
        "एम्बुलेंस": "ambulance",
        "उमंग": "umang kendre",
        "परिवार": "family welfare planning", "कल्याण": "welfare family",
        "नियोजन": "planning family",
        
        # ===== MISC =====
        "पट्टी": "dressing bandage", "ड्रेसिंग": "dressing bandage",
        "घाव": "wound dressing",
        "स्टोर": "store storage", "भंडार": "bhander store storage",
        "गोदाम": "store storage",
        "क्वालिटी": "quality qa", "गुणवत्ता": "quality qa",
        "सिविल": "civil surgeon cs",
    }
    
    # Expand: for each Hindi word in the query, inject its Latin equivalent(s)
    expanded_tokens = list(cleaned_words)
    for word in cleaned_words:
        if word in HINDI_SYNONYMS:
            # Support multi-inject: "शौचालय" -> "shauchalay toilet washroom"
            expanded_tokens.extend(HINDI_SYNONYMS[word].split())
    cleaned_words = expanded_tokens
        
    query_tokens = set(cleaned_words)
    
    # 2. Number-first check for Ward — but SKIP if the user said a specialty ward name
    #    like "maternity ward", "delivery ward", "picu ward", "anc ward"
    specialty_ward_words = {"maternity", "delivery", "picu", "anc", "labour", "labor", "dialysis",
                            "sncu", "nrc", "pediatric", "neonatal", "newborn",
                            # Devanagari equivalents
                            "मैटरनिटी", "प्रसूति", "एएनसी", "डिलीवरी", "लेबर", "प्रसव",
                            "डायलिसिस", "पीआईसीयू", "एसएनसीयू", "एनआरसी", "बाल", "नवजात", "जच्चा"}
    has_specialty = bool(query_tokens.intersection(specialty_ward_words))
    
    ward_numbers = {
        "1": "Ward No. 1 - Male Medical Ward", "ek": "Ward No. 1 - Male Medical Ward", "एक": "Ward No. 1 - Male Medical Ward", "पहला": "Ward No. 1 - Male Medical Ward", "first": "Ward No. 1 - Male Medical Ward",
        "2": "Ward No. 2 - Male Surgical & Trauma Ward", "do": "Ward No. 2 - Male Surgical & Trauma Ward", "दो": "Ward No. 2 - Male Surgical & Trauma Ward", "दूसरा": "Ward No. 2 - Male Surgical & Trauma Ward", "second": "Ward No. 2 - Male Surgical & Trauma Ward",
        "3": "Ward No. 3 - General Male Ward", "teen": "Ward No. 3 - General Male Ward", "तीन": "Ward No. 3 - General Male Ward", "तीसरा": "Ward No. 3 - General Male Ward", "third": "Ward No. 3 - General Male Ward",
        "4": "Ward No. 4 - Male Surgery Ward", "char": "Ward No. 4 - Male Surgery Ward", "चार": "Ward No. 4 - Male Surgery Ward", "चौथा": "Ward No. 4 - Male Surgery Ward", "fourth": "Ward No. 4 - Male Surgery Ward",
        "5": "Ward No. 5 - Female Surgery Ward", "panch": "Ward No. 5 - Female Surgery Ward", "पांच": "Ward No. 5 - Female Surgery Ward", "पांचवां": "Ward No. 5 - Female Surgery Ward", "fifth": "Ward No. 5 - Female Surgery Ward",
        "6": "Ward No. 6 - Female Medical Ward", "che": "Ward No. 6 - Female Medical Ward", "chah": "Ward No. 6 - Female Medical Ward", "छह": "Ward No. 6 - Female Medical Ward", "छठा": "Ward No. 6 - Female Medical Ward", "sixth": "Ward No. 6 - Female Medical Ward"
    }
    
    has_ward_token = any(w in query_tokens for w in ["ward", "word", "वार्ड", "वर्ड", "नंबर"])
    
    if has_ward_token and not has_specialty:
        # Check if they specified a number
        for num, target_name in ward_numbers.items():
            if num in query_tokens:
                # Find the node
                for node in graph.nodes.values():
                    if node.name == target_name:
                        return node
                        
        # If they said just "ward" with no number, fall through to keyword scoring
        # (Don't default to any specific ward)
                
    # 3. Score overlapping keywords
    best_score = 0
    best_nodes = []
    
    for node in graph.nodes.values():
        if not node.is_room or not node.name:
            continue
            
        node_meta = meta.get(node.name)
        
        # Also check words from the node's actual English name
        name_words = set(node.name.lower().replace('(', '').replace(')', '').replace('-', ' ').replace('&', ' ').replace('/', ' ').split())
        name_overlap = len(query_tokens.intersection(name_words))
        
        if not node_meta:
            # Fallback: check exact name inclusion or word overlap
            if node.name.lower() in query:
                best_nodes = [node]
                best_score = 100
            elif name_overlap > best_score:
                best_score = name_overlap
                best_nodes = [node]
            elif name_overlap == best_score and name_overlap > 0:
                best_nodes.append(node)
            continue
            
        overlap = len(query_tokens.intersection(node_meta["keywords"]))
        
        # Specialty bonus: if they said a specialty ward, give a massive bonus
        # to the node that actually has that specialty word in its keywords.
        if has_specialty:
            query_specialties = query_tokens.intersection(specialty_ward_words)
            if node_meta["keywords"].intersection(query_specialties):
                overlap += 5
                
        # Also add bonus for query words that match the room's actual name
        # (but don't double-count words already matched by keywords)
        extra_name_matches = query_tokens.intersection(name_words) - node_meta["keywords"]
        overlap += len(extra_name_matches)
        
        # Exact name match bonus! If the full room name (lowercased) is in the query,
        # it's almost certainly what they want.
        node_name_lower = node.name.lower()
        if node_name_lower in query.lower() or node_name_lower.replace("ward no. ", "ward ") in query.lower():
            overlap += 10
            
        # Hard check for "room" vs "panjian/slip" for X-ray/Sonography disambiguation
        # If they are tied but one has a specific disambiguation word, bump its score.
        if "panjian" in query_tokens or "parchi" in query_tokens or "slip" in query_tokens or "registration" in query_tokens:
            if "registration" in node_meta["keywords"] or "panjian" in node_meta["keywords"]:
                overlap += 2
                
        # Disambiguation for Reception vs Help Desk
        if "reception" in query_tokens or "रिसेप्शन" in query_tokens or "पूछताछ" in query_tokens:
            if node.name == "Reception":
                overlap += 3
        
        if overlap > best_score:
            best_score = overlap
            best_nodes = [node]
        elif overlap == best_score and overlap > 0:
            best_nodes.append(node)
            
    # 4. Disambiguation
    if best_score > 0:
        if len(best_nodes) > 1:
            # Check for Main Entrance / Help Desk generic tiebreaker
            for n in best_nodes:
                if n.name == "Main Entrance" or n.name == "Help Desk":
                    return n
                    
            # Check for Room vs Panjian/Counter tiebreaker (e.g., X-Ray, Dental)
            # If they didn't explicitly say "panjian/slip", prefer the actual "Room" or "Department"
            registration_words = {"panjian", "parchi", "slip", "registration", "counter"}
            if not query_tokens.intersection(registration_words):
                for n in best_nodes:
                    name_lower = n.name.lower()
                    if "room" in name_lower or "department" in name_lower or "radiology" in name_lower:
                        return n
                        
            return best_nodes[0]
        
        return best_nodes[0]
        
    # 5. Last resort generic substring match
    for node in graph.nodes.values():
        if node.is_room and node.name and node.name.lower() in query:
            return node
            
    return None
