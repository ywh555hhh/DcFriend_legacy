# diag_bot.py
import discord
from discord.ext import commands

print(f"discord version: {discord.__version__}")
print(f"Is discord.Bot directly available? {hasattr(discord, 'Bot')}")
print(f"Is discord.ext.commands.Bot available? {hasattr(commands, 'Bot')}")

print("\nAttempting to instantiate discord.Bot:")
bot_instance_discord_dot_bot = None
success_discord_dot_bot = False
intents_for_test = discord.Intents.default() # Intents are often required
try:
    # discord.Bot is an Application class, so it needs intents
    bot_instance_discord_dot_bot = discord.Bot(intents=intents_for_test)
    success_discord_dot_bot = True
    print(f"  Success: {success_discord_dot_bot}")
    print(f"  Type of bot_instance_discord_dot_bot: {type(bot_instance_discord_dot_bot)}")
except AttributeError as ae:
    print(f"  Failed with AttributeError: {ae} (This means discord.Bot is not found as a direct attribute)")
except Exception as e:
    print(f"  Failed with other Exception: {e}")


print("\nAttempting to instantiate discord.ext.commands.Bot:")
bot_instance_commands_dot_bot = None
success_commands_dot_bot = False
try:
    bot_instance_commands_dot_bot = commands.Bot(command_prefix=".", intents=intents_for_test)
    success_commands_dot_bot = True
    print(f"  Success: {success_commands_dot_bot}")
    print(f"  Type of bot_instance_commands_dot_bot: {type(bot_instance_commands_dot_bot)}")
except Exception as e:
    print(f"  Failed: {e}")

if success_discord_dot_bot and success_commands_dot_bot:
    print(f"\nIs discord.Bot an instance of commands.Bot? {isinstance(bot_instance_discord_dot_bot, commands.Bot)}")
    # In discord.py v2, discord.Bot IS a subclass of commands.Bot
    # So we should check if the class discord.Bot itself is a subclass of commands.Bot
    if hasattr(discord, 'Bot'): # Check again if the class itself exists
         print(f"Is the class discord.Bot a subclass of commands.Bot? {issubclass(discord.Bot, commands.Bot)}")