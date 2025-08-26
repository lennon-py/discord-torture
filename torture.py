import discord
from discord.ext import commands, tasks
import os
import json
import re
import asyncio
from datetime import datetime, timedelta

# this used to be called "scene kid mode"
# but i eventually scrapped it for "torture"
# because this is just about torture on anybody you use it on

SCENE_DIR = r #put your directory of where you want json data to be stored :0
os.makedirs(SCENE_DIR, exist_ok=True)

def load_scene_data(guild_id: int):
    path = os.path.join(SCENE_DIR, f"{guild_id}.json")
    if not os.path.exists(path):
        return {}
    with open(path, "r", encoding="utf-8") as f:
        return json.load(f)

def save_scene_data(guild_id: int, data: dict):
    path = os.path.join(SCENE_DIR, f"{guild_id}.json")
    with open(path, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=4)

def parse_duration(duration: str):
    match = re.match(r"(\d+)([smhdwy])", duration.lower())
    if not match:
        return None
    value, unit = int(match.group(1)), match.group(2)
    multipliers = {"s": 1, "m": 60, "h": 3600, "d": 86400, "w": 604800, "y": 31536000}
    return timedelta(seconds=value * multipliers[unit])

def sceneify(text: str):
    """torture"""
    replacements = {
        "a": "4", "e": "3", "i": "1", "o": "0", "u": "ü", "l": "L", "s": "z"
    }
    new_text = ""
    for char in text:
        if char.lower() in replacements and bool(discord.utils.utcnow().second % 2):
            new_text += replacements[char.lower()]
        else:
            new_text += char
    # add random scene kid suffix
    suffixes = [" :3", " xD", " rawr", " uwu", " nyaa~", " >:3" " mommy", " s3npaiii >.<", " owo", " :P", " :33333", " dada", " >.<", " daddy :3"]
    return new_text + suffixes[hash(text) % len(suffixes)]

class SceneCog(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.check_expired.start()

    def cog_unload(self):
        self.check_expired.cancel()

    @commands.command(name="torture")
    async def scene_cmd(self, ctx, member: discord.Member, duration: str = None):
        """Put someone in torture mode"""
        data = load_scene_data(ctx.guild.id)

        end_time = None
        if duration:
            td = parse_duration(duration)
            if td:
                end_time = (datetime.utcnow() + td).timestamp()

        webhook = None
        # create webhook (to replace messages)
        existing = await ctx.channel.webhooks()
        for wh in existing:
            if wh.name == f"scene-{member.id}":
                webhook = wh
                break
        if webhook is None:
            webhook = await ctx.channel.create_webhook(name=f"scene-{member.id}")

        data[str(member.id)] = {
            "webhook_url": webhook.url,
            "end_time": end_time
        }
        save_scene_data(ctx.guild.id, data)

        await ctx.reply(f"`{member.display_name}` is now being tortured `{'until ' + duration if duration else 'indefinitely'}`.")

    @commands.command(name="endtorture")
    async def stopscene_cmd(self, ctx, member: discord.Member):
        """Stop scene mode"""
        data = load_scene_data(ctx.guild.id)
        if str(member.id) not in data:
            return await ctx.reply(f"`{member.display_name}` is not being tortured.")

        # delete webhook
        try:
            wh = await self.bot.fetch_webhook(int(data[str(member.id)]["webhook_url"].split("/")[-1]))
            await wh.delete()
        except Exception:
            pass

        del data[str(member.id)]
        save_scene_data(ctx.guild.id, data)
        await ctx.reply(f"`{member.display_name}` has been freed from torture.")

    @commands.Cog.listener()
    async def on_message(self, message: discord.Message):
        if message.author.bot or not message.guild:
            return

        data = load_scene_data(message.guild.id)
        if str(message.author.id) not in data:
            return

        entry = data[str(message.author.id)]
        try:
            webhook = discord.SyncWebhook.from_url(entry["webhook_url"])
        except Exception:
            return

        await message.delete()
        scene_text = sceneify(message.content)
        await webhook.send(
            content=scene_text,
            username=message.author.display_name,
            avatar_url=message.author.display_avatar.url if message.author.display_avatar else None
        )

    @tasks.loop(minutes=1)
    async def check_expired(self):
        for guild in self.bot.guilds:
            data = load_scene_data(guild.id)
            changed = False
            for uid, entry in list(data.items()):
                if entry["end_time"] and datetime.utcnow().timestamp() > entry["end_time"]:
                    # expire
                    try:
                        wh = await self.bot.fetch_webhook(int(entry["webhook_url"].split("/")[-1]))
                        await wh.delete()
                    except Exception:
                        pass
                    del data[uid]
                    changed = True
            if changed:
                save_scene_data(guild.id, data)

async def setup(bot):
    await bot.add_cog(SceneCog(bot))
