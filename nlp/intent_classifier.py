"""
QueryMind 2.0 – Intent Classification and Semantic Scope Engine
Distinguishes valid relational database queries from conversational greetings,
ambiguous utterances, and unauthorized data-modification operations.
"""

import re
from typing import Dict, Any, List, Optional

# Supported Classification Constants
DATABASE_QUERY = "DATABASE_QUERY"
AMBIGUOUS_QUERY = "AMBIGUOUS_QUERY"
OUT_OF_SCOPE = "OUT_OF_SCOPE"
UNSUPPORTED_OPERATION = "UNSUPPORTED_OPERATION"
EMPTY_INPUT = "EMPTY_INPUT"

DEFAULT_SUGGESTIONS = [
    "Show all students",
    "Find students with attendance below 75%",
    "Show average marks by subject",
    "List the top five students by marks",
    "Count students in each department"
]

AMBIGUOUS_SUGGESTIONS = [
    "Show all students",
    "Show average marks by subject",
    "Show students with attendance below 75%",
    "Show all subjects and their credits"
]

UNSUPPORTED_SUGGESTIONS = [
    "Show all students",
    "Find students with attendance below 75%",
    "Show average marks by subject"
]

# Conversational Greetings & Out-of-Scope Patterns
OUT_OF_SCOPE_PATTERNS = [
    r"^(hello|hi|hey|hiya|howdy|greetings|namaste|hola|bonjour)\b",
    r"^good\s+(morning|afternoon|evening|night|day)\b",
    r"\bhow\s+are\s+you\b",
    r"\bwhat\s+is\s+your\s+name\b",
    r"\bwho\s+are\s+you\b",
    r"\bwho\s+made\s+you\b",
    r"\btell\s+me\s+a\s+joke\b",
    r"\bwhat\s+can\s+you\s+do\b",
    r"\bweather\b",
    r"\bwhat\s+time\s+is\s+it\b",
    r"\bare\s+you\s+(an?\s+)?(ai|robot|human|bot)\b",
    r"\bhow('s|\s+is)\s+it\s+going\b",
    r"\bnice\s+to\s+meet\s+you\b",
    r"\bthank\s*(you|s)?\b",
    r"\bbye|goodbye|see\s+you\b",
    r"\bkaise\s+ho\b",
    r"\bkya\s+hal\s+hai\b",
    r"\bnaam\s+kya\s+hai\b",
]

# Destructive / Unsupported Operations (DDL / DML modifications)
UNSUPPORTED_OPERATION_PATTERNS = [
    r"\b(delete|remove|erase|wipe|destroy|hata\s+do)\b",
    r"\b(drop\s+table|drop\s+database|truncate)\b",
    r"\b(insert\s+into|add\s+new\s+student|create\s+new)\b",
    r"\b(update\s+marks|update\s+student|modify|change\s+marks)\b",
    r"\b(alter\s+table|grant\s+all|revoke)\b",
]

# Generic / Ambiguous Requests lacking specific entities
AMBIGUOUS_PATTERNS = [
    r"^(show|display|get|fetch|list|view|give\s+me)?\s*(me\s+)?(the\s+)?(data|records|information|database|table|details|everything|all)(\s+please)?$",
    r"^(find|search|lookup|look\s+up)\s*(records|data|info)?$",
    r"^(data\s+dikhao|records\s+dikhao|mujhe\s+data\s+chahiye|sabhi\s+records)$",
    r"^show\s+data$",
    r"^find\s+records$",
]

# Core Academic Entity Keywords
ACADEMIC_ENTITIES = {
    "student", "students", "pupil", "pupils",
    "mark", "marks", "score", "scores", "grade", "grades",
    "attendance", "attend", "present", "absent", "defaulter", "defaulters",
    "subject", "subjects", "course", "courses",
    "division", "divisions", "section", "sections", "department", "departments",
    "credit", "credits"
}

def classify_intent(question: str, known_tables: Optional[List[str]] = None, known_columns: Optional[List[str]] = None) -> Dict[str, Any]:
    """
    Classify the incoming utterance into one of the 5 canonical intent states:
    1. EMPTY_INPUT
    2. OUT_OF_SCOPE
    3. UNSUPPORTED_OPERATION
    4. AMBIGUOUS_QUERY
    5. DATABASE_QUERY
    """
    if not question or not question.strip():
        return {
            "classification": EMPTY_INPUT,
            "status": "empty",
            "intent": None,
            "sql": None,
            "message": "Please ask a question about the connected database.",
            "suggestions": DEFAULT_SUGGESTIONS
        }

    q = question.strip()
    q_lower = q.lower()
    clean_text = re.sub(r"[^a-zA-Z0-9\s]", " ", q_lower).strip()

    if not clean_text:
        return {
            "classification": EMPTY_INPUT,
            "status": "empty",
            "intent": None,
            "sql": None,
            "message": "Please ask a question about the connected database.",
            "suggestions": DEFAULT_SUGGESTIONS
        }

    # 1. Check for Unsupported DDL / DML operations
    for pattern in UNSUPPORTED_OPERATION_PATTERNS:
        if re.search(pattern, q_lower):
            return {
                "classification": UNSUPPORTED_OPERATION,
                "status": "unsupported",
                "intent": None,
                "sql": None,
                "message": "Data modification (DELETE, DROP, UPDATE, INSERT) is strictly prohibited. QueryMind operates exclusively as a read-only analytical query engine.",
                "suggestions": UNSUPPORTED_SUGGESTIONS
            }

    # 2. Check for Conversational / Out-of-Scope input
    for pattern in OUT_OF_SCOPE_PATTERNS:
        if re.search(pattern, q_lower):
            # Guard against edge-cases where question starts with greeting but contains actual DB query
            # e.g., "Hello, show all students"
            has_db_entity = any(e in q_lower.split() for e in ACADEMIC_ENTITIES)
            if not has_db_entity:
                return {
                    "classification": OUT_OF_SCOPE,
                    "status": "out_of_scope",
                    "intent": None,
                    "sql": None,
                    "message": "Please ask a question about the connected database.",
                    "suggestions": DEFAULT_SUGGESTIONS
                }

    # 3. Check for Ambiguous Queries lacking entity context
    for pattern in AMBIGUOUS_PATTERNS:
        if re.search(pattern, q_lower.strip()):
            return {
                "classification": AMBIGUOUS_QUERY,
                "status": "ambiguous",
                "intent": None,
                "sql": None,
                "message": "Your request is too ambiguous. Which table or entity would you like to query?",
                "suggestions": AMBIGUOUS_SUGGESTIONS
            }

    # 4. Check whether input refers to any known schema entities or active custom dataset
    entities_pool = set(ACADEMIC_ENTITIES)
    if known_tables:
        for t in known_tables:
            entities_pool.add(t.lower())
            entities_pool.update(t.lower().replace("_", " ").split())
    if known_columns:
        for c in known_columns:
            entities_pool.add(c.lower())
            entities_pool.update(c.lower().replace("_", " ").split())

    tokens = set(clean_text.split())
    has_recognized_entity = bool(tokens.intersection(entities_pool))

    # Also check multi-word matching (e.g. "linear algebra", "computer science")
    if not has_recognized_entity:
        for ent in entities_pool:
            if f" {ent} " in f" {clean_text} ":
                has_recognized_entity = True
                break

    if not has_recognized_entity:
        # If no recognized entity was found and no known pattern matches:
        return {
            "classification": OUT_OF_SCOPE,
            "status": "out_of_scope",
            "intent": None,
            "sql": None,
            "message": "Please ask a question about the connected database.",
            "suggestions": DEFAULT_SUGGESTIONS
        }

    # Input contains recognized database entities
    return {
        "classification": DATABASE_QUERY,
        "status": "valid",
        "intent": "database_retrieval",
        "sql": None,  # To be generated by schema-aware SQL generator
        "message": "Valid database intent recognized.",
        "suggestions": DEFAULT_SUGGESTIONS
    }
