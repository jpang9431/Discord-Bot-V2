from Outputs.quest import interactionReplyQuest
import discord
from discord.ui import Button
from discord.ui import View

class backButton(Button):
    def __init__(self, interaction:discord.Interaction):
        super().__init__(label="Back", style=discord.ButtonStyle.blurple)
        self.interaction = interaction
    async def callback(self,interaction:discord.Interaction):
        await interactionReplyMenu(self.interaction, interaction)

class questButton(Button):
    def __init__(self, interaction:discord.Interaction):
        super().__init__(label="Quest", style=discord.ButtonStyle.blurple)
        self.interaction = interaction
    async def callback(self,interaction:discord.Interaction):
        await interactionReplyQuest(self.interaction, interaction)

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
    view.add_item(questButton(interaction))
    
