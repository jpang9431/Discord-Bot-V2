import json
import Database as db
from Bot_Ui import editMenu
from Bot_Ui import editQuest
from Bot_Ui import editDaily
from Bot_Ui import edit_stock_market_view_and_embed
from Bot_Ui import edit_stock_view_and_embed
from Bot_Ui import edit_leaderboard
import discord
from discord.ext import commands
from discord.ui import View
from discord import app_commands
import yfinance as yf
import asyncio

secertFile = open("config.json")
fileData = json.load(secertFile)

client = commands.Bot(command_prefix="!", intents=discord.Intents.all())
token = fileData["token"]

async def updateLeaderBoardInterval():
    while True:
        await db.updateLeaderBoard()
        await asyncio.sleep(3600)

@client.event
async def on_ready():
    db.createRepository()
    await db.updateLeaderBoard()
    await client.tree.sync()
    await updateLeaderBoardInterval()
    

async def add_guild(guild):
    for user in guild.members:
        if not user.bot:
            await db.insertNewUserIfNotExists(user.id, user.global_name)
        
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
    await db.insertNewUserIfNotExists(userId, interaction.user.global_name)
    user = interaction.user
    embed = discord.Embed(title=user.display_name, color = user.color)
    view = View()
    await editQuest(view, embed, user,interaction)
    await interaction.response.send_message(embed=embed, view=view)

@client.tree.command(name="menu", description="View the menu of options")
async def menu(interaction:discord.Interaction):
    userId = interaction.user.id
    await db.insertNewUserIfNotExists(userId, interaction.user.global_name)
    user = interaction.user
    embed = discord.Embed(title=user.display_name, color = user.color)
    view = View()
    await editMenu(view, embed, user, interaction)
    await interaction.response.send_message(embed=embed, view=view)

@client.tree.command(name="daily", description="Claim daily reward")
async def daily(interaction:discord.Interaction):
    user = interaction.user
    await db.insertNewUserIfNotExists(user.id, interaction.user.global_name)
    embed = discord.Embed(title=user.display_name, color = user.color)
    view = View()
    await editDaily(view, embed, user, interaction)
    await interaction.response.send_message(embed=embed, view=view)

@client.tree.command(name="stock_market", description="Display the menu for the stock market")
@app_commands.describe(ticker="The stock ticker symbol that you want to look up")
@app_commands.describe(amount="Amount of stocks to buy/sell")
async def stock_market(interaction:discord.Interaction, ticker: str, amount: app_commands.Range[int,0]):
    tickerObj = yf.Ticker(ticker)
    if(tickerObj.cashflow.empty):
        await interaction.response.send_message(content="Error, the stock is not found", ephemeral=True)
        return
    user = interaction.user
    view = View()
    embed = discord.Embed(title=user.display_name, color = user.color)
    await edit_stock_market_view_and_embed(view, embed, ticker, user, interaction, amount)
    await interaction.response.send_message(embed=embed, view=view)
    
@client.tree.command(name="buy_stocks", description="Buy stocks")
@app_commands.describe(ticker="The stock ticker symbol that you want to look up")
@app_commands.describe(amount="Amount of stocks to buy/sell")
async def buy_stocks(interaction:discord.Interaction, ticker: str, amount: app_commands.Range[int,0]):
    stock_ticker = yf.Ticker(ticker)
    if(stock_ticker.cashflow.empty):
        await interaction.response.send_message(content="Error, the stock is not found", ephemeral=True)
        return
    user = interaction.user
    view = View()
    embed = discord.Embed(title=user.display_name, color = user.color)
    points = await db.getPoints(user.id)
    stock_ticker_info = stock_ticker.info
    canAfford = points>=stock_ticker_info["ask"]*amount
    if (canAfford):
        await db.updateStock(user.id, stock_ticker_info, "Buy", amount)
    await edit_stock_market_view_and_embed(view=view, embed=embed, ticker=ticker, user=user, interaction=interaction, amount=amount)
    if (canAfford):
            embed.add_field(name="Action Result", value="Sucessfully bought "+str(amount)+" of "+stock_ticker_info["shortName"], inline=False)
    else:
        embed.add_field(name="Action Result", value="Too poor to afford the stocks", inline=False)
    await interaction.response.send_message(view=view, embed=embed)

@client.tree.command(name="sell_stocks", description="Sell stocks")
@app_commands.describe(ticker="The stock ticker symbol that you want to look up")
@app_commands.describe(amount="Amount of stocks to buy/sell")
async def sell_stocks(interaction:discord.Interaction, ticker: str, amount: app_commands.Range[int,0]):
    stock_ticker = yf.Ticker(ticker)
    if(stock_ticker.cashflow.empty):
        await interaction.response.send_message(content="Error, the stock is not found", ephemeral=True)
        return
    user = interaction.user
    view = View()
    embed = discord.Embed(title=user.display_name, color = user.color)
    stock_ticker_info = stock_ticker.info
    stock_ticker_amount = await db.getAmountOfStock(user.id, ticker)
    hasStocks = amount<=stock_ticker_amount
    if (hasStocks):
        await db.updateStock(user.id, stock_ticker_info, "Sell", amount)
    await edit_stock_market_view_and_embed(view, embed, ticker, user, interaction, amount)
    if (hasStocks):
        embed.add_field(name="Action Result", value="Sucessfully sold "+str(amount)+" of "+stock_ticker_info["shortName"], inline=False)
    else:
        embed.add_field(name="Action Result", value="Too few stocks own to sell", inline=False)
    await interaction.response.send_message(view=view, embed=embed)

@client.tree.command(name="owned_stocks", description="View stocks owned")
async def owned_stocks(interaction:discord.Interaction):
    user = interaction.user
    view = View()
    embed = discord.Embed(title=user.display_name, color = user.color)
    await edit_stock_view_and_embed(view, embed, interaction.user, interaction)
    await interaction.response.send_message(embed=embed, view=view)


@client.tree.command(name="update_leaderboard", description="Refresh leaderboard")
@app_commands.checks.has_permissions(administrator=True)
async def update_leaderboard(interaction:discord.Interaction):
    await db.updateLeaderBoard()
    user = interaction.user
    view = View()
    embed = discord.Embed(title=user.display_name, color = user.color)
    await edit_leaderboard(view, embed, interaction.user, interaction)
    await interaction.response.send_message(view=view, embed=embed)

@update_leaderboard.error
async def update_leaderboard_error(interaction, error):
    await interaction.response.send_message(content="You do not have the permission to update the leaderboard", ephemeral=True)

client.run(token)

