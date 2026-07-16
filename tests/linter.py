# tests/test_non_hardcoded.py
import re
import pathlib
import sys

# Liste noire de codes NAF ou mots-clés interdits dans le code applicatif
BANNED_WORDS = [
    r"\b4520Z\b", r"\b4511Z\b", r"\b4531Z\b", r"\b4532Z\b",
    r"\bgaragiste\b", r"\bgarage\b", r"\bcarrosserie\b", r"\bconcessionnaire\b"
]

EXCLUDED_PATHS = [
    "sql/schema_init.sql",
    "tests/test_non_hardcoded.py",  # Ce fichier lui-même
    "scripts/provision_pilot.py",   # Le script de provisioning de test
    "docs/"                         # Documentation
]

def run_linter():
    print("[LINTER] Vérification de l'étanchéité des agents et du code applicatif...")
    violations = 0
    root = pathlib.Path(".")
    
    for file_path in root.glob("**/*.py"):
        # Ignorer les exclusions de chemin
        if any(excl in str(file_path) for excl in EXCLUDED_PATHS):
            continue
            
        with open(file_path, "r", encoding="utf-8") as f:
            content = f.read()
            
        for pattern in BANNED_WORDS:
            matches = re.findall(pattern, content, re.IGNORECASE)
            if matches:
                print(f"[VIOLATION] Valeur métier détectée en dur dans '{file_path}' : {matches}")
                violations += len(matches)
                
    if violations > 0:
        print(f"[FAILED] {violations} violation(s) détectée(s). Rappel : Les ICP sont des données, pas du code !")
        sys.exit(1)
    else:
        print("[PASSED] Aucune fuite de données métier trouvée dans le code applicatif.")
        sys.exit(0)

if __name__ == "__main__":
    run_non_hardcoded_linter()