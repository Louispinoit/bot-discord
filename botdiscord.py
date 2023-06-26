import discord
import os
import asyncio
import youtube_dl
from discord.ext import commands

# Discord bot Initialization
intents = discord.Intents.default()
intents.message_content = True  # Activer l'intent de contenu de message
bot = commands.Bot(command_prefix ='!', intents = discord.Intents.all())
key = "MTEyMjg3OTg0NDQxMDIxMjQ0NQ.GeWhKk.7RrvKPxNPUlouWQ3ZpMAuupnSr7Ep_IiPwDYjw"

voice_clients = {}
playlists = {}

yt_dl_opts = {'format': 'bestaudio/best'}
ytdl = youtube_dl.YoutubeDL(yt_dl_opts)

ffmpeg_options = {'options': "-vn"}


@bot.event
async def on_ready():
    print(f"{bot.user} est maintenant connecté Lilian")


class Menu(discord.ui.View):
    def __init__(self, voice_clients):
        super().__init__()
        self.voice_clients = voice_clients

    @discord.ui.button(label="Pause", style=discord.ButtonStyle.grey)
    async def pause_button(self, button: discord.ui.Button, interaction: discord.Interaction):
        try:
            guild_id = interaction.guild.id
            if guild_id in self.voice_clients:
                self.voice_clients[guild_id].pause()
                await interaction.response.send_message("La musique a été mise en pause.")
            else:
                await interaction.response.send_message("Aucune musique n'est actuellement en cours de lecture.")
        except Exception as e:
            print(f"Erreur lors de la gestion de l'interaction : {e}")



@bot.command()
async def menu(ctx):
    view = Menu(voice_clients)
    await ctx.send(view=view)


@bot.event
async def on_message(msg):
    if msg.content.startswith("!play"):

        try:
            voice_client = await msg.author.voice.channel.connect()
            voice_clients[voice_client.guild.id] = voice_client
        except Exception as err:
            print(err)

        try:
            url = msg.content.split()[1]

            # Create the playlist if it does not exist
            if msg.guild.id not in playlists:
                playlists[msg.guild.id] = []

            # Add the song to the playlist
            playlists[msg.guild.id].append(url)

            # If not already playing a song, start playing
            if not voice_clients[msg.guild.id].is_playing():
                await play_next_song(msg.guild.id)

        except Exception as err:
            print(err)
    if msg.content.startswith("!pause"):
        try:
            voice_clients[msg.guild.id].pause()
        except Exception as err:
            print(err)

    if msg.content.startswith("!resume"):
        try:
            voice_clients[msg.guild.id].resume()
        except Exception as err:
            print(err)

    if msg.content.startswith("!skip"):
        try:
            voice_clients[msg.guild.id].stop()
        except Exception as err:
            print(err)

    if msg.content.startswith("!q"):
        try:
            queue_length = len(playlists[msg.guild.id])
            await msg.channel.send(f"Il y a {queue_length} chanson(s) dans la file d'attente.")
        except Exception as err:
            print(err)

    if msg.content.startswith("!stop"):
        try:
            voice_clients[msg.guild.id].stop()
            await voice_clients[msg.guild.id].disconnect()
            del playlists[msg.guild.id]
        except Exception as err:
            print(err)
    await bot.process_commands(msg)


async def play_next_song(guild_id):
    try:
        url = playlists[guild_id].pop(0)

        loop = asyncio.get_event_loop()
        data = await loop.run_in_executor(None, lambda: ytdl.extract_info(url, download=False))

        song = data['url']
        player = discord.FFmpegPCMAudio(song, **ffmpeg_options)

        def after_playing(err):
            # If an error occurred while playing, print it
            if err is not None:
                print(err)

            # If there are more songs in the playlist, continue playing
            if playlists[guild_id]:
                asyncio.run_coroutine_threadsafe(play_next_song(guild_id), loop)
            else:
                asyncio.run_coroutine_threadsafe(voice_clients[guild_id].disconnect(), loop)

        voice_clients[guild_id].play(player, after=after_playing)

    except Exception as err:
        print(err)


bot.run(key)
