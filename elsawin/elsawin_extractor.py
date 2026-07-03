import os
import subprocess
import shutil
import glob
import re

# Configuration
SOURCE_DIR = r"C:\Users\iboer\gemma_agent\elsawin\balls"
OUTPUT_DIR = r"C:\Users\iboer\gemma_agent\elsawin\GolfPlus_CAXA_Data"
TEMP_DIR = r"C:\Users\iboer\gemma_agent\elsawin\temp_extract"
SEVENZIP_PATH = r"C:\Program Files\7-Zip\7z.exe"

# Smarter Regex patterns to avoid false positives (like tool numbers "VAS 5216")
PATTERNS = [
    r'>Golf\s*Plus<',           # Exact XML tag content
    r'"Golf\s*Plus"',           # Attribute content
    r'>CAXA<',                  # Exact motor code in tag
    r'motor-kb="CAXA"',         # Exact motor code in attribute
    r'>NBW<',                   # Exact gearbox in tag
    r'getriebe-kb="NBW"',       # Exact gearbox in attribute
    r'verkaufstyp="[^"]*521[^"]*"',  # Starts with 521 in attribute
    r'<verkaufstyp>521',        # Starts with 521 in tag
    r'typen-bez="[^"]*521[^"]*"'
]

def extract_and_filter(max_files=10):
    if not os.path.exists(OUTPUT_DIR):
        os.makedirs(OUTPUT_DIR)
        
    if not os.path.exists(TEMP_DIR):
        os.makedirs(TEMP_DIR)
        
    wi_files = []
    for root, _, files in os.walk(SOURCE_DIR):
        for f in files:
            if f.endswith('.wi'):
                wi_files.append(os.path.join(root, f))
                
    print(f"Found {len(wi_files)} .wi files to process. Running test on max {max_files} files.")
    
    compiled_patterns = [re.compile(p, re.IGNORECASE) for p in PATTERNS]
    processed = 0
    hits = 0
    
    # Clean output dir for testing
    for item in os.listdir(OUTPUT_DIR):
        item_path = os.path.join(OUTPUT_DIR, item)
        if os.path.isfile(item_path):
            os.remove(item_path)
            
    for wi_file in wi_files[:max_files]:
        processed += 1
        basename = os.path.basename(wi_file)
        print(f"[{processed}/{max_files}] Processing {basename}...")
        
        # Clear temp dir to avoid mixing files from different archives
        for item in os.listdir(TEMP_DIR):
            item_path = os.path.join(TEMP_DIR, item)
            if os.path.isfile(item_path):
                try:
                    os.remove(item_path)
                except:
                    pass
            elif os.path.isdir(item_path):
                try:
                    shutil.rmtree(item_path)
                except:
                    pass
                
        # Extract using 7z (OLE Compound File format)
        cmd = [SEVENZIP_PATH, "e", wi_file, f"-o{TEMP_DIR}", "-y"]
        result = subprocess.run(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        if result.returncode != 0 and result.returncode != 1:
            print(f"  Failed to extract {basename}: {result.stderr.decode('utf-8', errors='ignore')}")
            continue
            
        extracted_xmls = glob.glob(os.path.join(TEMP_DIR, "*.xml"))
        print(f"  Extracted {len(extracted_xmls)} XML files.")
        
        for xml_file in extracted_xmls:
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
                    
            # Check keywords using Regex
            match = False
            for pattern in compiled_patterns:
                if pattern.search(content):
                    match = True
                    break
                    
            if match:
                xml_basename = os.path.basename(xml_file)
                new_filename = f"{os.path.splitext(basename)[0]}_{xml_basename}"
                dest_path = os.path.join(OUTPUT_DIR, new_filename)
                shutil.copy2(xml_file, dest_path)
                hits += 1
                
    print(f"\nDone! Processed {processed} .wi archives.")
    print(f"Found {hits} matching XML documents and saved them to {OUTPUT_DIR}.")

if __name__ == "__main__":
    extract_and_filter(10)
