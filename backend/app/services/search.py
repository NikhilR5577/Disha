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
    "lena", "leni", "dena", "deni", "do", "lo"
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
        
    query_tokens = set(cleaned_words)
    
    # 2. Number-first check for Ward — but SKIP if the user said a specialty ward name
    #    like "maternity ward", "delivery ward", "picu ward", "anc ward"
    specialty_ward_words = {"maternity", "delivery", "picu", "anc", "labour", "labor", "dialysis",
                            "sncu", "nrc", "pediatric", "neonatal", "newborn"}
    has_specialty = bool(query_tokens.intersection(specialty_ward_words))
    
    ward_numbers = {
        "1": "Ward No. 1 - Male Medical Ward", "ek": "Ward No. 1 - Male Medical Ward", "first": "Ward No. 1 - Male Medical Ward",
        "2": "Ward No. 2 - Male Surgical & Trauma Ward", "do": "Ward No. 2 - Male Surgical & Trauma Ward", "second": "Ward No. 2 - Male Surgical & Trauma Ward",
        "3": "Ward No. 3 - General Male Ward", "teen": "Ward No. 3 - General Male Ward", "third": "Ward No. 3 - General Male Ward",
        "4": "Ward No. 4 - Male Surgery Ward", "char": "Ward No. 4 - Male Surgery Ward", "fourth": "Ward No. 4 - Male Surgery Ward",
        "5": "Ward No. 5 - Female Surgery Ward", "panch": "Ward No. 5 - Female Surgery Ward", "fifth": "Ward No. 5 - Female Surgery Ward",
        "6": "Ward No. 6 - Female Medical Ward", "che": "Ward No. 6 - Female Medical Ward", "chah": "Ward No. 6 - Female Medical Ward", "sixth": "Ward No. 6 - Female Medical Ward"
    }
    
    has_ward_token = any(w in query_tokens for w in ["ward", "word"])
    
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
        
        # Also add bonus for query words that match the room's actual name
        # (but don't double-count words already matched by keywords)
        extra_name_matches = query_tokens.intersection(name_words) - node_meta["keywords"]
        overlap += len(extra_name_matches)
        
        # Hard check for "room" vs "panjian/slip" for X-ray/Sonography disambiguation
        # If they are tied but one has a specific disambiguation word, bump its score.
        if "panjian" in query_tokens or "parchi" in query_tokens or "slip" in query_tokens or "registration" in query_tokens:
            if "registration" in node_meta["keywords"] or "panjian" in node_meta["keywords"]:
                overlap += 2
        
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
