import discord
from discord.ui import Button
from discord.ui import View
import random
import Database as db

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
    embed.set_thumbnail(url=user.avatar.url)
    embed.add_field(name="Menu", value="Click a button below to go to that section")
    userPoints = await db.getPoints(user.id)
    embed.add_field(name="Points", value="You have "+str(userPoints)+" points", inline=False)
    view.add_item(dailyButton(interaction))
    view.add_item(claimQuestsButton(interaction, "Quest"))
    view.add_item(coinFlipButton(interaction, 0))
    
    
#quest
quests = {
    0:"Claim the daily reward ? time: */?",
    1:"Flip a coin ? time: */?",
    2:"Play blackjack ? time: */?"
}

class claimQuestsButton(Button):
    def __init__(self, interaction:discord.Interaction, label:str):
        super().__init__(label=label, style=discord.ButtonStyle.blurple)
        self.interaction = interaction
    async def callback(self,interaction:discord.Interaction):
        pointsGained = await db.claimQuests(interaction.user.id)
        user = interaction.user
        embed = discord.Embed(title=user.display_name, color = user.color)
        view = View()
        await editQuest(view, embed, user, self.interaction)
        embed.add_field(name="Reward", value="You gained "+str(pointsGained)+" points", inline=False)
        await self.interaction.edit_original_response(view=view, embed=embed)
        await interaction.response.defer()

class getNewQuestsButton(Button):
    def __init__(self, interaction:discord.Interaction):
        super().__init__(label="Get New Quests", style=discord.ButtonStyle.blurple)
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

async def interpretQuest(quest):
    msg = quests.get(quest["id"])
    msg = msg.replace("?",str(quest["goal"]))
    msg = msg.replace("*",str(quest["progress"]))
    msg += " - Reward: " + str(quest["points"])
    if (quest["progress"]>=quest["goal"]):
        msg = "~~"+msg+"~~"
    return msg +"\n"

async def editQuest(view:discord.ui.View, embed:discord.Embed, user:discord.User, interaction):
    embed.set_thumbnail(url=user.avatar.url)
    questList = await db.getQuests(user.id)
    textQuests = ""
    for quest in questList:
        textQuests+=await interpretQuest(quest)
    embed.add_field(name="Quests", value=textQuests)
    view.add_item(backButton(interaction))
    view.add_item(claimQuestsButton(interaction, "Claim Quest"))
    view.add_item(getNewQuestsButton(interaction))
    
#coin_flip
COINFLIP_OPTIONS = ["Heads", "Tails"]

class coinFlipButton(Button):
    def __init__(self, interaction:discord.Interaction, bet:int):
        super().__init__(label="Flip Coin", style=discord.ButtonStyle.blurple)
        self.interaction = interaction
        self.bet = bet
    async def callback(self, interaction:discord.Interaction):
        user = interaction.user
        view = View()
        embed = discord.Embed(title=user.display_name, color = user.color)
        await editCoinFlip(view, embed, user, self.interaction, self.bet)
        await self.interaction.edit_original_response(view=view, embed=embed)
        await interaction.response.defer()

class flipCoinButton(Button):
    def __init__(self, interaction:discord.Interaction, bet:int, label:str):     
        super().__init__(label=label, style=discord.ButtonStyle.blurple)
        self.interaction = interaction
        self.bet = bet
        self.label = label
    async def callback(self, interaction:discord.Interaction):
        user = interaction.user
        view = View()
        embed = discord.Embed(title=user.display_name, color = user.color)
        points = await db.getPoints(user.id)
        if (self.bet> points):
            self.bet = 0
        await flipCoin(view, embed, user, self.interaction, self.bet, self.label, COINFLIP_OPTIONS[random.randint(0,1)])
        await self.interaction.edit_original_response(view=view, embed=embed)
        await interaction.response.defer()
        
async def flipCoin(view:discord.ui.View, embed:discord.Embed, user:discord.User, interaction:discord.Interaction, bet:int, choice:str, result:str):
    await editCoinFlip(view, embed, user, interaction, bet)
    msg = ""
    if choice==result:
        msg += "You won: "+str(bet)
        await db.transferFromHouse(user.id, bet)
    else:
        msg += "You lost: "+str(bet)
        await db.transferFromHouse(user.id, bet*-1)
    msg+="\n You chose **"+choice+"** the result was **"+result+"**"
    embed.add_field(name="Result", value=msg, inline=False)
    
 
async def editCoinFlip(view:discord.ui.View, embed:discord.Embed, user:discord.User, interaction:discord.Interaction, bet:int):
    embed.set_thumbnail(url=user.avatar.url)
    embed.add_field(name="Coin Flip", value="Click heads or tails below to bet on that value.\nBet: "+str(bet)+"\nReturns 2x on win", inline=False)
    view.add_item(backButton(interaction))
    view.add_item(flipCoinButton(interaction, bet, "Heads"))
    view.add_item(flipCoinButton(interaction, bet, "Tails"))
    
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
    embed.set_thumbnail(url=user.avatar.url)
    embed.add_field(name="Daily", value="Click below to claim a daily reward")
    if (await db.checkDailyCooldown(user.id)):
        await db.resetDailyCooldown(user.id)
        points = random.randint(10,20)
        await db.updatePoints(user.id, points)
        embed.add_field(name="Reward", value="You recived "+str(points)+" points", inline=False)
    else:
        embed.add_field(name="Cooldown", value="Wait until twomorrow to claim your daily reward", inline=False)
    view.add_item(backButton(interaction))
    view.add_item(dailyButton(interaction))