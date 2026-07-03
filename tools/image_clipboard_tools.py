import os
import requests
from crewai.tools import BaseTool
from .core import is_safe_path

class DescribeImageTool(BaseTool):
    name: str = "Bild beschreiben"
    description: str = (
        "Analysiert und beschreibt eine lokale Bilddatei (z.B. PNG, JPEG, WEBP). "
        "Übergib den 'image_path' und optional einen 'prompt' (z.B. eine Frage zum Bild oder 'Beschreibe dieses Bild')."
    )

    def _run(self, image_path: str, prompt: str = "Beschreibe dieses Bild im Detail auf Deutsch.") -> str:
        if not is_safe_path(image_path):
            return f"Zugriff verweigert: Der Pfad '{image_path}' ist nicht erlaubt."
        
        try:
            if not os.path.exists(image_path):
                return f"Fehler: Die Datei '{image_path}' existiert nicht."
            
            import base64
            with open(image_path, "rb") as image_file:
                encoded_string = base64.b64encode(image_file.read()).decode('utf-8')
            
            payload = {
                "model": "gemma4:12b",
                "prompt": prompt,
                "images": [encoded_string],
                "stream": False
            }
            
            response = requests.post("http://localhost:11434/api/generate", json=payload, timeout=45)
            if response.status_code == 200:
                return response.json().get("response", "")
            else:
                return f"Fehler bei der Bildanalyse über Ollama: {response.text}"
        except Exception as e:
            return f"Fehler bei der Ausführung des Bildwerkzeugs: {str(e)}"

class ReadClipboardTool(BaseTool):
    name: str = "Zwischenablage lesen"
    description: str = "Liest den aktuellen Textinhalt aus der Windows-Zwischenablage (Clipboard) aus."

    def _run(self) -> str:
        try:
            import pyperclip
            text = pyperclip.paste()
            if not text: return "Die Zwischenablage ist leer oder enthält keinen Text."
            return f"Inhalt der Zwischenablage:\n\n{text}"
        except Exception as e:
            return f"Fehler beim Lesen der Zwischenablage: {str(e)}"

class WriteClipboardTool(BaseTool):
    name: str = "Zwischenablage schreiben"
    description: str = "Schreibt einen angegebenen Text direkt in die Windows-Zwischenablage (Clipboard)."

    def _run(self, text: str) -> str:
        try:
            import pyperclip
            pyperclip.copy(text)
            return "Erfolgreich: Der Text wurde in die Zwischenablage kopiert."
        except Exception as e:
            return f"Fehler beim Schreiben in die Zwischenablage: {str(e)}"
