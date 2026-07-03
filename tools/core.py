import os
import re

# Basis-Pfad des Projektverzeichnisses
PROJECT_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
AGENT_LOG_FILE = os.path.join(PROJECT_DIR, "agent_created_files.txt")

def is_safe_path(path: str) -> bool:
    """Überprüft, ob ein Pfad sicher ist.
    Erlaubt:
    - Alles unter C:\\Users\\iboer
    - Alle Pfade auf anderen Laufwerken (D:, E:, F:, etc.), solange sie nicht zu Systemordnern gehören.
    Nicht erlaubt:
    - Pfade auf C: außerhalb von C:\\Users\\iboer (wie C:\\Windows, C:\\)
    - Systemordner auf anderen Laufwerken (wie $RECYCLE.BIN, System Volume Information)
    """
    try:
        abs_path = os.path.abspath(path).lower()
        
        # 1. Alles unter C:\Users\iboer ist immer erlaubt
        if abs_path.startswith(r"c:\users\iboer"):
            return True
            
        # 2. Blockiere C: außerhalb von C:\Users\iboer
        if abs_path.startswith("c:"):
            return False
            
        # 3. Blockiere typische geschützte Systemordner auf allen Laufwerken
        forbidden_patterns = [
            r"\$recycle.bin",
            r"\system volume information",
            r"\recovery",
            r"\msocache",
            r"\windows",
            r"\program files",
            r"\program files (x86)",
            r"\programdata"
        ]
        for pattern in forbidden_patterns:
            if pattern in abs_path:
                return False
                
        # 4. Erlaube andere Laufwerke (D:, E:, etc.), sofern sie mit einem Laufwerksbuchstaben beginnen
        if re.match(r"^[a-b|d-z]:", abs_path):
            return True
            
        return False
    except Exception:
        return False

def is_protected_code_path(file_path: str) -> bool:
    """Überprüft, ob ein Pfad eine geschützte Python-Code-Datei des Bots im Projektverzeichnis darstellt."""
    try:
        abs_path = os.path.abspath(file_path).lower()
        project_dir_lower = PROJECT_DIR.lower()
        if abs_path.startswith(project_dir_lower) and abs_path.endswith(".py"):
            return True
    except Exception:
        pass
    return False

def log_created_file(path: str):
    """Protokolliert eine vom Agenten erstellte Datei."""
    try:
        abs_path = os.path.abspath(path)
        existing = []
        if os.path.exists(AGENT_LOG_FILE):
            with open(AGENT_LOG_FILE, "r", encoding="utf-8") as f:
                existing = [line.strip().lower() for line in f.readlines()]
        
        if abs_path.lower() not in existing:
            with open(AGENT_LOG_FILE, "a", encoding="utf-8") as f:
                f.write(abs_path + "\n")
    except Exception as e:
        print(f"Fehler beim Protokollieren der Datei: {e}")

def was_file_created_by_agent(path: str) -> bool:
    """Prüft, ob die Datei vom Agenten selbst erstellt wurde."""
    try:
        abs_path = os.path.abspath(path)
        if not os.path.exists(AGENT_LOG_FILE):
            return False
        with open(AGENT_LOG_FILE, "r", encoding="utf-8") as f:
            for line in f.readlines():
                if line.strip().lower() == abs_path.lower():
                    return True
    except Exception:
        pass
    return False
