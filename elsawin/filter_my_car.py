import os
import glob
import re
import shutil
import time

SOURCE_DIR = r"C:\Users\iboer\gemma_agent\elsawin\extracted_xmls"
OUTPUT_DIR = r"C:\Users\iboer\gemma_agent\elsawin\GolfPlus_CAXA_NBW_Data"

def filter_my_car():
    if not os.path.exists(OUTPUT_DIR):
        os.makedirs(OUTPUT_DIR)
        
    xml_files = glob.glob(os.path.join(SOURCE_DIR, "*.xml"))
    print(f"Prüfe {len(xml_files)} extrahierte XML-Dateien auf dein Auto (Golf Plus 521, CAXA, NBW)...")
    
    # Regex Patterns für dein spezifisches Auto
    # Wir suchen nach der Basis 521 (Golf Plus) oder exakt 5213G2 / 5212G2
    re_verkaufstyp = re.compile(r'verkaufstyp="[^"]*(?:521|5213G2|5212G2)[^"]*"', re.IGNORECASE)
    re_typen_bez = re.compile(r'typen-bez="[^"]*(?:521|5213G2|5212G2)[^"]*"', re.IGNORECASE)
    re_tag_verkaufstyp = re.compile(r'<verkaufstyp>(?:521|5213G2|5212G2)</verkaufstyp>', re.IGNORECASE)
    
    # Motor & Getriebe
    re_motor = re.compile(r'motor-kb="([^"]+)"', re.IGNORECASE)
    re_getriebe = re.compile(r'getriebe-kb="([^"]+)"', re.IGNORECASE)
    
    re_caxa = re.compile(r'CAXA', re.IGNORECASE)
    re_nbw = re.compile(r'NBW', re.IGNORECASE)
    
    hits = 0
    start_time = time.time()
    
    for i, xml_file in enumerate(xml_files):
        if i % 10000 == 0 and i > 0:
            print(f"... {i} Dateien geprüft, bisher {hits} Treffer.")
            
        try:
            with open(xml_file, "r", encoding="utf-8") as f:
                content = f.read()
        except UnicodeDecodeError:
            try:
                with open(xml_file, "r", encoding="iso-8859-1") as f:
                    content = f.read()
            except Exception:
                continue
        except Exception:
            continue
            
        # 1. Bedingung: Ist es überhaupt ein Golf Plus (521)?
        is_golf_plus = (
            re_verkaufstyp.search(content) or 
            re_typen_bez.search(content) or 
            re_tag_verkaufstyp.search(content) or
            "Golf Plus" in content
        )
        
        # WICHTIG: Wenn das Dokument NUR für 3G2 (Passat) ist und nicht für 521, überspringen wir es.
        # Das decken wir ab, indem wir fordern, dass 521 (oder Golf Plus) zwingend vorkommen muss.
        if not is_golf_plus:
            continue
            
        # 2. Bedingung: Motor & Getriebe Check
        # Wenn das Dokument Motorspezifisch ist, MUSS es CAXA enthalten.
        # Wenn es Getriebespezifisch ist, MUSS es NBW enthalten.
        # Wenn es generisch ist (Karosserie, Bremsen etc.), hat es diese Tags oft nicht -> dann behalten wir es.
        
        motor_match = re_motor.search(content)
        getriebe_match = re_getriebe.search(content)
        
        valid = True
        
        if motor_match:
            motor_codes = motor_match.group(1).upper()
            if "CAXA" not in motor_codes:
                valid = False # Motorspezifisches Dokument, aber falscher Motor
                
        if getriebe_match and valid:
            getriebe_codes = getriebe_match.group(1).upper()
            if "NBW" not in getriebe_codes:
                valid = False # Getriebespezifisches Dokument, aber falsches Getriebe
                
        # Alternativ: Manchmal stehen CAXA/NBW als freier Text in <motor-kb> Tags
        if not valid:
            # Falls die Attribute nicht passten, prüfen wir, ob die Codes frei im Text stehen
            if re_caxa.search(content) or re_nbw.search(content):
                valid = True
                
        if valid:
            # Kopiere die Datei in deinen persönlichen Auto-Ordner
            dest_path = os.path.join(OUTPUT_DIR, os.path.basename(xml_file))
            shutil.copy2(xml_file, dest_path)
            hits += 1

    elapsed = time.time() - start_time
    print(f"\nFertig! In {elapsed:.1f} Sekunden {len(xml_files)} Dateien geprüft.")
    print(f"Es wurden exakt {hits} Dokumente für DEIN Auto gefunden und nach {OUTPUT_DIR} kopiert.")

if __name__ == "__main__":
    filter_my_car()
