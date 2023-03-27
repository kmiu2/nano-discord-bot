import asyncio
import datetime
import discord
import os
import re
from discord.ext import commands, tasks
from dotenv import load_dotenv

# Get tokens
load_dotenv()
TOKEN = os.getenv("DISCORD_TOKEN")

# Setup
intents = discord.Intents.default()
intents.message_content = True
bot = commands.Bot(command_prefix="$", intents=intents)

# Global Variables
irs_days = {}

# Commands
@bot.command(name="set_irs")
async def set_irs(ctx, *args):
    # Check if user is admin
    if not ctx.author.guild_permissions.administrator:
        await ctx.send("You do not have permission to use this command.")
        return

    error_string = 'Invalid date given, the format is "$set_irs <month> <day> <year>". For example, "$set_irs 5 31 2024"'
    # Check if arguments are given
    if len(args) != 3:
        await ctx.send(error_string)
        return

    # Check if date is valid
    try:
        global irs_days
        month = int(args[0])
        day = int(args[1])
        year = int(args[2])

        irs_days[ctx.guild.id] = datetime.datetime(year, month, day, 12, 0, 0)
        await ctx.send(f"IRS day set to {month}/{day}/{year} at 12:00 PM.")
    except ValueError:
        await ctx.send(error_string)


# Bot startup
@bot.event
async def on_ready():
    await bot.change_presence(
        activity=discord.Activity(
            type=discord.ActivityType.listening, name="geese honking"
        ),
    )

    for guild in bot.guilds:
        now = datetime.datetime.now()
        irs_days[guild.id] = datetime.datetime(2024, 2, 3, 12, 0, 0)
        print(f"{bot.user} is connected to {guild.name} (id: {guild.id}) at {now}")


# Error Logging
@bot.event
async def on_error(event, *args, **kwargs):
    with open("err.log", "a") as f:
        if event == "on_message":
            f.write(f"Unhandled message: {args[0]}\n")
        else:
            raise


# On message function
@bot.event
async def on_message(message):
    # Prevent bot from responding to itself
    if message.author == bot.user:
        return

    # Variables
    guild_id = message.guild.id
    channel_id = message.channel.id
    irs_day = irs_days[guild_id]
    msg = message.content.lower()
    today = datetime.datetime.now()
    days = (irs_day - today).days

    ### 2024 Gradcomm server, only show on irs channel, modlog
    if (
        guild_id == 1083515069444403240
        and channel_id != 1086067292623863880
        and channel_id != 1086073945184284734
    ):
        return

    if re.match(r"\birs\b.*\bdays\b|\bdays\b.*\birs\b", msg):
        await message.channel.send(
            f"There are {days} days until IRS! It's on {irs_day.strftime('%B %d, %Y')} at 12:00 PM."
        )

    ### Nano 24 server
    if message.guild.id == 622044737800503326:
        if msg in ["goose", "geese", "honk"]:
            await message.channel.send("<:mrgoose:631687927629611008>")
        if "choices" in msg:
            await message.channel.send("<:choices:971840335623901194>")

    # Since we overrode on_message, we need to call process_commands
    await bot.process_commands(message)


bot.run(TOKEN)
