import re

def clean_text(text):
    if not text:
        return ""
    # Entfernt unnötige Leerzeichen und Newlines
    return re.sub(r'\s+', ' ', text).strip()

def xml_to_discord_md(xml_string):
    """
    Konvertiert rohes ElsaWin XML in ein lesbares Discord-Markdown-Format.
    Dadurch spart der Agent Tokens und kann die Anleitung direkt posten.
    """
    # 1. Entferne den Vorspann (Metadaten), wir brauchen nur den Inhalt
    xml_string = re.sub(r'<vorspann.*?</vorspann>', '', xml_string, flags=re.IGNORECASE | re.DOTALL)
    
    # 2. Überschriften (titel)
    xml_string = re.sub(r'<titel>(.*?)</titel>', r'\n**\1**\n', xml_string, flags=re.IGNORECASE)
    
    # 3. Warnungen / Hinweise (als Blockquotes)
    xml_string = re.sub(r'<(?:warnung|vorsicht|hinweis)[^>]*>(.*?)</(?:warnung|vorsicht|hinweis)>', 
                        r'\n> ⚠️ **HINWEIS/WARNUNG:** \1\n', xml_string, flags=re.IGNORECASE | re.DOTALL)
    
    # 4. Listenpunkte
    xml_string = re.sub(r'<listenpkt[^>]*>(.*?)</listenpkt>', r'- \1\n', xml_string, flags=re.IGNORECASE | re.DOTALL)
    xml_string = re.sub(r'<aufzaehlg[^>]*>(.*?)</aufzaehlg>', r'\n\1\n', xml_string, flags=re.IGNORECASE | re.DOTALL)
    
    # 5. Absätze
    xml_string = re.sub(r'<absatz[^>]*>(.*?)</absatz>', r'\1\n\n', xml_string, flags=re.IGNORECASE | re.DOTALL)
    
    # 6. Tabellen (sehr primitiv: Zellen mit | trennen)
    xml_string = re.sub(r'<tabelle[^>]*>(.*?)</tabelle>', r'\n\1\n', xml_string, flags=re.IGNORECASE | re.DOTALL)
    xml_string = re.sub(r'<zeile[^>]*>(.*?)</zeile>', r'\1\n', xml_string, flags=re.IGNORECASE | re.DOTALL)
    xml_string = re.sub(r'<spalte[^>]*>(.*?)</spalte>', r' | \1', xml_string, flags=re.IGNORECASE | re.DOTALL)
    
    # 7. Hervorhebungen (fett)
    xml_string = re.sub(r'<g[^>]*>(.*?)</g>', r'**\1**', xml_string, flags=re.IGNORECASE | re.DOTALL)
    
    # 8. Alle restlichen XML-Tags restlos entfernen
    markdown = re.sub(r'<[^>]+>', '', xml_string)
    
    # 9. Aufräumen (Mehrfache Newlines reduzieren)
    markdown = re.sub(r'\n{3,}', '\n\n', markdown)
    
    # HTML Entities decodieren (z.B. &lt; -> <)
    markdown = markdown.replace('&lt;', '<').replace('&gt;', '>').replace('&amp;', '&')
    
    return markdown.strip()

if __name__ == "__main__":
    # Kleiner Test
    test_xml = """<h-kap><titel>Motor ausbauen</titel>
    <warnung>Batterie abklemmen!</warnung>
    <absatz>Das Fahrzeug auf eine Hebebühne fahren.</absatz>
    <aufzaehlg>
        <listenpkt>Schraube <g>A</g> lösen.</listenpkt>
        <listenpkt>Kabelbaum abziehen.</listenpkt>
    </aufzaehlg>
    </h-kap>"""
    
    print(xml_to_discord_md(test_xml))
