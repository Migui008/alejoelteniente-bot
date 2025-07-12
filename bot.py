import os
import json
from dotenv import load_dotenv
import discord
import asyncio
from twitchAPI.twitch import Twitch

# Cargar variables de entorno
load_dotenv()

DISCORD_TOKEN = os.getenv('DISCORD_TOKEN')
TWITCH_CLIENT_ID = os.getenv('TWITCH_CLIENT_ID')
TWITCH_CLIENT_SECRET = os.getenv('TWITCH_CLIENT_SECRET')
TWITCH_USERNAME = os.getenv('TWITCH_USERNAME')

intents = discord.Intents.default()
intents.message_content = True  # Necesario para leer mensajes
client = discord.Client(intents=intents)

# Archivo donde guardamos la configuración de canales por servidor
CONFIG_FILE = 'canales.json'

def cargar_config():
    try:
        with open(CONFIG_FILE, 'r') as f:
            return json.load(f)
    except FileNotFoundError:
        return {}

def guardar_config(config):
    with open(CONFIG_FILE, 'w') as f:
        json.dump(config, f, indent=4)

config = cargar_config()

was_live = False

async def check_stream():
    global was_live
    twitch = await Twitch(TWITCH_CLIENT_ID, TWITCH_CLIENT_SECRET)
    user_data = await twitch.get_users(logins=[TWITCH_USERNAME])
    user_id = user_data['data'][0]['id']

    while True:
        stream = await twitch.get_streams(user_id=[user_id])

        if stream['data']:
            if not was_live:
                stream_title = stream['data'][0]['title']
                url = f'https://twitch.tv/{TWITCH_USERNAME}'

                for guild in client.guilds:
                    guild_id_str = str(guild.id)
                    if guild_id_str in config:
                        channel_id = config[guild_id_str]
                        channel = client.get_channel(channel_id)
                        if channel:
                            await channel.send(f'🎥 **{TWITCH_USERNAME}** está EN DIRECTO!\n**{stream_title}**\n🔴 {url}')

                was_live = True
        else:
            was_live = False

        await asyncio.sleep(60)

@client.event
async def on_ready():
    print(f'✅ Bot conectado como {client.user}')
    client.loop.create_task(check_stream())

@client.event
async def on_message(message):
    if message.author == client.user:
        return

    if message.content.startswith('&change_channel'):
        # Solo admins pueden usar el comando
        if not message.author.guild_permissions.administrator:
            await message.channel.send('❌ Solo administradores pueden usar este comando.')
            return

        # Guardamos el canal actual para el servidor
        guild_id_str = str(message.guild.id)
        channel_id = message.channel.id

        config[guild_id_str] = channel_id
        guardar_config(config)

        await message.channel.send(f'✅ Canal configurado correctamente para avisos en este servidor: {message.channel.mention}')

client.run(DISCORD_TOKEN)
