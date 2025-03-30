import discord
import yt_dlp
import asyncio
from config import YTDL_OPTIONS, FFMPEG_OPTIONS

ytdl = yt_dlp.YoutubeDL(YTDL_OPTIONS)

class YTDLSource(discord.PCMVolumeTransformer):
    def __init__(self, source, *, data, volume=0.5):
        super().__init__(source, volume)
        self.data = data
        self.title = data.get('title')
        self.url = data.get('url')
        self.duration = data.get('duration')
        self.original = source

    @classmethod
    async def from_url(cls, url, *, loop=None, stream=False):
        loop = loop or asyncio.get_event_loop()
        data = await loop.run_in_executor(None, lambda: ytdl.extract_info(url, download=not stream))
        if 'entries' in data:
            data = data['entries'][0]
        
        filename = data['url'] if stream else ytdl.prepare_filename(data)
        
        ffmpeg_opts = FFMPEG_OPTIONS.copy()
        if 'preferredcodec' in ffmpeg_opts.get('options', ''):
            ffmpeg_opts['options'] = ffmpeg_opts['options'].replace('-preferredcodec opus', '')
        
        return cls(discord.FFmpegPCMAudio(filename, **ffmpeg_opts), data=data)

    @classmethod
    async def get_info(cls, url):
        loop = asyncio.get_event_loop()
        return await loop.run_in_executor(None, lambda: ytdl.extract_info(url, download=False))