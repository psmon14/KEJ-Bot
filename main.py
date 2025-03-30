import discord
from discord.ext import commands
import sys
from pathlib import Path
import os

from dotenv import load_dotenv
load_dotenv() 

sys.path.append(str(Path(__file__).parent))

from commands import PlaybackCommands, QueueCommands, VoiceCommands
from messages import AUTO_DISCONNECT
from views import PlaybackControls

DISCORD_TOKEN = os.getenv("DISCORD_TOKEN")
if not DISCORD_TOKEN:
    raise ValueError("Please set the DISCORD_TOKEN environment variable.")

intents = discord.Intents.default()
intents.message_content = True
intents.voice_states = True

class Bot(commands.Bot):
    def __init__(self):
        super().__init__(
            command_prefix="!",
            intents=intents
        )
        self.persistent_views_added = False

    async def setup_hook(self):
        if not self.persistent_views_added:
            self.add_view(PlaybackControls())
            self.persistent_views_added = True

bot = Bot()

@bot.event
async def on_ready():
    print(f'Logged in as {bot.user} (ID: {bot.user.id})')
    await bot.add_cog(PlaybackCommands(bot))
    await bot.add_cog(QueueCommands(bot))
    await bot.add_cog(VoiceCommands(bot))
    await bot.tree.sync()
    print('Slash commands synced')

@bot.event
async def on_voice_state_update(member, before, after):
    if member.id == bot.user.id:
        return
        
    voice_client = discord.utils.get(bot.voice_clients, guild=member.guild)
    if voice_client and len(voice_client.channel.members) == 1:
        channel = voice_client.channel
        await voice_client.disconnect()
        
        playback_commands = bot.get_cog('PlaybackCommands')
        playback_commands.player.clear_queue(member.guild.id)
        
        summon_context = playback_commands.player.get_summon_context(member.guild.id)
        playback_commands.player.clear_summon_context(member.guild.id)
        
        try:
            if summon_context:
                await summon_context.followup.send(AUTO_DISCONNECT)
            else:
                await channel.send(AUTO_DISCONNECT)
        except Exception as e:
            print(f"Couldn't send disconnect message: {e}")

bot.run(DISCORD_TOKEN)