import discord
from messages import *

class SearchSelectView(discord.ui.View):
    def __init__(self, entries, requester, player):
        super().__init__(timeout=30.0)
        self.entries = entries
        self.requester = requester
        self.player = player
        
        for i in range(1, 6):
            if i <= len(entries):
                self.add_item(SearchButton(i, entries[i-1], requester, player))
            else:
                self.add_item(SearchButton(i, None, requester, player, disabled=True))

class SearchButton(discord.ui.Button):
    def __init__(self, number, entry, requester, player, disabled=False):
        super().__init__(
            label=str(number),
            style=discord.ButtonStyle.primary,
            disabled=disabled
        )
        self.entry = entry
        self.requester = requester
        self.player = player

    async def callback(self, interaction: discord.Interaction):
        if not self.entry:
            await interaction.response.send_message(SEARCH_SELECTION_NOT_AVAILABLE, ephemeral=True)
            return
            
        guild_id = interaction.guild.id
        if guild_id not in self.player.queues:
            self.player.queues[guild_id] = []
            
        self.player.queues[guild_id].append({
            'title': self.entry.get('title', 'Unknown Title'),
            'url': self.entry.get('url') or self.entry.get('webpage_url', ''),
            'requester': self.requester
        })
        
        await interaction.response.send_message(
            QUEUE_ADDED_SONG.format(title=self.entry.get('title', 'Unknown Title')),
            ephemeral=True
        )
        
        voice_client = interaction.guild.voice_client
        if voice_client and not voice_client.is_playing():
            await self.player.play_next(interaction)
        
        for item in self.view.children:
            item.disabled = True
        await interaction.message.edit(view=self.view)

class PlaybackControls(discord.ui.View):
    def __init__(self):
        super().__init__(timeout=None)

    @discord.ui.button(
        emoji="⏸️",
        style=discord.ButtonStyle.secondary,
        custom_id="persistent:pause"
    )
    async def pause_button(self, interaction: discord.Interaction, button: discord.ui.Button):
        voice_client = interaction.guild.voice_client
        if voice_client and voice_client.is_playing():
            voice_client.pause()
            await interaction.response.send_message(PLAYBACK_PAUSED, ephemeral=True)
        else:
            await interaction.response.send_message(NOTHING_PLAYING, ephemeral=True)

    @discord.ui.button(
        emoji="▶️", 
        style=discord.ButtonStyle.secondary,
        custom_id="persistent:resume"
    )
    async def resume_button(self, interaction: discord.Interaction, button: discord.ui.Button):
        voice_client = interaction.guild.voice_client
        if voice_client and voice_client.is_paused():
            voice_client.resume()
            await interaction.response.send_message(PLAYBACK_RESUMED, ephemeral=True)
        else:
            await interaction.response.send_message(NOT_PAUSED, ephemeral=True)

    @discord.ui.button(
        emoji="⏭️",
        style=discord.ButtonStyle.secondary,
        custom_id="persistent:skip"
    )
    async def skip_button(self, interaction: discord.Interaction, button: discord.ui.Button):
        player = interaction.client.get_cog('PlaybackCommands').player
        guild_id = interaction.guild.id

        if player.loop_song.get(guild_id, False):
            player.loop_song[guild_id] = False
            await interaction.response.send_message(PLAYBACK_LOOP_SKIPPED)
        else:
            await interaction.response.send_message(PLAYBACK_SKIPPED, ephemeral=True)

        voice_client = interaction.guild.voice_client
        if voice_client and voice_client.is_playing():
            voice_client.stop()
        else:
            await interaction.response.send_message(NOTHING_PLAYING, ephemeral=True)

    @discord.ui.button(
        emoji="🔁",
        style=discord.ButtonStyle.secondary,
        custom_id="persistent:loop_song"
    )
    async def loop_song_button(self, interaction: discord.Interaction, button: discord.ui.Button):
        player = interaction.client.get_cog('PlaybackCommands').player
        is_looping = player.toggle_loop_song(interaction.guild.id)
        message = LOOP_SONG_ENABLED if is_looping else LOOP_SONG_DISABLED
        await interaction.response.send_message(message)