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
    embed.add_field(name="", value="**Click a button below to go to that section**")
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
        pointsGained = db.claimQuests(interaction.user.id)
        user = interaction.user
        embed = discord.Embed(title=user.display_name, color = user.color)
        view = View()
        await editQuest(view, embed, user,interaction)
        embed.add_field(name="Reward", value="You gained "+str(pointsGained)+" points")
        await self.interaction.edit_original_response(view=view, embed=embed)

class getNewQuestsButton(Button):
    def __init__(self, interaction:discord.Interaction):
        super().__init__(label="Get New Quests", style=discord.ButtonStyle.blurple)
        self.interaction = interaction
    async def callback(self,interaction:discord.Interaction):
        if (await db.checkQuestCooldown(interaction.user.id)):
            await db.setNewQuets(interaction.user.id)
            db.resetQuestCooldown(interaction.user.id)
            await interactionReplyQuest(self.interaction, interaction)
        else:
            await interactionReplyQuest(self.interaction, interaction, "Cooldown", "Wait until twomorrow to replace completed quests")

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
    
async def interactionReplyQuest(orgInteraction, curInteraction, extraName="", extraValue=""):
    user = curInteraction.user
    embed = discord.Embed(title=user.display_name, color = user.color)
    view = View()
    await editQuest(view, embed, user,orgInteraction)
    if (not extraName=="" and not extraValue==""):
        embed.add_field(name=extraName, value=extraValue)
    await orgInteraction.edit_original_response(view=view, embed=embed)
    
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