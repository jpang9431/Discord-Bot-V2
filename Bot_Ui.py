import discord
from discord.ui import Button
from discord.ui import View
import yfinance as yf
import random
import Database as db
import json

#menu
class backButton(Button):
    def __init__(self, interaction:discord.Interaction):
        super().__init__(label="Back", style=discord.ButtonStyle.blurple)
        self.interaction = interaction
    async def callback(self,interaction:discord.Interaction):
        await interactionReplyMenu(self.interaction, interaction)

async def interactionReplyMenu(orgInteraction, curInteraction):
    user = curInteraction.user
    embed = discord.Embed(title=user.display_name, color = user.color)
    view = View()
    await editMenu(view, embed, user, orgInteraction)
    await orgInteraction.edit_original_response(view=view, embed=embed)
    await curInteraction.response.defer()

async def editMenu(view:discord.ui.View, embed:discord.Embed, user:discord.User, interaction:discord.Interaction):
    if (not user.avatar == None):
        embed.set_thumbnail(url=user.avatar.url)
    data = await db.getUserData(user.id)
    embed.add_field(name="Menu", value="Click a button below to go to that section")
    embed.add_field(name="User Stats", value="Position: "+str(data[0])+"\nTotal: "+str(data[2])+"\nPoints: "+str(data[3])+"\nStocks: "+str(data[4]),inline=False)
    embed.set_footer(text="*Position and stock last updated: "+str(await db.getLastUpdate()))
    view.add_item(dailyButton(interaction))
    view.add_item(claimQuestsButton(interaction, "Quest")) 
    view.add_item(refreshStocks(interaction, "Stocks"))
    view.add_item(refreshLeaderboard(interaction, "Leader Board"))
    
#quest
quests = {
    0:"Claim the daily reward ? time(s): */?",
    1:"Sell ? stock(s): */?",
    2:"Buy ? stock(s): */?"
}

questDict = {
    "Daily" : 0,
    "Sell Stock" : 1,
    "Buy Stock" : 2
}

class claimQuestsButton(Button):
    def __init__(self, interaction:discord.Interaction, label:str):
        super().__init__(label=label, style=discord.ButtonStyle.blurple)
        self.interaction = interaction
    async def callback(self,interaction:discord.Interaction):
        pointsGained = await db.claimQuests(interaction.user.id)
        await db.updatePoints(interaction.user.id, pointsGained)
        user = interaction.user
        embed = discord.Embed(title=user.display_name, color = user.color)
        view = View()
        await editQuest(view, embed, user, self.interaction)
        embed.add_field(name="Reward", value="You gained "+str(pointsGained)+" points", inline=False)
        await self.interaction.edit_original_response(view=view, embed=embed)
        await interaction.response.defer()

class getNewQuestsButton(Button):
    def __init__(self, interaction:discord.Interaction):
        super().__init__(label="Replace Completed Quests", style=discord.ButtonStyle.blurple)
        self.interaction = interaction
    async def callback(self,interaction:discord.Interaction):
        user = interaction.user
        embed = discord.Embed(title=user.display_name, color = user.color)
        view = View()
        if (await db.checkQuestCooldown(interaction.user.id)):
            await db.setNewQuets(interaction.user.id)
            await db.resetQuestCooldown(interaction.user.id)
            await editQuest(view, embed, user, self.interaction)
        else:
            await editQuest(view, embed, user, self.interaction)
            embed.add_field(name="Cooldown", value="Wait until twomorrow to replace completed quests", inline= False)
        await self.interaction.edit_original_response(view=view, embed=embed)
        await interaction.response.defer()

class resetQuestsButton(Button):
    def __init__(self, interaction:discord.Interaction):
        super().__init__(label="Replace All Quets", style=discord.ButtonStyle.blurple)
        self.interaction = interaction
    async def callback(self, interaction:discord.Interaction):
        user=  interaction.user
        embed = discord.Embed(title=user.display_name, color = user.color)
        view = View()
        if (await db.checkQuestCooldown(interaction.user.id)):
            await db.resetQuests(interaction.user.id)
            await db.resetQuestCooldown(interaction.user.id)
            await editQuest(view, embed, user, self.interaction)
        else:
            await editQuest(view, embed, user, self.interaction)
            embed.add_field(name="Cooldown", value="Wait until twomorrow to replace all quests", inline = False)
        await self.interaction.edit_original_response(view=view, embed=embed)
        await interaction.response.defer()

async def interpretQuest(quest):
    msg = quests.get(quest["id"])
    msg = msg.replace("?",str(quest["goal"]))
    msg = msg.replace("*",str(quest["progress"]))
    if (quest["goal"]==1):
        msg = msg.replace("(s)","")
    else:
        msg = msg.replace("(s)", "s")
    msg += " - Reward: " + str(quest["points"])
    if (quest["progress"]>=quest["goal"]):
        msg = "~~"+msg+"~~"
    return msg +"\n"

async def editQuest(view:discord.ui.View, embed:discord.Embed, user:discord.User, interaction):
    if (not user.avatar == None):
        embed.set_thumbnail(url=user.avatar.url)
    questList = await db.getQuests(user.id)
    textQuests = ""
    for quest in questList:
        textQuests+=await interpretQuest(quest)
    embed.add_field(name="Quests", value=textQuests)
    view.add_item(backButton(interaction))
    view.add_item(claimQuestsButton(interaction, "Claim Quest"))
    view.add_item(getNewQuestsButton(interaction))
    view.add_item(resetQuestsButton(interaction))
    
#daily
class dailyButton(Button):
    def __init__(self, interaction:discord.Interaction):
        super().__init__(label="Daily", style=discord.ButtonStyle.blurple)
        self.interaction = interaction
    async def callback(self, interaction:discord.Interaction):
        user = interaction.user
        user = interaction.user
        view = View()
        embed = discord.Embed(title=user.display_name, color = user.color)
        await editDaily(view, embed, user, self.interaction)
        await self.interaction.edit_original_response(view=view, embed=embed)
        await interaction.response.defer()

async def editDaily(view:discord.ui.View, embed:discord.Embed, user:discord.User, interaction:discord.Interaction):   
    if (not user.avatar == None):
        embed.set_thumbnail(url=user.avatar.url)
    embed.add_field(name="Daily", value="Click below to claim a daily reward")
    if (await db.checkDailyCooldown(user.id)):
        await db.resetDailyCooldown(user.id)
        points = random.randint(10,20)
        await db.updatePoints(user.id, points)
        embed.add_field(name="Reward", value="You recived "+str(points)+" points", inline=False)
        await db.updateQuests(user.id, questDict["Daily"])
    else:
        embed.add_field(name="Cooldown", value="Wait until twomorrow to claim your daily reward", inline=False)
    view.add_item(backButton(interaction))
    view.add_item(dailyButton(interaction))

#stock market
class buyShares(Button):
    def __init__(self, interaction:discord.Interaction, amount:int, ticker:str):
        super().__init__(label="Buy "+str(amount), style=discord.ButtonStyle.blurple)
        self.interaction = interaction
        self.amount = amount
        self.ticker = ticker
    async def callback(self, interaction:discord.Interaction):
        user = interaction.user
        view = View()
        embed = discord.Embed(title=user.display_name, color=user.color)
        points = await db.getPoints(user.id)
        stock_ticker = yf.Ticker(self.ticker)
        stock_ticker_info = stock_ticker.info
        canAfford = points>=stock_ticker_info["ask"]*self.amount
        if (canAfford):
            await db.updateStock(user.id, stock_ticker_info, "Buy", self.amount)
        await edit_stock_market_view_and_embed(view, embed, self.ticker, user, self.interaction, self.amount)
        if (canAfford):
            embed.add_field(name="Action Result", value="Sucessfully bought "+str(self.amount)+" of "+stock_ticker_info["shortName"], inline=False)
        else:
            embed.add_field(name="Action Result", value="Too poor to afford the stocks", inline=False)
        await self.interaction.edit_original_response(view=view, embed=embed)
        await interaction.response.defer()

class sellShares(Button):
    def __init__(self, interaction:discord.Interaction, amount:int, ticker:str):
        super().__init__(label="Sell "+str(amount), style=discord.ButtonStyle.blurple)
        self.interaction = interaction
        self.amount = amount
        self.ticker = ticker
    async def callback(self, interaction:discord.Interaction):
        user = interaction.user
        view = View()
        embed = discord.Embed(title=user.display_name, color=user.color)
        stock_ticker = yf.Ticker(self.ticker)
        stock_ticker_info = stock_ticker.info
        stock_ticker_amount = await db.getAmountOfStock(user.id, self.ticker)
        hasStocks = self.amount<=stock_ticker_amount
        if (hasStocks):
            await db.updateStock(user.id, stock_ticker_info, "Sell", self.amount)
        await edit_stock_market_view_and_embed(view, embed, self.ticker, user, self.interaction, self.amount)
        if (hasStocks):
            embed.add_field(name="Action Result", value="Sucessfully sold "+str(self.amount)+" of "+stock_ticker_info["shortName"], inline=False)
        else:
            embed.add_field(name="Action Result", value="Too few stocks own to sell", inline=False)
        await self.interaction.edit_original_response(view=view, embed=embed)
        await interaction.response.defer()
            
async def edit_stock_market_view_and_embed(view:discord.ui.View, embed:discord.Embed, ticker:str, user:discord.User, interaction:discord.Interaction, amount:int):
    embed.add_field(name="Stock Market", value="Stock data is displayed below, at the very bottom click buy or sell to buy or sell the stock")
    stock_ticker = yf.Ticker(ticker)
    info = stock_ticker.info
    msg = "Company Website: "+info["website"]+"\n"
    msg += "Industry: "+info["industry"]+"\n"
    msg += "Buy Price: "+str(info["ask"])+"\n"
    msg += "Sell Price: "+str(info["bid"])
    embed.add_field(name=info["shortName"]+" ("+ticker+")", value=msg, inline=False)
    numShares = await db.getAmountOfStock(user.id, ticker)
    userDataMsg = "Points Balance: "+str(await db.getPoints(user.id))+"\n"
    if (not numShares):
        userDataMsg += "Owned Shares: 0\n"
        userDataMsg += "Total Value: 0\n"
    else:
        userDataMsg += "Owned Shares: "+str(numShares)+"\n"
        userDataMsg += "Total Value: "+str(int(numShares)*info["bid"])+"\n"
    embed.add_field(name="User Data", value=userDataMsg)
    view.add_item(backButton(interaction))
    view.add_item(buyShares(interaction, amount, ticker))
    view.add_item(sellShares(interaction, amount, ticker))
    
class refreshStocks(Button):
    def __init__(self, interaction:discord.Interaction, label:str):
        super().__init__(label=label, style=discord.ButtonStyle.blurple)
        self.interaction = interaction
    async def callback(self, interaction:discord.Interaction):   
        user = interaction.user
        view = View()
        embed = discord.Embed(title=user.display_name, color=user.color)
        await edit_stock_view_and_embed(view, embed,user,self.interaction)  
        await self.interaction.edit_original_response(view=view, embed=embed)
        await interaction.response.defer()

async def edit_stock_view_and_embed(view:discord.ui.View, embed:discord.Embed, user:discord.User, interaction:discord.Interaction):
    data = await db.getStocks(user.id)
    msg = ""
    totalStockValue = 0
    for key, value in data.items():
        info = yf.Ticker(key).info
        msg += info["shortName"]+" ("+key+") | Amount: "+str(value)+" | Value: "+str(value*info["bid"])+"\n"
        totalStockValue += value*info["bid"]
    await db.setStockValue(user.id, totalStockValue)
    embed.add_field(name="Owned Stocks", value=msg)
    if (not user.avatar == None):
        embed.set_thumbnail(url=user.avatar.url)
    view.add_item(backButton(interaction))
    view.add_item(refreshStocks(interaction, "Refresh Stocks"))

class refreshLeaderboard(Button):
    def __init__(self, interaction:discord.Interaction, label:str):
        super().__init__(label=label, style=discord.ButtonStyle.blurple)
        self.interaction = interaction
    async def callback(self, interaction:discord.Interaction):   
        user = interaction.user
        view = View()
        embed = discord.Embed(title=user.display_name, color=user.color)
        await edit_leaderboard(view,embed,user,interaction)
        await self.interaction.edit_original_response(view=view, embed=embed)
        await interaction.response.defer()
    
async def edit_leaderboard(view:discord.ui.View, embed:discord.Embed, user:discord.User, interaction:discord.Interaction):
    leaderboard = json.loads(await db.getLeaderBoard())
    userData = await db.getUserData(user.id)
    lastUpdate = await db.getLastUpdate()
    if (not user.avatar == None):
        embed.set_thumbnail(url=user.avatar.url)
    embed.add_field(name="Username and Total", value=leaderboard[0]+"\n"+str(userData[0])+"."+userData[1])
    embed.add_field(name="Total", value=leaderboard[1]+"\n"+str(userData[2]))
    embed.add_field(name="Points|Stocks", value=leaderboard[2]+"\n"+str(userData[3])+"|"+str(userData[4]))
    embed.set_footer(text="Last Updated: "+lastUpdate)
    view.add_item(backButton(interaction))
    view.add_item(refreshLeaderboard(interaction,"Refresh Leaderboard"))
    
    
  
        