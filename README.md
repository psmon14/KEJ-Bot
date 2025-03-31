# KEJ-Bot

A simple Discord music bot written with Python.

Bot uses a YouTube cookie to bypass bot checks and to be able to play age restricted videos.

Bot supports slash commands and discords "Message Components" to control playback.

Bot can use youtube links, playlist youtube links, and also has a search function.

Bot is created primarly for private use, so don't bother reporting bugs.

# Installation

## Docker

In the same directory as your cookies.txt run

```bash
docker run --rm -it \
  -e DISCORD_TOKEN=your_discord_token \
  -v "cookies.txt:/app/cookies.txt" \
  ghcr.io/psmon14/kej-bot:main
```

Or use Docker-compose

```yaml
services:
  kej-bot:
    image: ghcr.io/psmon14/kej-bot:main
    restart: always
    environment:
      - DISCORD_TOKEN=your_discord_token
    volumes:
      - ./cookies.txt:/app/cookies.txt
```

## Manual

1.Install Python 3.11 or newer

2.Create a virtual environment

3.Install ffmpeg for your system

4.Install requirements from requirements.txt by using pip (pip install -r requirements.txt)

5.Add your discord bot token to the .env file (DISCORD_TOKEN=YOUR_TOKEN)

6.Export a youtube cookie into cookie.txt file in the same directory as the bot (always use a throwaway account because cookies will expire if you often use the account from which you took cookies)

7.Launch the main.py file
