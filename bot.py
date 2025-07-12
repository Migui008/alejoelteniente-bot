import os
from dotenv import load_dotenv
import discord
from discord.ext import commands

# Carga variables del .env
load_dotenv()
TOKEN = os.getenv("DISCORD_TOKEN")
TWITCH_CLIENT_ID = os.getenv("TWITCH_CLIENT_ID")
TWITCH_CLIENT_SECRET = os.getenv("TWITCH_CLIENT_SECRET")
TWITCH_USERNAME = os.getenv("TWITCH_USERNAME")

# Configura los intents
intents = discord.Intents.default()
intents.message_content = True  # Para poder leer mensajes

bot = commands.Bot(command_prefix="&", intents=intents)

@bot.event
async def on_ready():
    print(f"Bot conectado como {bot.user}")

# Comando para cambiar canal Twitch donde se informa (ejemplo)
current_channel_id = None

@bot.command(name="change_channel")
async def change_channel(ctx, channel: discord.TextChannel):
    global current_channel_id
    current_channel_id = channel.id
    await ctx.send(f"Canal cambiado a {channel.mention}")

# Aquí pondrías la lógica para Twitch y avisar cuando empiece directo

bot.run(TOKEN)
