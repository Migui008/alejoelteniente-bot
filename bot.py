import os
import discord
from discord.ext import commands
from dotenv import load_dotenv
import aiohttp
import asyncio
from datetime import datetime, timezone

# Cargar variables de entorno
load_dotenv()
TOKEN = os.getenv("DISCORD_TOKEN")
TWITCH_CLIENT_ID = os.getenv("TWITCH_CLIENT_ID")
TWITCH_CLIENT_SECRET = os.getenv("TWITCH_CLIENT_SECRET")
TWITCH_USERNAME = os.getenv("TWITCH_USERNAME")

# Configurar intents
intents = discord.Intents.default()
intents.message_content = True  # Necesario para leer mensajes

# Estado global del canal y stream
current_channel_id = None
was_live = False
check_interval = 60  # Intervalo en segundos

# Función para obtener token de Twitch
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

# Comprobar si el canal está en directo
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
        return bool(data["data"])

# Bucle de comprobación de Twitch
async def check_twitch_loop():
    await bot.wait_until_ready()
    token = await get_twitch_token()
    headers = {
        "Client-ID": TWITCH_CLIENT_ID,
        "Authorization": f"Bearer {token}"
    }
    last_live = False

    while not bot.is_closed():
        async with aiohttp.ClientSession() as session:
            async with session.get(
                "https://api.twitch.tv/helix/streams",
                headers=headers,
                params={"user_login": TWITCH_USERNAME}
            ) as resp:
                data = await resp.json()
                stream = data.get("data", [])

                is_live = len(stream) > 0

                if is_live and not last_live:
                    # Entró en directo ahora
                    channel = bot.get_channel(current_channel_id)
                    if channel:
                        await channel.send(f"🔴 {TWITCH_USERNAME} está en directo ahora: https://twitch.tv/{TWITCH_USERNAME}")
                last_live = is_live

        await asyncio.sleep(60)  # comprueba cada 60 segundos


# Subclase personalizada para el bot con setup_hook
class TwitchBot(commands.Bot):
    async def setup_hook(self):
        self.loop.create_task(check_twitch_loop())

# Crear instancia del bot
bot = TwitchBot(command_prefix="&", intents=intents)

# Evento cuando el bot está listo
@bot.event
async def on_ready():
    print(f"✅ Bot conectado como {bot.user}")
    bot.loop.create_task(check_twitch_loop())  # 👈 Esto inicia el loop automático

# Comando para cambiar el canal de avisos
@bot.command(name="change_channel")
async def change_channel(ctx, channel: discord.TextChannel):
    global current_channel_id
    current_channel_id = channel.id
    await ctx.send(f"📢 Canal de avisos configurado a {channel.mention}")

@bot.command(name="twitch_status")
async def twitch_status(ctx):
    token = await get_twitch_token()
    url = "https://api.twitch.tv/helix/streams"
    headers = {
        "Client-ID": TWITCH_CLIENT_ID,
        "Authorization": f"Bearer {token}"
    }
    params = {
        "user_login": TWITCH_USERNAME
    }

    async with aiohttp.ClientSession() as session:
        async with session.get(url, headers=headers, params=params) as resp:
            data = await resp.json()
            stream_data = data.get("data", [])
            
            if stream_data:
                # Está en directo
                start_time = stream_data[0]["started_at"]
                # Calcular duración del directo
                from datetime import datetime, timezone

                started_dt = datetime.fromisoformat(start_time.replace('Z', '+00:00'))
                now_dt = datetime.now(timezone.utc)
                duration = now_dt - started_dt

                hours, remainder = divmod(int(duration.total_seconds()), 3600)
                minutes, seconds = divmod(remainder, 60)

                await ctx.send(f"✅ {TWITCH_USERNAME} está en directo desde hace {hours}h {minutes}m {seconds}s.\nhttps://twitch.tv/{TWITCH_USERNAME}")
            else:
                await ctx.send(f"❌ {TWITCH_USERNAME} no está en directo ahora mismo.")

@bot.command(name="status")
async def status(ctx):
    if current_channel_id:
        canal = bot.get_channel(current_channel_id)
        await ctx.send(f"📡 Canal actual de avisos: {canal.mention}")
    else:
        await ctx.send("❌ No hay canal configurado.")

# Iniciar el bot
bot.run(TOKEN)
