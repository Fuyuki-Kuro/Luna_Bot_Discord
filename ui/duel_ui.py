import discord
from discord import ui

class DuelChallengeView(ui.View):
    def __init__(self, duel_id: str):
        super().__init__(timeout=3600)
        self.accept_button.custom_id = f"duel_accept_{duel_id}"
        self.decline_button.custom_id = f"duel_decline_{duel_id}"

    @ui.button(label="Aceitar Duelo", style=discord.ButtonStyle.success, emoji="⚔️")
    async def accept_button(self, interaction: discord.Interaction, button: ui.Button):
        pass

    @ui.button(label="Recusar", style=discord.ButtonStyle.danger)
    async def decline_button(self, interaction: discord.Interaction, button: ui.Button):
        pass

class DuelPanelView(ui.View):
    def __init__(self, duel_id: str):
        super().__init__(timeout=None)
        # --- CORREÇÃO APLICADA AQUI ---
        # Simplificamos o custom_id para garantir a leitura correta.
        self.report_winner_button.custom_id = f"duel_report_{duel_id}"

    @ui.button(label="Declarar Vitória", style=discord.ButtonStyle.primary, emoji="🏆")
    async def report_winner_button(self, interaction: discord.Interaction, button: ui.Button):
        # A lógica é tratada no Cog
        pass