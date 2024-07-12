import json
import Database as db
from Bot_Ui import editMenu
from Bot_Ui import editQuest
from Bot_Ui import editCoinFlip
import discord
from discord.ext import commands
from discord.ui import View
from discord import app_commands

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
    await editMenu(view, embed, user, interaction)
    await interaction.response.send_message(embed=embed, view=view)

@client.tree.command(name="coin_flip", description="Flip a coin to win some points")
@app_commands.describe(bet="The amount you want to be must be >=0 and <= the number of points you have, if the bet is out of range it goes to the default of 0")
async def coin_flip(interaction:discord.Interaction, bet:int):
    userId = interaction.user.id
    db.insertNewUserIfNotExists(userId)
    user = interaction.user
    embed = discord.Embed(title=user.display_name, color = user.color)
    view = View()
    await editCoinFlip(view, embed, user, interaction, bet)
    await interaction.response.send_message(embed=embed, view=view)

client.run(token)