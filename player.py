import asyncio
import discord
from ytdl_source import YTDLSource
from messages import *
from views import PlaybackControls

class MusicPlayer:
    def __init__(self, bot):
        self.bot = bot
        self.queues = {}
        self.current = {}
        self.loop_song = {}
        self.loop_queue = {}
        self.summon_context = {}

    def set_summon_context(self, guild_id, interaction):
        self.summon_context[guild_id] = interaction

    def get_summon_context(self, guild_id):
        return self.summon_context.get(guild_id)

    def clear_summon_context(self, guild_id):
        if guild_id in self.summon_context:
            del self.summon_context[guild_id]

    def toggle_loop_song(self, guild_id):
        self.loop_song[guild_id] = not self.loop_song.get(guild_id, False)
        return self.loop_song[guild_id]

    def toggle_loop_queue(self, guild_id):
        self.loop_queue[guild_id] = not self.loop_queue.get(guild_id, False)
        return self.loop_queue[guild_id]

    def get_queue(self, guild_id):
        return self.queues.get(guild_id, [])

    def get_current(self, guild_id):
        return self.current.get(guild_id)

    def clear_queue(self, guild_id):
        self.queues[guild_id] = []
        self.current[guild_id] = None

    async def add_to_queue(self, interaction: discord.Interaction, query: str):
        guild_id = interaction.guild.id
        if guild_id not in self.queues:
            self.queues[guild_id] = []

        async with interaction.channel.typing():
            data = await YTDLSource.get_info(query)
            
            if 'entries' in data:
                for entry in data['entries']:
                    if entry:
                        self.queues[guild_id].append({
                            'title': entry.get('title', 'Unknown Title'),
                            'url': entry.get('url') or entry.get('webpage_url', ''),
                            'requester': interaction.user
                        })
                await interaction.followup.send(QUEUE_ADDED_PLAYLIST.format(count=len(data['entries'])))
            else:
                self.queues[guild_id].append({
                    'title': data.get('title', 'Unknown Title'),
                    'url': data.get('url') or data.get('webpage_url', ''),
                    'requester': interaction.user
                })
                await interaction.followup.send(QUEUE_ADDED_SONG.format(title=data.get('title', 'Unknown Title')))

        voice_client = interaction.guild.voice_client
        if voice_client and not voice_client.is_playing():
            await self.play_next(interaction)

    async def play_next(self, interaction: discord.Interaction):
        guild_id = interaction.guild.id
        voice_client = interaction.guild.voice_client

        if not voice_client or not voice_client.is_connected():
            return

        if guild_id in self.current and self.loop_song.get(guild_id, False):
            song = self.current[guild_id]
            source = await YTDLSource.from_url(song['url'], stream=True)
            voice_client.play(
                source,
                after=lambda e: asyncio.run_coroutine_threadsafe(
                    self.play_next(interaction), self.bot.loop
                ).result()
            )
            return

        if guild_id in self.queues and self.queues[guild_id]:
            if self.loop_queue.get(guild_id, False):
                if guild_id in self.current:
                    self.queues[guild_id].append(self.current[guild_id])

            self.current[guild_id] = self.queues[guild_id].pop(0)
            try:
                source = await YTDLSource.from_url(self.current[guild_id]['url'], stream=True)
                voice_client.play(
                    source,
                    after=lambda e: asyncio.run_coroutine_threadsafe(
                        self.play_next(interaction), self.bot.loop
                    ).result()
                )
                embed = discord.Embed(
                    title=QUEUE_NEXT_SONG,
                    description=f"[{self.current[guild_id]['title']}]({self.current[guild_id]['url']})",
                    color=discord.Color.blue()
                )
                embed.set_footer(text=SONG_REQUESTED_BY.format(user=self.current[guild_id]['requester'].display_name))
                await interaction.followup.send(embed=embed, view=PlaybackControls())
            except Exception as e:
                print(f"Error playing song: {e}")
                await interaction.followup.send(REQUEST_FAILED.format(error=str(e)))
                await self.play_next(interaction)
        else:
            self.current[guild_id] = None
            await interaction.followup.send(QUEUE_EMPTY)