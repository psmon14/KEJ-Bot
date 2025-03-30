import discord
from discord import app_commands
from discord.ext import commands
from player import MusicPlayer
from messages import *
from ytdl_source import YTDLSource
from views import SearchSelectView, PlaybackControls

class PlaybackCommands(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.player = MusicPlayer(bot)

    @app_commands.command(name="play", description=CMD_PLAY)
    @app_commands.describe(query=CMD_PLAY_QUERY)
    async def play(self, interaction: discord.Interaction, query: str):
        if not interaction.user.voice:
            await interaction.response.send_message(VOICE_NOT_CONNECTED, ephemeral=True)
            return

        voice_client = interaction.guild.voice_client
        if not voice_client:
            try:
                voice_client = await interaction.user.voice.channel.connect()
            except Exception as e:
                await interaction.response.send_message(VOICE_JOIN_FAILED.format(error=e), ephemeral=True)
                return

        if query.startswith(('http://', 'https://')):
            await interaction.response.defer()
            await self.player.add_to_queue(interaction, query)
            return

        await interaction.response.defer()
        
        search_query = f"ytsearch5:{query}"
        data = await YTDLSource.get_info(search_query)
        
        if not data or not data.get('entries'):
            await interaction.followup.send(NO_RESULTS)
            return
            
        entries = data['entries'][:5]
        
        embed = discord.Embed(
            title=SEARCH_TITLE.format(query=query),
            color=discord.Color.gold()
        )
        
        for i, entry in enumerate(entries, 1):
            duration = entry.get('duration', 0)
            hours, remainder = divmod(int(duration), 3600)
            minutes, seconds = divmod(remainder, 60)
            if hours > 0:
                duration_str = f"{hours}:{minutes:02}:{seconds:02}"
            else:
                duration_str = f"{minutes}:{seconds:02}"
            embed.add_field(
                name=f"{i}. {entry.get('title', 'Unknown Title')}",
                value=SONG_DURATION.format(duration=duration_str),
                inline=False
            )
        view = SearchSelectView(entries, interaction.user, self.player)
        await interaction.followup.send(embed=embed, view=view)

    @app_commands.command(name="skip", description=CMD_SKIP)
    async def skip(self, interaction: discord.Interaction):
        guild_id = interaction.guild.id
        if self.player.loop_song.get(guild_id, False):
            self.player.loop_song[guild_id] = False
            await interaction.response.send_message(PLAYBACK_LOOP_SKIPPED)
        else:
            await interaction.response.send_message(PLAYBACK_SKIPPED)

        voice_client = interaction.guild.voice_client
        if voice_client and voice_client.is_playing():
            voice_client.stop()
        else:
            await interaction.response.send_message(NOTHING_PLAYING, ephemeral=True)

    @app_commands.command(name="stop", description=CMD_STOP)
    async def stop(self, interaction: discord.Interaction):
        voice_client = interaction.guild.voice_client
        if voice_client:
            if voice_client.is_playing():
                voice_client.stop()
            self.player.clear_queue(interaction.guild.id)
            await interaction.response.send_message(PLAYBACK_STOPPED)
        else:
            await interaction.response.send_message(BOT_NOT_CONNECTED, ephemeral=True)

    @app_commands.command(name="pause", description=CMD_PAUSE)
    async def pause(self, interaction: discord.Interaction):
        voice_client = interaction.guild.voice_client
        if voice_client and voice_client.is_playing():
            voice_client.pause()
            await interaction.response.send_message(PLAYBACK_PAUSED)
        else:
            await interaction.response.send_message(NOTHING_PLAYING, ephemeral=True)

    @app_commands.command(name="resume", description=CMD_RESUME)
    async def resume(self, interaction: discord.Interaction):
        voice_client = interaction.guild.voice_client
        if voice_client and voice_client.is_paused():
            voice_client.resume()
            await interaction.response.send_message(PLAYBACK_RESUMED)
        else:
            await interaction.response.send_message(NOT_PAUSED, ephemeral=True)

    @app_commands.command(name="loopsong", description=CMD_LOOPSONG)
    async def loopsong(self, interaction: discord.Interaction):
        is_looping = self.player.toggle_loop_song(interaction.guild.id)
        message = LOOP_SONG_ENABLED if is_looping else LOOP_SONG_DISABLED
        await interaction.response.send_message(message)

    @app_commands.command(name="loopqueue", description=CMD_LOOPQUEUE)
    async def loopqueue(self, interaction: discord.Interaction):
        is_looping = self.player.toggle_loop_queue(interaction.guild.id)
        message = LOOP_QUEUE_ENABLED if is_looping else LOOP_QUEUE_DISABLED
        await interaction.response.send_message(message)


class QueueCommands(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @app_commands.command(name="queue", description=CMD_QUEUE)
    async def show_queue(self, interaction: discord.Interaction):
        queue = self.bot.get_cog('PlaybackCommands').player.get_queue(interaction.guild.id)
        if not queue:
            await interaction.response.send_message(QUEUE_EMPTY)
            return
        
        embed = discord.Embed(title=CMD_QUEUE, color=discord.Color.green())
        current = self.bot.get_cog('PlaybackCommands').player.get_current(interaction.guild.id)
        
        if current:
            embed.add_field(name=QUEUE_NEXT_SONG, value=f"[{current['title']}]({current['url']})", inline=False)
        
        for i, song in enumerate(queue[:10], 1):
            embed.add_field(
                name=f"{i}. {song['title']}",
                value=SONG_REQUESTED_BY.format(user=song['requester'].display_name),
                inline=False
            )
        
        if len(queue) > 10:
            embed.set_footer(text=f"+{len(queue)-10} more songs")
        
        await interaction.response.send_message(embed=embed)

    @app_commands.command(name="nowplaying", description=CMD_NOWPLAYING)
    async def now_playing(self, interaction: discord.Interaction):
        current = self.bot.get_cog('PlaybackCommands').player.get_current(interaction.guild.id)
        if not current:
            await interaction.response.send_message(NOTHING_PLAYING, ephemeral=True)
            return
        
        embed = discord.Embed(
            title=QUEUE_NEXT_SONG,
            description=f"[{current['title']}]({current['url']})",
            color=discord.Color.blue()
        )
        embed.set_footer(text=SONG_REQUESTED_BY.format(user=current['requester'].display_name))
        
        view = PlaybackControls()
        await interaction.response.send_message(embed=embed, view=view)

    @app_commands.command(name="clear", description=CMD_CLEAR)
    async def clear_queue(self, interaction: discord.Interaction):
        self.bot.get_cog('PlaybackCommands').player.clear_queue(interaction.guild.id)
        await interaction.response.send_message(QUEUE_CLEARED)

class VoiceCommands(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @app_commands.command(name="join", description=CMD_JOIN)
    async def join(self, interaction: discord.Interaction):
        if not interaction.user.voice:
            await interaction.response.send_message(VOICE_NOT_CONNECTED, ephemeral=True)
            return
        
        channel = interaction.user.voice.channel
        try:
            await channel.connect()
            await interaction.response.send_message(VOICE_JOIN_SUCCESS.format(channel=channel.name))
        except Exception as e:
            await interaction.response.send_message(VOICE_JOIN_FAILED.format(error=e), ephemeral=True)

    @app_commands.command(name="leave", description=CMD_LEAVE)
    async def leave(self, interaction: discord.Interaction):
        voice_client = interaction.guild.voice_client
        if voice_client and voice_client.is_connected():
            await voice_client.disconnect()
            await interaction.response.send_message(VOICE_LEAVE_SUCCESS)
        else:
            await interaction.response.send_message(BOT_NOT_CONNECTED, ephemeral=True)