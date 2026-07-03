import os
import sqlite3
import argparse
from pathlib import Path
from elsawin_discord_formatter import xml_to_discord_md

DB_PATH = r"C:\Users\iboer\gemma_agent\elsawin\elsawin_index.db"
XML_DIR = r"C:\Users\iboer\gemma_agent\elsawin\extracted_xmls"

class ElsaWinSearcher:
    def __init__(self, db_path=DB_PATH):
        self.db_path = db_path
        if not os.path.exists(self.db_path):
            raise FileNotFoundError(f"Datenbank nicht gefunden: {self.db_path}. Bitte zuerst elsawin_indexer.py ausführen.")
            
    def search(self, marke=None, modell=None, baugrup=None, titel=None, limit=5):
        """Sucht in der Index-Datenbank nach passenden Reparaturdokumenten."""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        query = "SELECT id, xml_filename, marke, modell, obergrup, baugrup, titel, filepath FROM documents WHERE 1=1"
        params = []
        
        if marke:
            query += " AND marke LIKE ?"
            params.append(f"%{marke}%")
        if modell:
            query += " AND modell LIKE ?"
            params.append(f"%{modell}%")
        if baugrup:
            query += " AND baugrup LIKE ?"
            params.append(f"%{baugrup}%")
        if titel:
            query += " AND titel LIKE ?"
            params.append(f"%{titel}%")
            
        query += " LIMIT ?"
        params.append(limit)
        
        cursor.execute(query, params)
        results = cursor.fetchall()
        conn.close()
        
        # Umwandeln in Dictionary
        columns = ['id', 'xml_filename', 'marke', 'modell', 'obergrup', 'baugrup', 'titel', 'filepath']
        return [dict(zip(columns, row)) for row in results]

    def read_document(self, filepath):
        """Liest den rohen XML-Inhalt eines Dokuments."""
        try:
            with open(filepath, 'r', encoding='utf-8') as f:
                return f.read()
        except UnicodeDecodeError:
            with open(filepath, 'r', encoding='iso-8859-1') as f:
                return f.read()
        except FileNotFoundError:
            return f"Fehler: Datei nicht gefunden: {filepath}"

def main():
    parser = argparse.ArgumentParser(description="Durchsucht den lokalen ElsaWin-Index nach Reparaturanleitungen.")
    parser.add_argument("--marke", help="Fahrzeugmarke (z.B. VW)")
    parser.add_argument("--modell", help="Fahrzeugmodell (z.B. Golf Plus)")
    parser.add_argument("--baugrup", help="Baugruppe (z.B. Fahrwerk)")
    parser.add_argument("--titel", help="Teil des Titels der Anleitung")
    parser.add_argument("--limit", type=int, default=5, help="Maximale Anzahl der Ergebnisse")
    parser.add_argument("--read", type=int, help="ID des Dokuments, das gelesen werden soll")
    parser.add_argument("--discord", action="store_true", help="Formatiert die Ausgabe als Discord-Markdown")
    
    args = parser.parse_args()
    searcher = ElsaWinSearcher()
    
    if args.read:
        # Lese spezifisches Dokument basierend auf ID
        conn = sqlite3.connect(DB_PATH)
        cursor = conn.cursor()
        cursor.execute("SELECT filepath, titel FROM documents WHERE id = ?", (args.read,))
        result = cursor.fetchone()
        conn.close()
        
        if result:
            filepath, titel = result
            content = searcher.read_document(filepath)
            
            if args.discord:
                print(f"**=== {titel} ===**\n")
                print(xml_to_discord_md(content))
            else:
                print(f"=== {titel} ===\n")
                print(content)
        else:
            print(f"Dokument mit ID {args.read} nicht gefunden.")
    else:
        # Suche durchführen
        if not any([args.marke, args.modell, args.baugrup, args.titel]):
            print("Bitte mindestens einen Suchparameter angeben (--marke, --modell, --baugrup, --titel)")
            return
            
        print("Suche läuft...\n")
        results = searcher.search(args.marke, args.modell, args.baugrup, args.titel, args.limit)
        
        if not results:
            print("Keine Ergebnisse gefunden.")
            return
            
        print(f"{len(results)} Ergebnis(se) gefunden:\n")
        for res in results:
            print(f"ID:       {res['id']}")
            print(f"Marke:    {res['marke']}")
            print(f"Modell:   {res['modell']}")
            print(f"Baugrup:  {res['baugrup']}")
            print(f"Titel:    {res['titel']}")
            print(f"Dateipfad:{res['filepath']}")
            print("-" * 50)
        
        print("\nUm ein Dokument zu lesen, führe aus:")
        print(f"python elsawin_search.py --read <ID>")

if __name__ == "__main__":
    main()
