# Integration von ElsaWin in den Gemma-Agenten

Dieses Dokument fasst die Erkenntnisse und Lösungsansätze zusammen, um die Reparaturdaten aus ElsaWin an den autonomen Gemma-Agenten anzubinden.

---

## 1. Die Herausforderung: Das Container-Format
ElsaWin (Legacy-Windows-Anwendung) speichert Reparaturanleitungen nicht als plain HTML, sondern in proprietären `.wi` Archiven (umbenannte CAB-Dateien) unter `C:\ElsaWin\docs\`.
Das System rendert diese Dokumente zur Laufzeit über ein proprietäres `vw-wi://` Protokoll in einem eingebetteten Internet Explorer / Edge Control.

---

## 2. Verworfen: Playwright, SQL-Server und API-Brücken
Sämtliche Pläne, das ElsaWin-Frontend fernzusteuern (Playwright), die `vw-wi://` API anzuzapfen oder die interne SQL-Datenbank (`ELSAWINDB`) auszulesen, wurden aufgrund von Architektur-Hürden und fehlenden Passwörtern verworfen.

---

## 3. Der ultimative Lösungsansatz: Direkte XML-Extraktion ("Plan F")
Die Durchbruch-Erkenntnis: Wenn man die `.wi`-Archive entpackt, erhält man reine `.xml`-Dateien (z. B. `75896101.xml`). 
Diese Dateien sind **selbstbeschreibend** und enthalten im XSLT-kompatiblen Header alle notwendigen Metadaten für das Inhaltsverzeichnis:
```xml
<marke>VW</marke>
<modell>Eos</modell>
<obergrup>Fahrwerk</obergrup>
<baugrup>Fahrwerk, Achsen, Lenkung</baugrup>
<titel>Prüfliste für die Beurteilung des Fahrwerkes an Unfall-Fahrzeugen</titel>
```

Da diese rohen XML-Dateien semantisch hervorragend strukturiert sind (`<absatz>`, `<aufzaehlg>`), sind sie für ein LLM / einen KI-Agenten **besser lesbar** als das XSLT-gerenderte HTML-Dokument.

### Die Architektur für den Gemma-Agenten:
1. **Transfer:** Der gesamte Ordner `C:\ElsaWin\docs\` wird aus der VM auf das Host-System des Agenten kopiert oder freigegeben.
2. **Entpacken:** Ein Python-Tool im Agenten-Framework (`cabextract` oder native Windows-Bordmittel) entpackt alle `.wi`-Archive.
3. **Indexierung:** Ein Python-Skript durchläuft alle `.xml`-Dateien, extrahiert die Metadaten (`<marke>`, `<modell>`, `<baugrup>`) und baut eine eigene, leichtgewichtige lokale Datenbank (SQLite oder JSON-Index) auf dem Host auf.
4. **Retrieval:** Der Agent sucht bei einer Anfrage in seinem eigenen Index, öffnet die entsprechende XML-Datei und liest die Reparaturanleitung im Raw-Format aus. 

Die Abhängigkeit zur ElsaWin-Anwendung, zur VM und zur Windows-Registry ist damit zu 100% eliminiert.

---

*Aktualisiert am: 26. Juni 2026*
