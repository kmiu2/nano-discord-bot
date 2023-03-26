# Nano Discord Bot

See it live in the Nano 2024 Discord Server!

## Discord Developer Portal

https://discord.com/developers/applications

## Hosting Details

Hosted on a GCP VM with the following details:

- `us-central1-a`
- `N1`
- `f1-micro`

# tmux

Use tmux to run the bot and after disconnecting

```bash
tmux new -s nanobot
python3 bot.py
```

Then `Ctrl-a Ctr-d` to detach. To reconnect

```bash
tmux attach -t nanobot
```

## Discord Py

To get emoji id, type `\:YourEmoji:` in the respective server.

Full documentation here: https://discordpy.readthedocs.io/en/stable/index.html
