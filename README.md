# Gemma Agent: Local AI Assistant & Discord Bot

A powerful, autonomous Discord bot powered by **CrewAI** and a local **Gemma AI** (via Ollama). This bot combines advanced LLM capabilities with direct system access, OSINT utilities, and a dedicated integration for ElsaWin repair data.

## Features

### 🧠 Local AI Intelligence
* Powered by **Ollama** using the `gemma4:12b` model by default.
* Runs entirely locally and privacy-focused, without sending data to external APIs.
* Utilizes the **CrewAI** framework to autonomously plan and execute tasks.

### 🎭 Context-Sensitive Dual Personality
* **DM Mode (Direct Messages):** Polite, objective, precise, and highly professional. Ideal for private tasks, system maintenance, and file management.
* **Server Mode (Public Channels):** Humorous, highly sarcastic, cheeky, and packed with dry/dark humor. Perfect for entertainment while still getting tasks done.

### 🛠️ Advanced Tools (Capabilities)
The bot has direct access to various system and API modules:
* **System & File Management:** Execute shell commands, browse directories, read/write/delete files, monitor CPU/RAM usage, and diagnose hardware/disk health.
* **Document Processing:** Support for reading and writing Excel sheets (`.xlsx`) and Word documents (`.docx`).
* **Web & Search Tools:** Deep web search and an integrated interactive web browser.
* **OSINT (Open Source Intelligence):** SSL analysis, IP/domain intelligence, subdomain enumeration, tech-stack detection, email recon, phone lookup, and username search.
* **Discord Utilities:** List channels, fetch chat history, clean bot messages, and clear DMs.
* **Clipboard:** Direct access to read and write the system clipboard.

### 🚗 ElsaWin Integration
Includes specialized scripts to process Volkswagen/Audi ElsaWin repair manuals and workshop data:
* XML structure extraction.
* Indexing and searching repair manuals.
* Formatting and preparing vehicle data for Discord.

---

## Installation & Setup

### Prerequisites
1. **Ollama:** Installed and running with the appropriate Gemma model (e.g. `gemma4:12b`).
2. **Python 3.10+**

### 1. Clone the Repository
```bash
git clone https://github.com/thestepnoob/gemma-agent.-crewai.git
cd gemma-agent.-crewai
```

### 2. Create Virtual Environment & Install Dependencies
```bash
python -m venv venv
venv\Scripts\activate
pip install -r requirements.txt
```

### 3. Configuration (`.env`)
Create a `.env` file in the root directory and add your keys (this file is excluded from git commits via `.gitignore`):
```env
DISCORD_TOKEN=your_discord_bot_token
JANNI_USER_ID=your_discord_user_id
```

### 4. Run the Bot
Use the provided batch script or run it directly:
* **Direct:** `python discord_bot.py`
* **Script (Windows):** `start_bot.bat` (or background via `start_bot_background.vbs`)

---

## Project Structure
* [discord_bot.py](file:///c:/Users/iboer/gemma_agent/discord_bot.py): Main entry point for the Discord bot and CrewAI agent orchestration.
* [tools/](file:///c:/Users/iboer/gemma_agent/tools/): Custom agent tools (OSINT, system diagnostics, web utilities, etc.).
* [elsawin/](file:///c:/Users/iboer/gemma_agent/elsawin/): Scripts for ElsaWin manual extraction and search.
* [scripts/](file:///c:/Users/iboer/gemma_agent/scripts/): Helper scripts (e.g. cleaning DMs).
* [requirements.txt](file:///c:/Users/iboer/gemma_agent/requirements.txt): List of Python dependencies.

---

## Legal
* [Terms of Service](file:///c:/Users/iboer/gemma_agent/Nutzungsbedingungen.md)
* [Privacy Policy](file:///c:/Users/iboer/gemma_agent/Datenschutzerklaerung.md)
