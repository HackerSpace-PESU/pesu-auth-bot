import logging
import traceback

import discord
from discord.ext import commands, tasks

from .db import DatabaseCog


class BaseCog(commands.Cog):
    """
    This cog contains all base functions
    """

    def __init__(self, client: commands.Bot, db: DatabaseCog):
        self.client = client
        self.db = db
        self.count = 0

        self.change_status_loop.start()

    @commands.Cog.listener()
    async def on_ready(self):
        """
        Called when the bot is ready
        """
        logging.info(f"Logged in as {self.client.user.name}#{self.client.user.discriminator}")

    @commands.Cog.listener()
    async def on_guild_join(self, guild):
        """
        Called when the bot joins a new server
        """
        logging.info(f"Joined server {guild.name}")
        self.db.add_server(guild.id)
        embed = discord.Embed(
            title="PESU Auth Bot - Hello!",
            description="I am the PESU Auth Bot. I am here to help you with your server's authentication. "
                        "To get started, please use the `/setup` command to add an existing role as the "
                        "verification role. Once you have done that, members can use the `/auth` command to "
                        "authenticate and assign the verification role to themselves.",
            color=discord.Color.green(),
        )
        for member in guild.members:
            if member.guild_permissions.administrator:
                await member.send(embed=embed)

        for channel in guild.text_channels:
            if channel.permissions_for(guild.me).send_messages:
                await channel.send(embed=embed)
                break

    @commands.Cog.listener()
    async def on_guild_remove(self, guild):
        """
        Called when the bot leaves a server
        """
        logging.info(f"Left server {guild.name}")
        self.db.remove_server(guild.id)

    @tasks.loop(hours=2)
    async def change_status_loop(self):
        """
        Changes the bot status every 2 hours
        """
        await self.client.wait_until_ready()
        logging.info("Changing bot status")
        self.count += 1
        if self.count == 3:
            self.count = 0
            member_count = 0
            for guild in self.client.guilds:
                guild = await self.client.fetch_guild(guild.id)
                member_count += guild.approximate_member_count
            await self.client.change_presence(activity=discord.Activity(type=discord.ActivityType.watching, name=f"over {(member_count // 100) * 100} members"))
        elif self.count == 2:
            await self.client.change_presence(activity=discord.Activity(type=discord.ActivityType.watching, name=f"{len(self.client.guilds)} servers"))
        else:
            await self.client.change_presence(activity=discord.Game(name=f"with the PRIDE of PESU"))


async def setup(client: commands.Bot):
    """
    Adds the cog to the bot
    """
    await client.add_cog(BaseCog(client, client.db))