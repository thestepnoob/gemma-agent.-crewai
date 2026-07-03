import sys
import os
import asyncio
import datetime
import re
import json
import logging
import requests
import discord
from discord import app_commands
from discord.ext import commands
from dotenv import load_dotenv
from crewai import Agent, Task, Crew, Process, LLM

from tools import (
    ListDirectoryTool, ReadFileTool, WriteFileTool, DeleteFileTool,
    DiscordCleanDMsTool, DiscordDeleteMessageTool, DescribeImageTool,
    ExecuteTerminalCommandTool, DeepWebSearchTool, ReadWordDocumentTool,
    ReadExcelDocumentTool, WriteExcelDocumentTool, SystemMonitorTool,
    ReadClipboardTool, WriteClipboardTool, HardwarePerformanceDiagnosticTool,
    DiskManagementTool, DiscordListChannelsTool, DiscordFetchChannelMessagesTool,
    DiscordSendMessageTool, InteractiveBrowserTool
)
from tools.osint_tools import (
    username_search, email_recon, phone_lookup,
    domain_recon, ip_lookup, ssl_analysis, subdomain_enum, tech_stack
)

if hasattr(sys.stdout, 'reconfigure'): sys.stdout.reconfigure(encoding='utf-8')
if hasattr(sys.stderr, 'reconfigure'): sys.stderr.reconfigure(encoding='utf-8')

PROJECT_DIR = os.path.dirname(os.path.abspath(__file__))
LOG_DIR = os.path.join(PROJECT_DIR, "logs")
os.makedirs(LOG_DIR, exist_ok=True)
LOG_FILE = os.path.join(LOG_DIR, "discord_bot.log")

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
    handlers=[
        logging.FileHandler(LOG_FILE, encoding='utf-8')
    ] + ([logging.StreamHandler(sys.stdout)] if sys.stdout is not None else [])
)

load_dotenv()
DISCORD_TOKEN = os.getenv("DISCORD_TOKEN")
try:
    JANNI_USER_ID = int(os.getenv("JANNI_USER_ID", 572838735998353412))
except ValueError:
    JANNI_USER_ID = 572838735998353412

ATTACHMENT_DIR = os.path.join(PROJECT_DIR, "attachments")
LOGBOOK_DIR = os.path.join(PROJECT_DIR, "task_logbook")
PROMPTS_DIR = os.path.join(PROJECT_DIR, "prompts")
STATES_FILE = os.path.join(PROJECT_DIR, "states.json")
LAST_USER_FILE = os.path.join(PROJECT_DIR, "last_user_id.txt")

os.makedirs(ATTACHMENT_DIR, exist_ok=True)
os.makedirs(LOGBOOK_DIR, exist_ok=True)
os.makedirs(PROMPTS_DIR, exist_ok=True)

intents = discord.Intents.default()
intents.message_content = True
intents.messages = True
bot = commands.Bot(command_prefix="!", intents=intents)

llm = LLM(
    model="ollama/gemma4:12b",
    base_url="http://localhost:11434",
    temperature=0.3
)

all_tools = [
    ListDirectoryTool(), ReadFileTool(), WriteFileTool(), DeleteFileTool(),
    DiscordCleanDMsTool(), DiscordDeleteMessageTool(), DescribeImageTool(),
    ExecuteTerminalCommandTool(), DeepWebSearchTool(), ReadWordDocumentTool(),
    ReadExcelDocumentTool(), WriteExcelDocumentTool(), SystemMonitorTool(),
    ReadClipboardTool(), WriteClipboardTool(), HardwarePerformanceDiagnosticTool(),
    DiskManagementTool(), DiscordListChannelsTool(), DiscordFetchChannelMessagesTool(),
    DiscordSendMessageTool(), InteractiveBrowserTool()
]

def load_states():
    if os.path.exists(STATES_FILE):
        try:
            with open(STATES_FILE, "r", encoding="utf-8") as f:
                return json.load(f)
        except Exception as e:
            logging.error(f"Fehler beim Laden von states.json: {e}")
    return {}

def save_states(states):
    try:
        with open(STATES_FILE, "w", encoding="utf-8") as f:
            json.dump(states, f, indent=4, ensure_ascii=False)
    except Exception as e:
        logging.error(f"Fehler beim Speichern von states.json: {e}")

user_states = load_states()

def load_prompt(filename: str, default_text: str) -> str:
    prompt_path = os.path.join(PROMPTS_DIR, filename)
    if os.path.exists(prompt_path):
        try:
            with open(prompt_path, "r", encoding="utf-8") as f:
                return f.read().strip()
        except Exception as e:
            logging.error(f"Fehler beim Laden des Prompts '{filename}': {e}")
    return default_text

def get_personal_agent(is_dm: bool = True) -> Agent:
    default_prompt = (
        "Du bist ein loyaler, autonomer lokaler KI-Agent mit dem Namen 'Gemma'. "
        "Du antwortest IMMER auf Deutsch und sprichst die Benutzerin mit dem informellen 'du' an. "
        "Dein Kommunikationsstil zeichnet sich standardmäßig durch Sachlichkeit, Professionalität, Klarheit und Präzision aus."
    )
    prompt = load_prompt("personal_agent_prompt.txt", default_prompt)
    
    if not is_dm:
        # Server-Modus: Extrem lustig, sarkastisch, schwarzer Humor, Ironie
        prompt += (
            "\n\nACHTUNG (SERVER-MODUS): Du befindest dich in einem öffentlichen Server-Kanal. "
            "Dein Kommunikationsstil soll hier das genaue Gegenteil von professionell sein: Sei extrem lustig, "
            "reiße Witze, nutze schwarzen Humor, sarkastische Bemerkungen und pure Ironie. Sei frech, humorvoll und todes funny. "
            "Trotz der Witze und des schwarzen Humors erfüllst du deine Aufgaben weiterhin korrekt, "
            "aber deine Antworten müssen extrem witzig und sarkastisch formuliert sein, aber nicht krampfhaft auf jden Mikrometer."
        )
        role = "Dein todes funny, sarkastischer und witziger Server-Assistent Gemma"
        goal = "Erledige Aufgaben, verwalte das Dateisystem und bringe die Benutzerin mit schwarzem Humor und Sarkasmus zum Lachen."
    else:
        # DM-Modus: Absolut professionell und sachlich
        prompt += (
            "\n\nACHTUNG (DM-MODUS): Du befindest dich in einer Direktnachricht (DM). "
            "Dein Kommunikationsstil muss professionell, sachlich, höflich, klar und präzise, aber dennoch locker sein. "
            "Vermeide Witze, Sarkasmus und schwarzen Humor komplett."
        )
        role = "Dein präziser, professioneller persönlicher KI-Assistent Gemma"
        goal = "Erledige Aufgaben, verwalte das Dateisystem und unterstütze die Benutzerin effizient, höflich und sachlich."
    
    return Agent(
        role=role,
        goal=goal,
        backstory=prompt,
        verbose=True,
        allow_delegation=False,
        llm=llm,
        tools=all_tools
    )

def run_crew(task_description: str, is_dm: bool = True) -> str:
    p_agent = get_personal_agent(is_dm)
    expected_output = (
        "Eine klare, professionelle und präzise Antwort auf Deutsch." if is_dm else
        "Eine extrem witzige, sarkastische und humorvolle Antwort auf Deutsch (unter Verwendung von schwarzem Humor/Ironie)."
    )
    task = Task(
        description=task_description,
        expected_output=expected_output,
        agent=p_agent
    )
    crew = Crew(agents=[p_agent], tasks=[task], process=Process.sequential)
    return str(crew.kickoff())

def call_ollama(system_prompt: str, user_prompt: str) -> str:
    try:
        response = requests.post(
            "http://localhost:11434/api/chat",
            json={
                "model": "gemma4:12b",
                "messages": [
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": user_prompt}
                ],
                "stream": False,
                "options": {"temperature": 0.3}
            },
            timeout=30
        )
        response.raise_for_status()
        return response.json().get("message", {}).get("content", "").strip()
    except Exception as e:
        logging.error(f"Fehler beim Ollama API Call: {e}")
        return ""

def classify_is_smalltalk(prompt: str) -> bool:
    sys_instruction = (
        "Bestimme, ob die Nachricht des Benutzers reiner Smalltalk, eine Begrüßung oder "
        "allgemeine Konversation ohne System-Aktion ist (z. B. 'Hallo', 'Wie gehts?'). "
        "Wenn es eine Aufgabe ist, antworte 'NEIN'. Sonst 'JA'. Antworte AUSSCHLIESSLICH mit 'JA' oder 'NEIN'."
    )
    result = call_ollama(sys_instruction, f"Benutzernachricht: '{prompt}'").upper()
    return "JA" in result

def answer_smalltalk(prompt: str, is_dm: bool = True) -> str:
    if is_dm:
        sys_instruction = (
            "Du bist Gemma, ein persönlicher KI-Assistent. "
            "Dein Kommunikationsstil ist absolut professionell, sachlich, höflich und präzise. "
            "Antworte freundlich, kurz (1-2 Sätze) auf Deutsch. Nutze keinen Humor oder Sarkasmus."
        )
    else:
        sys_instruction = (
            "Du bist Gemma, ein persönlicher KI-Assistent. Du befindest dich auf einem Discord-Server. "
            "Dein Kommunikationsstil ist extrem witzig, sarkastisch, ironisch und voller schwarzem Humor. "
            "Antworte todes funny und kurz (1-2 Sätze) auf Deutsch."
        )
    res = call_ollama(sys_instruction, prompt)
    return res if res else ("Hallo! Wie kann ich dir helfen?" if is_dm else "Ja moin! Was gibt's?")

def classify_is_followup(current_prompt: str, last_task: str) -> bool:
    sys_instruction = (
        "Du bist ein Klassifikator. Entscheide ob die neue Benutzernachricht sich inhaltlich auf die vorherige Aufgabe "
        "bezieht (z.B. eine Nachbesserung, Anschlussfrage, Korrektur wie 'mach das nochmal rot' oder 'fasse das kürzer zusammen') "
        "oder ob es eine völlig neue, unabhängige Aufgabe ist.\n"
        "Antworte AUSSCHLIESSLICH mit 'JA' (es ist ein Follow-up) oder 'NEIN' (neues Thema)."
    )
    user_prompt = f"Vorherige Aufgabe: '{last_task}'\nNeue Nachricht: '{current_prompt}'"
    result = call_ollama(sys_instruction, user_prompt).upper()
    return "JA" in result

async def send_long_message(channel, text: str):
    if len(text) <= 1950:
        await channel.send(text)
        return
    
    current_chunk = []
    current_length = 0
    for line in text.splitlines(keepends=True):
        if len(line) > 1900:
            if current_chunk:
                await channel.send("".join(current_chunk))
                current_chunk = []
                current_length = 0
            for i in range(0, len(line), 1900):
                await channel.send(line[i:i+1900])
        else:
            if current_length + len(line) > 1900:
                await channel.send("".join(current_chunk))
                current_chunk = [line]
                current_length = len(line)
            else:
                current_chunk.append(line)
                current_length += len(line)
                
    if current_chunk:
        await channel.send("".join(current_chunk))

@bot.command(name="clear", aliases=["clean", "bereinigen"])
async def cmd_clear(ctx):
    if ctx.author.id != JANNI_USER_ID: return
    try:
        async for msg in ctx.channel.history(limit=100):
            if msg.author == bot.user:
                await msg.delete()
        if not isinstance(ctx.channel, discord.DMChannel):
            await ctx.message.delete()
        await ctx.send("Hallo! Ich bin jetzt online und einsatzbereit. Was kann ich heute für dich tun?")
        logging.info("Clear-Command ausgeführt.")
    except Exception as e:
        logging.error(f"Fehler bei !clear: {e}")

@bot.command(name="flush", aliases=["flush!"])
async def cmd_flush(ctx):
    if ctx.author.id != JANNI_USER_ID: return
    deleted = 0
    if os.path.exists(ATTACHMENT_DIR):
        for item in os.listdir(ATTACHMENT_DIR):
            p = os.path.join(ATTACHMENT_DIR, item)
            if os.path.isfile(p):
                try:
                    os.remove(p)
                    deleted += 1
                except: pass
    await ctx.send(f"🧹 Flush ausgeführt: {deleted} Anhänge gelöscht.")
    logging.info(f"Flush ausgeführt: {deleted} gelöscht.")

@bot.event
async def on_ready():
    logging.info(f"Eingeloggt als {bot.user.name}")
    
    # Slash-Commands mit Discord synchronisieren
    try:
        synced = await bot.tree.sync()
        logging.info(f"{len(synced)} Slash-Command(s) synchronisiert.")
    except Exception as e:
        logging.error(f"Fehler beim Synchronisieren der Slash-Commands: {e}")
    
    # Reset stuck states to IDLE
    modified = False
    for c_id, data in user_states.items():
        if data.get("state") == "EXECUTING":
            data["state"] = "IDLE"
            modified = True
    if modified:
        save_states(user_states)
        logging.info("Stuck EXECUTING states have been reset to IDLE.")

    target_user = None
    if os.path.exists(LAST_USER_FILE):
        try:
            with open(LAST_USER_FILE, "r") as f:
                target_user = await bot.fetch_user(int(f.read().strip()))
        except: pass
            
    if not target_user:
        try: target_user = await bot.fetch_user(JANNI_USER_ID)
        except: pass
            
    if target_user:
        try:
            dm_channel = target_user.dm_channel or await target_user.create_dm()
            greeting = "Hallo! Ich bin jetzt online und einsatzbereit. Was kann ich heute für dich tun?"
            async for msg in dm_channel.history(limit=50):
                if msg.author.id == target_user.id: break
                if msg.author == bot.user and msg.content == greeting:
                    await msg.delete()
            await target_user.send(greeting)
            logging.info(f"Begrüßung an {target_user.name} gesendet.")
        except Exception as e:
            logging.error(f"Fehler bei Begrüßung: {e}")

@bot.event
async def on_message(message: discord.Message):
    if message.author == bot.user: return
    if message.author.id != JANNI_USER_ID: return
    
    await bot.process_commands(message)
    if message.content.startswith("!"):
        return

    is_dm = isinstance(message.channel, discord.DMChannel)
    is_mentioned = bot.user in message.mentions
    is_reply = False
    if message.reference and message.reference.cached_message:
        is_reply = message.reference.cached_message.author == bot.user

    if is_dm or is_mentioned or is_reply:
        with open(LAST_USER_FILE, "w") as f:
            f.write(str(message.author.id))

        prompt = message.content.replace(f"<@{bot.user.id}>", "").replace(f"<@!{bot.user.id}>", "").strip()

        if not prompt and not message.attachments:
            await message.channel.send("Hallo! Wie kann ich helfen?")
            return

        c_id = str(message.channel.id)
        state_data = user_states.get(c_id, {"state": "IDLE"})

        if state_data.get("state") == "EXECUTING":
            await message.channel.send("⏳ Ich arbeite gerade noch an einer Aufgabe!")
            return

        new_downloads = []
        if message.attachments:
            for att in message.attachments:
                local_path = os.path.join(ATTACHMENT_DIR, f"{message.id}_{att.filename}")
                try:
                    await att.save(local_path)
                    new_downloads.append({"name": att.filename, "path": local_path})
                except Exception as e:
                    logging.error(f"Download-Fehler: {e}")

        task_desc = prompt or "Verarbeite die hochgeladenen Dateien."
        
        # Check Smalltalk
        is_small = await asyncio.to_thread(classify_is_smalltalk, task_desc)
        if is_small:
            ans = await asyncio.to_thread(answer_smalltalk, task_desc, is_dm)
            await send_long_message(message.channel, ans)
            return

        # Check Follow-Up
        last_task = state_data.get("last_task", "")
        last_result = state_data.get("last_result", "")
        last_files = state_data.get("last_files", [])
        
        env_ctx = f"\n\n--- KONTEXT-INFORMATIONEN ---\nAktuelle Kanal-ID: {c_id}\nKanalname: {getattr(message.channel, 'name', 'DM')}\nAutor: {message.author.name}\n"

        is_followup = False
        if last_task:
            is_followup = await asyncio.to_thread(classify_is_followup, task_desc, last_task)

        if is_followup:
            files_use = last_files + new_downloads
            ctx_str = "\nFolgende Anhänge stehen zur Verfügung:\n" + "\n".join([f"- {f['path']}" for f in files_use]) if files_use else ""
            full_prompt = f"Follow-Up Befehl des Users: {task_desc}\nVorherige Aufgabe: {last_task}\nVorheriges Ergebnis: {last_result}{ctx_str}{env_ctx}"
            current_task_title = f"{last_task} (Follow-Up: {task_desc})"
        else:
            files_use = new_downloads
            # Bereinige alte Dateien, wenn neues Thema
            for f_info in last_files:
                try: os.remove(f_info["path"])
                except: pass
            
            ctx_str = "\nFolgende Anhänge stehen zur Verfügung:\n" + "\n".join([f"- {f['path']}" for f in files_use]) if files_use else ""
            full_prompt = f"Befehl: {task_desc}{ctx_str}{env_ctx}"
            current_task_title = task_desc

        user_states[c_id] = {"state": "EXECUTING"}
        save_states(user_states)
        
        # Statt nativem `async with message.channel.typing():`, senden wir eine temporäre Nachricht
        status_msg = await message.channel.send("⚙️ *Gemma analysiert und bearbeitet die Anfrage im Hintergrund...*")

        try:
            res = await asyncio.to_thread(run_crew, full_prompt, is_dm)
            
            # Auto-Logging im Hintergrund
            task_clean = re.sub(r'[^a-z0-9\s_]', '', current_task_title.lower())
            task_clean = re.sub(r'[\s_]+', '_', task_clean)[:40].strip('_') or "aufgabe"
            now = datetime.datetime.now()
            log_file = os.path.join(LOGBOOK_DIR, f"{now.strftime('%d%m%Y')}_{task_clean}.md")
            content = f"# Aufgaben-Protokoll: {current_task_title}\n* **Datum:** {now.strftime('%d.%m.%Y %H:%M')}\n\n## Ergebnis:\n{res}\n"
            try:
                with open(log_file, "w", encoding="utf-8") as f:
                    f.write(content)
            except Exception as e:
                logging.error(f"Auto-Log Fehler: {e}")

            # State zurücksetzen und Kurzzeitgedächtnis speichern
            user_states[c_id] = {
                "state": "IDLE",
                "last_task": current_task_title,
                "last_result": res,
                "last_files": files_use
            }
            save_states(user_states)
            
            # Status-Nachricht löschen und Ergebnis senden
            try: await status_msg.delete()
            except: pass
            await send_long_message(message.channel, res)
            
        except Exception as e:
            user_states[c_id] = {"state": "IDLE"}
            save_states(user_states)
            try: await status_msg.edit(content=f"❌ Fehler bei der Ausführung: {e}")
            except: pass

# ============================================================
# OSINT Slash-Commands
# ============================================================

async def _send_osint_result(interaction: discord.Interaction, result: str):
    """Sendet ein OSINT-Ergebnis in Chunks über followup.send().
    Berücksichtigt das Discord-Limit von 2000 Zeichen pro Nachricht.
    """
    chunks = []
    current = ""
    for line in result.split("\n"):
        # +1 für den Zeilenumbruch
        if len(current) + len(line) + 1 > 1900:
            chunks.append(current)
            current = line
        else:
            current += ("\n" if current else "") + line
    if current:
        chunks.append(current)

    for i, chunk in enumerate(chunks):
        if i == 0:
            await interaction.followup.send(chunk)
        else:
            await interaction.channel.send(chunk)


@bot.tree.command(name="p-osint", description="Personen-OSINT: Benutzernamen, E-Mails und Telefonnummern recherchieren")
@app_commands.describe(
    aktion="Art der OSINT-Recherche",
    query="Suchbegriff (Benutzername, E-Mail-Adresse oder Telefonnummer)"
)
@app_commands.choices(aktion=[
    app_commands.Choice(name="\U0001f50d Benutzername suchen (30+ Plattformen)", value="username"),
    app_commands.Choice(name="\U0001f4e7 E-Mail-Adresse analysieren", value="email"),
    app_commands.Choice(name="\U0001f4f1 Telefonnummer analysieren", value="phone"),
])
async def p_osint_cmd(interaction: discord.Interaction, aktion: app_commands.Choice[str], query: str):
    """Personen-OSINT Slash-Command."""
    if interaction.user.id != JANNI_USER_ID:
        await interaction.response.send_message("\u274c Nicht autorisiert.", ephemeral=True)
        return

    await interaction.response.defer(thinking=True)
    logging.info(f"OSINT /p-osint gestartet: aktion={aktion.value}, query={query}")

    try:
        action_map = {
            "username": username_search,
            "email": email_recon,
            "phone": phone_lookup,
        }

        func = action_map.get(aktion.value)
        if not func:
            await interaction.followup.send("\u274c Unbekannte Aktion.")
            return

        result = await asyncio.to_thread(func, query)
        await _send_osint_result(interaction, result)
        logging.info(f"OSINT /p-osint abgeschlossen: aktion={aktion.value}")

    except Exception as e:
        logging.error(f"OSINT /p-osint Fehler: {e}")
        await interaction.followup.send(f"\u274c Fehler bei der OSINT-Analyse: {str(e)}")


@bot.tree.command(name="i-osint", description="Infrastruktur-OSINT: Domains, IPs, SSL und Technologien analysieren")
@app_commands.describe(
    aktion="Art der OSINT-Recherche",
    query="Suchbegriff (Domain, IP-Adresse oder URL)"
)
@app_commands.choices(aktion=[
    app_commands.Choice(name="\U0001f310 Domain-Aufklärung (WHOIS, DNS, Security)", value="domain"),
    app_commands.Choice(name="\U0001f50d IP-Adresse analysieren (Geo, ISP, ASN)", value="ip"),
    app_commands.Choice(name="\U0001f512 SSL/TLS-Zertifikat analysieren", value="ssl"),
    app_commands.Choice(name="\U0001f5fa\ufe0f Subdomains finden (CT-Logs + DNS)", value="subdomains"),
    app_commands.Choice(name="\u2699\ufe0f Tech-Stack erkennen (CMS, Frameworks, CDN)", value="techstack"),
])
async def i_osint_cmd(interaction: discord.Interaction, aktion: app_commands.Choice[str], query: str):
    """Infrastruktur-OSINT Slash-Command."""
    if interaction.user.id != JANNI_USER_ID:
        await interaction.response.send_message("\u274c Nicht autorisiert.", ephemeral=True)
        return

    await interaction.response.defer(thinking=True)
    logging.info(f"OSINT /i-osint gestartet: aktion={aktion.value}, query={query}")

    try:
        action_map = {
            "domain": domain_recon,
            "ip": ip_lookup,
            "ssl": ssl_analysis,
            "subdomains": subdomain_enum,
            "techstack": tech_stack,
        }

        func = action_map.get(aktion.value)
        if not func:
            await interaction.followup.send("\u274c Unbekannte Aktion.")
            return

        result = await asyncio.to_thread(func, query)
        await _send_osint_result(interaction, result)
        logging.info(f"OSINT /i-osint abgeschlossen: aktion={aktion.value}")

    except Exception as e:
        logging.error(f"OSINT /i-osint Fehler: {e}")
        await interaction.followup.send(f"\u274c Fehler bei der OSINT-Analyse: {str(e)}")


if __name__ == "__main__":
    if DISCORD_TOKEN:
        bot.run(DISCORD_TOKEN)
    else:
        logging.error("Kein DISCORD_TOKEN gefunden!")
