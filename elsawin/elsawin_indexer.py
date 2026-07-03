import os
import subprocess
import shutil
import glob
import re
import sqlite3
import time
from xml.etree import ElementTree

# Konfiguration
SOURCE_DIR = r"C:\Users\iboer\gemma_agent\elsawin\balls"
OUTPUT_DIR = r"C:\Users\iboer\gemma_agent\elsawin\extracted_xmls"
TEMP_DIR = r"C:\Users\iboer\gemma_agent\elsawin\temp_index_extract"
SEVENZIP_PATH = r"C:\Program Files\7-Zip\7z.exe"
DB_PATH = r"C:\Users\iboer\gemma_agent\elsawin\elsawin_index.db"

def init_db():
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS documents (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            archive_name TEXT,
            xml_filename TEXT,
            filepath TEXT,
            marke TEXT,
            modell TEXT,
            obergrup TEXT,
            baugrup TEXT,
            titel TEXT
        )
    ''')
    # Erstelle Indizes für schnellere Suchanfragen
    cursor.execute('CREATE INDEX IF NOT EXISTS idx_marke ON documents (marke)')
    cursor.execute('CREATE INDEX IF NOT EXISTS idx_modell ON documents (modell)')
    cursor.execute('CREATE INDEX IF NOT EXISTS idx_baugrup ON documents (baugrup)')
    conn.commit()
    return conn

def extract_text(element, tag_name):
    # Hilfsfunktion, um den Text eines Tags zu finden
    found = element.find(f".//{tag_name}")
    if found is not None and found.text:
        return found.text.strip()
    return ""

def process_archives(limit=None):
    if not os.path.exists(OUTPUT_DIR):
        os.makedirs(OUTPUT_DIR)
        
    if not os.path.exists(TEMP_DIR):
        os.makedirs(TEMP_DIR)
        
    conn = init_db()
    cursor = conn.cursor()
    
    # Finde alle .wi Archive
    wi_files = []
    for root, _, files in os.walk(SOURCE_DIR):
        for f in files:
            if f.endswith('.wi'):
                wi_files.append(os.path.join(root, f))
                
    total_files = len(wi_files)
    if limit:
        wi_files = wi_files[:limit]
        total_files = len(wi_files)
        
    print(f"Gefundene .wi Archive: {total_files}")
    
    processed_archives = 0
    processed_xmls = 0
    start_time = time.time()
    
    # Regex-Fallback für sehr kaputtes XML
    re_marke = re.compile(r'<marke>(.*?)</marke>', re.IGNORECASE)
    re_modell = re.compile(r'<modell>(.*?)</modell>', re.IGNORECASE)
    re_obergrup = re.compile(r'<obergrup>(.*?)</obergrup>', re.IGNORECASE)
    re_baugrup = re.compile(r'<baugrup>(.*?)</baugrup>', re.IGNORECASE)
    re_titel = re.compile(r'<titel>(.*?)</titel>', re.IGNORECASE)
    
    for wi_file in wi_files:
        processed_archives += 1
        basename = os.path.basename(wi_file)
        print(f"[{processed_archives}/{total_files}] Verarbeite {basename}...")
        
        # Temp-Verzeichnis leeren
        for item in os.listdir(TEMP_DIR):
            item_path = os.path.join(TEMP_DIR, item)
            try:
                if os.path.isfile(item_path):
                    os.remove(item_path)
                elif os.path.isdir(item_path):
                    shutil.rmtree(item_path)
            except Exception as e:
                pass
                
        # Archiv entpacken
        cmd = [SEVENZIP_PATH, "e", wi_file, f"-o{TEMP_DIR}", "-y"]
        result = subprocess.run(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        if result.returncode not in (0, 1):
            print(f"  Fehler beim Entpacken von {basename}")
            continue
            
        extracted_xmls = glob.glob(os.path.join(TEMP_DIR, "*.xml"))
        
        for xml_file in extracted_xmls:
            xml_basename = os.path.basename(xml_file)
            new_filename = f"{os.path.splitext(basename)[0]}_{xml_basename}"
            dest_path = os.path.join(OUTPUT_DIR, new_filename)
            
            # Kopiere XML ins endgültige Verzeichnis
            try:
                shutil.copy2(xml_file, dest_path)
            except Exception:
                continue
                
            # XML lesen
            try:
                with open(dest_path, "r", encoding="utf-8") as f:
                    content = f.read()
            except UnicodeDecodeError:
                try:
                    with open(dest_path, "r", encoding="iso-8859-1") as f:
                        content = f.read()
                except Exception:
                    continue
            except Exception:
                continue
            
            # Metadaten extrahieren
            marke, modell, obergrup, baugrup, titel = "", "", "", "", ""
            
            # Versuch 1: ElementTree (manchmal schlägt dies fehl, da ElsaWin-XML kein sauberes Root-Element hat)
            try:
                # Da XML-Dateien oft fehlerhaft sind, probieren wir erst Regex
                raise Exception("Regex bevorzugt")
            except Exception:
                # Versuch 2: Regex
                m1 = re_marke.search(content)
                if m1: marke = m1.group(1).strip()
                
                # Bei Modellen können mehrere <modell> Tags existieren. Wir nehmen den ersten oder verketten sie.
                modelle = re_modell.findall(content)
                if modelle: modell = ", ".join(list(set(m.strip() for m in modelle)))
                
                m3 = re_obergrup.search(content)
                if m3: obergrup = m3.group(1).strip()
                
                m4 = re_baugrup.search(content)
                if m4: baugrup = m4.group(1).strip()
                
                m5 = re_titel.search(content)
                if m5: titel = m5.group(1).strip()
            
            # In Datenbank schreiben
            cursor.execute('''
                INSERT INTO documents (archive_name, xml_filename, filepath, marke, modell, obergrup, baugrup, titel)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?)
            ''', (basename, xml_basename, dest_path, marke, modell, obergrup, baugrup, titel))
            
            processed_xmls += 1
            
        conn.commit()
        
    conn.close()
    
    elapsed = time.time() - start_time
    print(f"\nFertig! {processed_archives} Archive und {processed_xmls} XML-Dateien in {elapsed:.2f} Sekunden verarbeitet.")
    print(f"Index-Datenbank gespeichert in {DB_PATH}")

if __name__ == "__main__":
    # Um alles zu entpacken, `limit=None` setzen. Für einen Testlauf `limit=10`.
    process_archives(limit=None)
