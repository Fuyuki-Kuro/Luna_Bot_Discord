import discord
from discord import ui

class GuildPanelView(ui.View):
    """View com os botões de ação para o painel da guilda."""
    def __init__(self):
        super().__init__(timeout=None)

    @ui.button(label="Convidar Membro", style=discord.ButtonStyle.success, emoji="📨")
    async def invite_member(self, interaction: discord.Interaction, button: ui.Button):
        await interaction.response.send_message("Em breve: Convidar um novo membro para a guilda.", ephemeral=True)

    @ui.button(label="Recrutar Equipe", style=discord.ButtonStyle.primary, emoji="🤝")
    async def recruit_team(self, interaction: discord.Interaction, button: ui.Button):
        await interaction.response.send_message("Em breve: Abrir o painel de recrutamento de equipes.", ephemeral=True)

    @ui.button(label="Disbandar Guilda", style=discord.ButtonStyle.danger, emoji="💥")
    async def disband_guild(self, interaction: discord.Interaction, button: ui.Button):
        await interaction.response.send_message("Em breve: Iniciar o processo para deletar a guilda.", ephemeral=True)