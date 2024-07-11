import json
import Database as db
from Outputs.menu import editMenu
from Outputs.quest import editQuest
import discord
from discord.ext import commands
from discord.ui import View


secertFile = open("config.json")
fileData = json.load(secertFile)

client = commands.Bot(command_prefix="!", intents=discord.Intents.all())
token = fileData["token"]

@client.event
async def on_ready():
    db.createRepository()
    await client.tree.sync()

async def add_guild(guild):
    for user in guild.members:
        print(user)
        if not user.bot:
            db.insertNewUserIfNotExists(user.id)
        
@client.event
async def on_guild_join(guild):
    await add_guild(guild)

@client.tree.command(name="add_new_users", description="Add users not in the database")
async def add_new_users(interaction:discord.Interaction):
    await add_guild(interaction.guild)
    await interaction.response.send_message(content="Process completed", ephemeral=True)
    
@client.tree.command(name="quest", description="Check/Claim quest progress and get new quests")
async def quest(interaction:discord.Interaction):
    userId = interaction.user.id
    db.insertNewUserIfNotExists(userId)
    user = interaction.user
    embed = discord.Embed(title=user.display_name, color = user.color)
    view = View()
    await editQuest(view, embed, user,interaction)
    await interaction.response.send_message(embed=embed, view=view)

@client.tree.command(name="menu", description="View the menu of options")
async def menu(interaction:discord.Interaction):
    userId = interaction.user.id
    db.insertNewUserIfNotExists(userId)
    user = interaction.user
    embed = discord.Embed(title=user.display_name, color = user.color)
    view = View()
    await editMenu(view, embed, user,interaction)
    await interaction.response.send_message(embed=embed, view=view)
    
client.run(token)