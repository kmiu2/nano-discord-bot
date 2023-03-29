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
tz = datetime.timezone(datetime.timedelta(hours=-5)) # UTC:-5 for Toronto Time
irs_dates_file = "irs_dates.json"

# Global Variables
irs_days = {}
bot_cooldown = {}
bot_cooldown_seconds = 60
irs_regex = re.compile(r"\birs\b.*\bdays\b|\bdays\b.*\birs\b")
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
        file = open(irs_dates_file, mode="w")
        file.write("{}")
        file.close()
    file = open(irs_dates_file, mode="r")
    times = json.load(file)
    for key in times:
        times[key] = datetime.datetime.fromtimestamp(times[key], tz=tz)
    return times


# Commands
@bot.command(name="set_irs", help="Set the IRS date for this server. Admin only.")
async def set_irs(ctx, *args):
    # Check if user is admin
    if not ctx.author.guild_permissions.administrator:
        await ctx.send("You do not have permission to use this command.")
        return

    error_string = 'Invalid date given, the format is "$set_irs YYYY/MM/DD [HH:MM:SS]". For example, "$set_irs 2024/05/31" or "$set_irs 2024/05/29 15:30:00. If time is not specified, it defaults to Noon (12:00:00). Timezone is EST (UTC:-5)"'

    command = " ".join(args)
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
        global irs_days
        irs_days[str(ctx.guild.id)] = datetime.datetime(
            year, month, day, hour, minute, second, tz=tz
        )
        write_irs_data(irs_days)
        irs_days = read_irs_data()
        await ctx.send(
            f"IRS time set to {irs_days[str(ctx.guild.id)].strftime('%A, %b %d, %Y @ %I:%M:%S %p')}"
        )
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
    global irs_days
    irs_days = read_irs_data()
    for guild in bot.guilds:
        now = datetime.datetime.now(tz=tz)
        if str(guild.id) not in irs_days:
            irs_days[str(guild.id)] = datetime.datetime(2024, 2, 3, 12, 0, 0, tz=tz)
        print(f"{bot.user} is connected to {guild.name} (id: {guild.id}) at {now}")

    write_irs_data(irs_days)


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

    ### 2024 Gradcomm server, only show on irs channel, modlog
    if (
        guild_id == 1083515069444403240
        and channel_id != 1086067292623863880
        and channel_id != 1086073945184284734
    ):
        return

    ### All server responses
    if bool(irs_regex.search(msg)) and await check_cooldown(user_id, message):
        irs_day = irs_days[str(guild_id)]
        now = datetime.datetime.now(tz=tz)
        minutes, seconds = divmod(round((irs_day - now).total_seconds()), 60)
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


### Bot Cooldown
async def check_cooldown(user_id, message):
    global bot_cooldown
    if user_id not in bot_cooldown:
        bot_cooldown[user_id] = {
            "time": datetime.datetime.now().timestamp(),
            "warned": False,
        }
        return True

    now = datetime.datetime.now().timestamp()
    user_time = bot_cooldown[user_id]["time"]

    if (now - user_time) < bot_cooldown_seconds:
        bot_cooldown[user_id]["time"] = datetime.datetime.now().timestamp()
        if not bot_cooldown[user_id]["warned"]:
            bot_cooldown[user_id]["warned"] = True
            await message.author.send("Woah there, take it easy. Dont spam me please.")
        await message.delete()
        return False
    bot_cooldown[user_id] = {
        "time": datetime.datetime.now().timestamp(),
        "warned": False,
    }
    return True


bot.run(TOKEN)
