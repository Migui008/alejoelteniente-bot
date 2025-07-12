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
import aiohttp
import asyncio

was_live = False  # Estado anterior
check_interval = 60  # segundos

async def get_twitch_token():
    url = "https://id.twitch.tv/oauth2/token"
    params = {
        "client_id": TWITCH_CLIENT_ID,
        "client_secret": TWITCH_CLIENT_SECRET,
        "grant_type": "client_credentials"
    }

    async with aiohttp.ClientSession() as session:
        async with session.post(url, params=params) as resp:
            data = await resp.json()
            return data["access_token"]

async def is_stream_live(session, token):
    url = "https://api.twitch.tv/helix/streams"
    headers = {
        "Client-ID": TWITCH_CLIENT_ID,
        "Authorization": f"Bearer {token}"
    }
    params = {
        "user_login": TWITCH_USERNAME
    }

    async with session.get(url, headers=headers, params=params) as resp:
        data = await resp.json()
        return bool(data["data"])  # True si está en directo

async def check_twitch_loop():
    global was_live

    token = await get_twitch_token()
    await bot.wait_until_ready()
    
    async with aiohttp.ClientSession() as session:
        while not bot.is_closed():
            try:
                is_live = await is_stream_live(session, token)
                if is_live and not was_live:
                    # Solo anuncia cuando pasa de offline a online
                    if current_channel_id:
                        channel = bot.get_channel(current_channel_id)
                        if channel:
                            await channel.send(f"🎥 ¡{TWITCH_USERNAME} acaba de empezar directo en https://twitch.tv/{TWITCH_USERNAME}!")
                    was_live = True
                elif not is_live and was_live:
                    was_live = False
                await asyncio.sleep(check_interval)
            except Exception as e:
                print(f"Error al comprobar Twitch: {e}")
                await asyncio.sleep(check_interval)

bot.loop.create_task(check_twitch_loop())
bot.run(TOKEN)
