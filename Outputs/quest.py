import Database as db
import Outputs.menu as menu
import discord
from discord.ui import Button
from discord.ui import View

quests = {
    0:"Claim the daily reward ? time: */?",
    1:"Flip a coin ? time: */?",
    2:"Play blackjack ? time: */?"
}

class claimQuestsButton(Button):
    def __init__(self, interaction:discord.Interaction):
        super().__init__(label="Claim Quests", style=discord.ButtonStyle.blurple)
        self.interaction = interaction
    async def callback(self,interaction:discord.Interaction):
        pointsGained = db.claimQuests(interaction.user.id)
        user = interaction.user
        embed = discord.Embed(title=user.display_name, color = user.color)
        view = View()
        await editQuest(view, embed, user,interaction)
        await self.interaction.edit_original_response(view=view, embed=embed)
        await interaction.response.send_message(content="You gained "+str(pointsGained)+" points", ephemeral=True)

class getNewQuestsButton(Button):
    def __init__(self, interaction:discord.Interaction):
        super().__init__(label="Get New Quests", style=discord.ButtonStyle.blurple)
        self.interaction = interaction
    async def callback(self,interaction:discord.Interaction):
        if (db.checkQuestCooldown(interaction.user.id)):
            db.setNewQuets(interaction.user.id)
            db.resetQuestCooldown(interaction.user.id)
        else:
            await interaction.response.send_message(content="Wait until twomorrow to replace completed quests", ephemeral=True)
        await interactionReplyQuest(self.interaction, interaction)
            
        
class resetQuestsButton(Button):
    def __init__(self, interaction:discord.Interaction):
        super().__init__(label="Reset Quests", style=discord.ButtonStyle.blurple)
        self.interaction = interaction
    async def callback(self,interaction:discord.Interaction):
        if (db.checkQuestCooldown(interaction.user.id)):
            db.resetQuestCooldown(interaction.user.id)
            db.resetQuests(interaction.user.id)
        else:
            await interaction.response.send_message(content="Wait until twomorrow to change all your quests", ephemeral=True)
        await interactionReplyQuest(self.interaction, interaction)
        

async def interpretQuest(quest):
    if (quest=="None"):
        return ""
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
    view.add_item(menu.backButton(interaction))
    view.add_item(claimQuestsButton(interaction))
    view.add_item(getNewQuestsButton(interaction))
    view.add_item(resetQuestsButton(interaction))
    
async def interactionReplyQuest(orgInteraction, curInteraction):
    user = curInteraction.user
    embed = discord.Embed(title=user.display_name, color = user.color)
    view = View()
    await editQuest(view, embed, user,orgInteraction)
    await orgInteraction.edit_original_response(view=view, embed=embed)
    await curInteraction.response.defer()