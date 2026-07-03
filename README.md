# Gemma Agent: Lokaler KI-Assistent & Discord-Bot

Ein mächtiger, autonomer Discord-Bot auf Basis von **CrewAI** und einer lokalen **Gemma KI** (via Ollama). Dieser Bot verbindet hochentwickelte Sprachmodell-Fähigkeiten mit direktem Systemzugriff, OSINT-Werkzeugen und einer speziellen Integration für ElsaWin-Reparaturdaten.

## Features

### 🧠 Lokale KI-Intelligenz
* Basiert standardmäßig auf **Ollama** mit dem Modell `gemma4:12b`.
* Arbeitet vollkommen lokal und datenschutzfreundlich, ohne Daten an externe APIs zu senden.
* Nutzt das **CrewAI**-Framework, um komplexe Aufgaben autonom zu planen und durchzuführen.

### 🎭 Duales Persönlichkeitssystem (Kontextsensitiv)
* **DM-Modus (Direktnachrichten):** Höflich, sachlich, präzise und absolut professionell. Ideal für ungestörtes Arbeiten, Systempflege und Dateiverwaltung.
* **Server-Modus (Kanäle):** Humorvoll, extrem sarkastisch, frech und mit einer gesunden Dosis schwarzem Humor. Perfekt zur Unterhaltung auf dem Server, während er dennoch seine Aufgaben zuverlässig erledigt.

### 🛠️ Mächtige Werkzeuge (Tools)
Der Bot verfügt über direkten Zugriff auf zahlreiche Module:
* **System- & Dateiverwaltung:** Terminal-Befehle ausführen, Ordner durchsuchen, Dateien lesen/schreiben/löschen, CPU-/Arbeitsspeicher-Monitoring, Hardware- und Festplattendiagnose.
* **Dokumentenverarbeitung:** Unterstützung für das Lesen und Schreiben von Excel-Tabellen (`.xlsx`) und Word-Dokumenten (`.docx`).
* **Web- & Recherche-Tools:** Deep-Web-Suche und ein integrierter interaktiver Webbrowser.
* **OSINT (Open Source Intelligence):** SSL-Analysen, IP- und Domain-Recherche, Subdomain-Enumeration, Tech-Stack-Erkennung, E-Mail-Aufklärung, Telefonnummern-Lookup und Benutzernamensuche.
* **Discord-Verwaltung:** Kanäle auflisten, Chatverläufe auslesen, eigene Nachrichten bereinigen und DMs aufräumen.
* **Zwischenablage:** Zugriff auf die System-Zwischenablage (Lesen/Schreiben).

### 🚗 ElsaWin-Spezialintegration
Enthält spezialisierte Skripte zur Verarbeitung von Reparatur- und Werkstattdaten der ElsaWin-Datenbanken (z. B. Volkswagen/Audi):
* Extrahieren von XML-Datenstrukturen.
* Durchsuchen und Indexieren von Reparaturleitfäden.
* Strukturierte Aufbereitung und Formatierung von Autodaten für Discord.

---

## Installation & Setup

### Voraussetzungen
1. **Ollama:** Installiert und betriebsbereit mit dem entsprechenden Gemma-Modell (z. B. `gemma4:12b` oder ein anderes lokales Modell).
2. **Python 3.10+**

### 1. Repository klonen
```bash
git clone https://github.com/thestepnoob/gemma-agent.-crewai.git
cd gemma-agent.-crewai
```

### 2. Virtuelle Umgebung erstellen & Abhängigkeiten installieren
```bash
python -m venv venv
venv\Scripts\activate
pip install -r requirements.txt
```

### 3. Konfiguration (`.env`)
Erstelle eine Datei namens `.env` im Hauptverzeichnis des Projekts und trage deine Token und IDs ein (diese Datei wird dank `.gitignore` niemals hochgeladen):
```env
DISCORD_TOKEN=dein_discord_bot_token
JANNI_USER_ID=deine_discord_user_id
```

### 4. Bot starten
Verwende die mitgelieferte Batch-Datei oder starte das Skript direkt:
* **Direkt:** `python discord_bot.py`
* **Per Skript (Windows):** `start_bot.bat` (oder im Hintergrund via `start_bot_background.vbs`)

---

## Projektstruktur
* [discord_bot.py](file:///c:/Users/iboer/gemma_agent/discord_bot.py): Das Hauptskript des Discord-Bots und die CrewAI-Steuerung.
* [tools/](file:///c:/Users/iboer/gemma_agent/tools/): Eigene Werkzeuge für den Agenten (OSINT, System, Web, Discord etc.).
* [elsawin/](file:///c:/Users/iboer/gemma_agent/elsawin/): Skripte zur Extraktion und Suche in ElsaWin-Reparaturleitfäden.
* [scripts/](file:///c:/Users/iboer/gemma_agent/scripts/): Hilfsskripte (z. B. zum automatischen Löschen von Direktnachrichten).
* [requirements.txt](file:///c:/Users/iboer/gemma_agent/requirements.txt): Liste der benötigten Python-Pakete.

---

## Rechtliche Hinweise
* [Nutzungsbedingungen](file:///c:/Users/iboer/gemma_agent/Nutzungsbedingungen.md)
* [Datenschutzerklärung](file:///c:/Users/iboer/gemma_agent/Datenschutzerklaerung.md)
