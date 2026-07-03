import discord
from discord.ext import commands
import os
from dotenv import load_dotenv

# Umgebungsvariablen laden
load_dotenv()
DISCORD_TOKEN = os.getenv("DISCORD_TOKEN")

# Intents konfigurieren
intents = discord.Intents.default()
intents.message_content = True
intents.messages = True
bot = commands.Bot(command_prefix="!", intents=intents)

@bot.event
async def on_ready():
    print(f"Eingeloggt als {bot.user.name} zum Bereinigen der DMs...")
    try:
        app_info = await bot.application_info()
        owner = app_info.owner
        if owner:
            # DM-Kanal abrufen/erstellen
            dm_channel = owner.dm_channel
            if dm_channel is None:
                dm_channel = await owner.create_dm()
            
            print(f"Lösche eigene Nachrichten im Chat mit {owner.name}...")
            deleted_count = 0
            
            # Durch die letzten 100 Nachrichten gehen und eigene löschen
            async for message in dm_channel.history(limit=100):
                if message.author == bot.user:
                    await message.delete()
                    deleted_count += 1
            
            print(f"Erfolgreich {deleted_count} eigene Nachrichten gelöscht!")
            
            # Frische Begrüßung senden
            await owner.send(
                "Hallo! Ich bin jetzt online und bereit, Befehle in `C:\\Users\\iboer` entgegenzunehmen. "
                "Was kann ich heute für dich tun?"
            )
            print("Neue Begrüßungs-DM gesendet.")
            
    except Exception as e:
        print(f"Fehler beim Bereinigen der DMs: {e}")
    finally:
        # Script beenden
        await bot.close()

if __name__ == "__main__":
    if not DISCORD_TOKEN:
        print("Kein DISCORD_TOKEN gefunden!")
    else:
        bot.run(DISCORD_TOKEN)
