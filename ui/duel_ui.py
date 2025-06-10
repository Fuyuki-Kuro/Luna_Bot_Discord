import discord
from discord import ui
from typing import Dict, Any

class DuelChallengeView(ui.View):
    # ... (esta classe não muda) ...
    def __init__(self, duel_id: str):
        super().__init__(timeout=3600)
        self.accept_button.custom_id = f"duel_accept_{duel_id}"
        self.decline_button.custom_id = f"duel_decline_{duel_id}"
    @ui.button(label="Aceitar Duelo", style=discord.ButtonStyle.success, emoji="⚔️")
    async def accept_button(self, interaction: discord.Interaction, button: ui.Button): pass
    @ui.button(label="Recusar", style=discord.ButtonStyle.danger)
    async def decline_button(self, interaction: discord.Interaction, button: ui.Button): pass

class DuelPanelView(ui.View):
    """Painel dinâmico que mostra os botões corretos com base no status do duelo."""
    def __init__(self, duel_data: Dict[str, Any]):
        super().__init__(timeout=None)
        duel_id = duel_data['_id']
        
        # Limpa quaisquer botões que possam existir
        self.clear_items()
        
        status = duel_data.get('status')
        
        if status == "in_progress":
            self.add_item(ui.Button(label="Reportar Vitória", style=discord.ButtonStyle.primary, emoji="🏆", custom_id=f"duel_report_{duel_id}"))
        
        elif status == "awaiting_confirmation":
            self.add_item(ui.Button(label="Confirmar Derrota", style=discord.ButtonStyle.success, emoji="✅", custom_id=f"duel_confirm_{duel_id}"))
            self.add_item(ui.Button(label="Disputar Resultado", style=discord.ButtonStyle.danger, emoji="❗", custom_id=f"duel_dispute_{duel_id}"))

class DisputeDecisionView(ui.View):
    # ... (esta classe não muda) ...
    def __init__(self, duel_data: Dict[str, Any]):
        super().__init__(timeout=None)
        duel_id = duel_data['_id']
        self.challenger_win_button.custom_id = f"duel_modwin_{duel_id}_{duel_data['challenger_id']}"
        self.opponent_win_button.custom_id = f"duel_modwin_{duel_id}_{duel_data['opponent_id']}"
    @ui.button(label="Dar Vitória ao Desafiante", style=discord.ButtonStyle.primary)
    async def challenger_win_button(self, interaction: discord.Interaction, button: ui.Button): pass
    @ui.button(label="Dar Vitória ao Oponente", style=discord.ButtonStyle.secondary)
    async def opponent_win_button(self, interaction: discord.Interaction, button: ui.Button): pass