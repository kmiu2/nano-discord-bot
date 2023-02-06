import os
import datetime
import discord
from dotenv import load_dotenv

# Get tokens
load_dotenv()
TOKEN = os.getenv("DISCORD_TOKEN")

# Intents
intents = discord.Intents.default()
intents.message_content = True
client = discord.Client(intents=intents)


# Not required, for logging purposes
@client.event
async def on_ready():
    for guild in client.guilds:
        now = datetime.datetime.now()
        print(f"{client.user} is connected to {guild.name} (id: {guild.id}) at {now}")


# Error Logging
@client.event
async def on_error(event, *args, **kwargs):
    with open("err.log", "a") as f:
        if event == "on_message":
            f.write(f"Unhandled message: {args[0]}\n")
        else:
            raise


# On message function
@client.event
async def on_message(message):
    # Prevent bot from responding to itself
    if message.author == client.user:
        return

    # Variables
    msg = message.content.lower()
    today = datetime.date.today()
    irs_day = datetime.date(2024, 2, 3)
    days = str(irs_day - today).split(" ")[0]

    # Message responses
    if "days" in msg and "irs" in msg:
        await message.channel.send(f"There are {days} days until IRS!")

    if "choices" in msg:
        await message.channel.send("<:choices:971840335623901194>")


client.run(TOKEN)
