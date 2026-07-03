import os
import requests
from typing import Optional
from crewai.tools import BaseTool
from dotenv import load_dotenv

load_dotenv()
DISCORD_TOKEN = os.getenv("DISCORD_TOKEN")

class DiscordCleanDMsTool(BaseTool):
    name: str = "Discord Chatverlauf bereinigen"
    description: str = (
        "Löscht alle Nachrichten, die von dir (dem Bot selbst) in diesem Discord-Kanal gesendet wurden. "
        "Erfordert die channel_id des Kanals als Argument."
    )

    def _run(self, channel_id: str) -> str:
        if not DISCORD_TOKEN:
            return "Fehler: Kein DISCORD_TOKEN in den Umgebungsvariablen gefunden."
        
        headers = {
            "Authorization": f"Bot {DISCORD_TOKEN}",
            "Content-Type": "application/json"
        }
        
        try:
            me_resp = requests.get("https://discord.com/api/v10/users/@me", headers=headers)
            if me_resp.status_code != 200:
                return f"Fehler beim Abrufen der Bot-ID: {me_resp.text}"
            bot_id = me_resp.json()["id"]
            
            history_url = f"https://discord.com/api/v10/channels/{channel_id}/messages?limit=100"
            hist_resp = requests.get(history_url, headers=headers)
            if hist_resp.status_code != 200:
                return f"Fehler beim Abrufen des Chatverlaufs: {hist_resp.text}"
            
            messages = hist_resp.json()
            deleted_count = 0
            
            for msg in messages:
                if msg["author"]["id"] == bot_id:
                    del_url = f"https://discord.com/api/v10/channels/{channel_id}/messages/{msg['id']}"
                    del_resp = requests.delete(del_url, headers=headers)
                    if del_resp.status_code in [204, 200]:
                        deleted_count += 1
            
            return f"Erfolgreich: Ich habe {deleted_count} meiner eigenen Nachrichten in diesem Kanal gelöscht."
        except Exception as e:
            return f"Fehler bei der Bereinigung: {str(e)}"

class DiscordDeleteMessageTool(BaseTool):
    name: str = "Discord Nachricht loeschen"
    description: str = (
        "Löscht eine spezifische Nachricht in einem Discord-Kanal anhand der channel_id und message_id. "
        "Hinweis: Du kannst in DMs nur deine eigenen Nachrichten löschen."
    )

    def _run(self, channel_id: str, message_id: str) -> str:
        if not DISCORD_TOKEN:
            return "Fehler: Kein DISCORD_TOKEN gefunden."
        
        headers = {"Authorization": f"Bot {DISCORD_TOKEN}"}
        try:
            del_url = f"https://discord.com/api/v10/channels/{channel_id}/messages/{message_id}"
            resp = requests.delete(del_url, headers=headers)
            if resp.status_code in [200, 204]:
                return f"Erfolgreich: Nachricht mit ID {message_id} im Kanal {channel_id} gelöscht."
            else:
                return f"Fehler beim Löschen der Nachricht: {resp.text}"
        except Exception as e:
            return f"Fehler beim Löschen: {str(e)}"

class DiscordListChannelsTool(BaseTool):
    name: str = "Discord Server Kanaele auflisten"
    description: str = (
        "Listet alle Discord-Server (Guilds) auf, in denen der Bot Mitglied ist, "
        "sowie alle Text-Kanäle dieser Server mit ihren Namen und IDs."
    )

    def _run(self) -> str:
        if not DISCORD_TOKEN:
            return "Fehler: Kein DISCORD_TOKEN gefunden."
        
        headers = {"Authorization": f"Bot {DISCORD_TOKEN}"}
        try:
            guilds_resp = requests.get("https://discord.com/api/v10/users/@me/guilds", headers=headers)
            if guilds_resp.status_code != 200:
                return f"Fehler beim Abrufen der Guilds: {guilds_resp.text}"
            
            guilds = guilds_resp.json()
            if not guilds:
                return "Der Bot befindet sich auf keinem Server."
            
            result = []
            for guild in guilds:
                g_id = guild["id"]
                g_name = guild["name"]
                result.append(f"Server: {g_name} (ID: {g_id})")
                
                chan_resp = requests.get(f"https://discord.com/api/v10/guilds/{g_id}/channels", headers=headers)
                if chan_resp.status_code == 200:
                    channels = chan_resp.json()
                    text_channels = [c for c in channels if c.get("type") == 0]
                    for chan in text_channels:
                        result.append(f"  - #{chan['name']} (ID: {chan['id']})")
                else:
                    result.append(f"  Fehler beim Abrufen der Kanäle: {chan_resp.text}")
            
            return "\n".join(result)
        except Exception as e:
            return f"Fehler beim Auflisten der Kanäle: {str(e)}"

class DiscordFetchChannelMessagesTool(BaseTool):
    name: str = "Discord Kanal Nachrichten abrufen"
    description: str = (
        "Ruft die letzten Nachrichten aus einem bestimmten Discord-Kanal ab. "
        "Erfordert die channel_id. Optional kann ein 'start_date' im Format 'YYYY-MM-DD HH:MM:SS' angegeben werden, "
        "um nur Nachrichten abzurufen, die nach diesem Zeitpunkt gesendet wurden. "
        "Gibt bis zu 100 Nachrichten zurück."
    )

    def _run(self, channel_id: str, start_date: str = "") -> str:
        if not DISCORD_TOKEN:
            return "Fehler: Kein DISCORD_TOKEN gefunden."
        
        channel_id = channel_id.replace("<#", "").replace(">", "").strip()
        
        headers = {"Authorization": f"Bot {DISCORD_TOKEN}"}
        try:
            url = f"https://discord.com/api/v10/channels/{channel_id}/messages?limit=100"
            resp = requests.get(url, headers=headers)
            if resp.status_code != 200:
                return f"Fehler beim Abrufen der Nachrichten: {resp.text}"
            
            messages = resp.json()
            if not messages:
                return "Keine Nachrichten im Kanal gefunden."
            
            filter_dt = None
            if start_date:
                import datetime
                try:
                    filter_dt = datetime.datetime.strptime(start_date.strip(), "%Y-%m-%d %H:%M:%S")
                except Exception as parse_err:
                    return f"Fehler beim Parsen des start_date '{start_date}': {str(parse_err)}"
            
            result = []
            for msg in reversed(messages):
                ts_str = msg["timestamp"]
                clean_ts_str = ts_str.split(".")[0].replace("T", " ")
                if "+" in clean_ts_str:
                    clean_ts_str = clean_ts_str.split("+")[0]
                
                try:
                    import datetime
                    msg_dt = datetime.datetime.strptime(clean_ts_str, "%Y-%m-%d %H:%M:%S")
                except Exception:
                    msg_dt = None
                
                if filter_dt and msg_dt and msg_dt < filter_dt:
                    continue
                
                author_name = msg["author"]["username"]
                content = msg["content"]
                result.append(f"[{clean_ts_str}] {author_name}: {content}")
            
            if not result:
                return "Keine Nachrichten nach dem angegebenen Datum im Kanal gefunden."
                
            return "\n".join(result)
        except Exception as e:
            return f"Fehler beim Abrufen der Nachrichten: {str(e)}"

class DiscordSendMessageTool(BaseTool):
    name: str = "Discord Nachricht senden"
    description: str = (
        "Sendet eine Textnachricht an einen spezifischen Discord-Kanal. "
        "Erfordert die channel_id und content (die eigentliche Nachricht)."
    )

    def _run(self, channel_id: str, content: str) -> str:
        if not DISCORD_TOKEN:
            return "Fehler: Kein DISCORD_TOKEN gefunden."
        
        channel_id = channel_id.replace("<#", "").replace(">", "").strip()
        
        headers = {
            "Authorization": f"Bot {DISCORD_TOKEN}",
            "Content-Type": "application/json"
        }
        payload = {"content": content}
        
        try:
            url = f"https://discord.com/api/v10/channels/{channel_id}/messages"
            resp = requests.post(url, headers=headers, json=payload)
            if resp.status_code == 200:
                return f"Erfolgreich: Nachricht an Kanal {channel_id} gesendet."
            else:
                return f"Fehler beim Senden der Nachricht: {resp.text}"
        except Exception as e:
            return f"Fehler beim Senden: {str(e)}"
