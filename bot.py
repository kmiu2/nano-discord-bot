import os
import re
import json
import asyncio
import datetime

import discord
from discord.ext import commands
from dotenv import load_dotenv

# Get tokens
load_dotenv()
TOKEN = os.getenv("DISCORD_TOKEN")

# Setup
intents = discord.Intents.default()
intents.message_content = True
bot = commands.Bot(command_prefix="$", intents=intents)
irs_dates_file = 'irs_dates.json'

# Global Variables
irs_days = {}
bot_cooldown = {}
bot_cooldown_seconds = 60
irs_regex =  re.compile(r"\birs\b.*\bdays\b|\bdays\b.*\birs\b")
set_irs_regex = re.compile(r"(\d{4})/(\d{2})/(\d{2})( (\d{2}):(\d{2}):(\d{2}))?")

def write_irs_data(times):
    # Write unix timestamps to file with guild IDs
    file = open(irs_dates_file, mode="w")
    stamps = {}
    for key in times:
        stamps[key] = times[key].timestamp()
    json.dump(stamps, file, indent=4)

def read_irs_data():
    # Read unix timestamps from file with guild IDs
    if not os.path.isfile(irs_dates_file):
        return {}
    file = open(irs_dates_file, mode="r")
    times = json.load(file)
    for key in times:
        times[key] = datetime.datetime.fromtimestamp(times[key])
    return times

# Commands
async def set_irs(ctx, *args):
    # Check if user is admin
    if not ctx.author.guild_permissions.administrator:
        await ctx.send("You do not have permission to use this command.")
        return
    
    error_string = f'Invalid date given, the format is "${set_irs.__name__} YYYY/MM/DD [HH:MM:SS]".\
                     For example, "${set_irs.__name__} 2024/05/31" or "${set_irs.__name__} 2024/05/29 15:30:00.\
                     If time is not specified, it defaults to Noon (12:00:00)"'
    
    command = ' '.join(args)
    match = set_irs_regex.fullmatch(command)
    try:
        # Check for regex match
        if not match:
            raise ValueError("Invalid date format")
        # Collect values
        year = int(match.group(1))
        month = int(match.group(2))
        day = int(match.group(3))
        if match.group(4):
            hour = int(match.group(5))
            minute = int(match.group(6))
            second = int(match.group(7))
        else:
            hour = 12
            minute = 0
            second = 0
        # Set the datetime
        irs_days[ctx.guild.id] = datetime.datetime(year, month, day, hour, minute, second)
        write_irs_data(irs_days)
        irs_days = read_irs_data()
        await ctx.send(f"IRS time set to {irs_days[ctx.guild.id].strftime('%A, %b %d, %Y @ %I:%M%S %p')}")
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
    # Opening JSON file
    irs_days = read_irs_data()
    for guild in bot.guilds:
        now = datetime.datetime.now()
        if not irs_days[guild.id]:
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
    user_id = message.author.id
    msg = message.content.lower()

    ### Bot Cooldown
    try:
        if (datetime.datetime.now().timestamp - bot_cooldown[user_id]) < bot_cooldown_seconds:
            bot_cooldown[user_id] = datetime.datetime.now().timestamp
            await message.author.send("Woah there, take it easy. Dont spam me please.")
            return
    except:
        continue
    finally:
        bot_cooldown[user_id] = datetime.datetime.now().timestamp

    ### 2024 Gradcomm server, only show on irs channel, modlog
    if (
        guild_id == 1083515069444403240
        and channel_id != 1086067292623863880
        and channel_id != 1086073945184284734
    ):
        return
    
    ### All server responses
    if irs_regex.search(msg):
        irs_day = irs_days[guild_id]
        now = datetime.now()
        minutes, seconds = divmod(round((irs_day-now).total_seconds()), 60)
        hours, minutes = divmod(minutes, 60)
        days, hours = divmod(hours, 24)

        await message.channel.send(
            f"There are {days} days, {hours} hours, {minutes} minutes, and {seconds} seconds until IRS! It's on {irs_day.strftime('%B %d, %Y @ %I:%M:%S %p')}."
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
