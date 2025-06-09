import discord
from discord import ui
import logging
import os

from utils.embeds import create_player_card_embed
# Não precisamos mais da PlayerCardView
# from .player_card_ui import PlayerCardView 

logger = logging.getLogger(__name__)

try:
    PLAYER_CARD_CHANNEL_ID = int(os.getenv('PLAYER_CARD_CHANNEL_ID'))
    SERVER_ID = int(os.getenv('SERVER_ID'))
except (TypeError, ValueError):
    PLAYER_CARD_CHANNEL_ID = 0
    SERVER_ID = 0

class RegistrationModal(ui.Modal, title="Formulário de Registro"):
    wr_nickname = ui.TextInput(label="Seu Nick no Wild Rift (ex: Nome#TAG)", required=True)
    wr_region = ui.TextInput(label="Sua região (ex: BR, LAS, NA)", required=True, max_length=5)
    preferred_roles = ui.TextInput(label="Suas rotas preferidas (separadas por vírgula)", style=discord.TextStyle.paragraph, required=True)

    async def on_submit(self, interaction: discord.Interaction):
        await interaction.response.defer(ephemeral=True)
        
        # Validação do Nickname
        nickname_value = self.wr_nickname.value
        if '#' not in nickname_value or len(nickname_value.split('#')) != 2 or not nickname_value.split('#')[0] or not nickname_value.split('#')[1]:
            return await interaction.followup.send("❌ **Formato de Nick Inválido!** Use `Nome#TAG`.", ephemeral=True)
        
        registration_cog = interaction.client.get_cog("RegistrationCog")
        player_service = registration_cog.player_service
        
        roles_list = [role.strip().capitalize() for role in self.preferred_roles.value.split(',')]
        
        await player_service.update_player_registration(
            member_id=interaction.user.id, nickname=nickname_value,
            region=self.wr_region.value.upper(), roles=roles_list
        )
        
        guild = interaction.client.get_guild(SERVER_ID)
        member = guild.get_member(interaction.user.id) if guild else None

        if guild and member:
            roles_to_add = [role for role_name in roles_list if (role := discord.utils.find(lambda r: r.name.lower() == role_name.lower(), guild.roles))]
            if roles_to_add:
                try:
                    await member.add_roles(*roles_to_add, reason="Rotas definidas no registro.")
                except discord.Forbidden:
                    logger.error(f"Sem permissão para adicionar cargos para {member.display_name}.")

        if PLAYER_CARD_CHANNEL_ID != 0 and guild and member:
            card_channel = guild.get_channel(PLAYER_CARD_CHANNEL_ID)
            if card_channel:
                try:
                    player_data = await player_service.get_player_by_id(member.id)
                    if player_data:
                        card_embed = await create_player_card_embed(member, player_data)
                        
                        # Envia o card (sem botões) e salva o ID da mensagem
                        card_message = await card_channel.send(embed=card_embed)
                        await player_service.set_player_card_message_id(member.id, card_message.id)
                except Exception as e:
                    logger.error(f"Falha ao enviar e salvar o card de jogador para {member.display_name}: {e}")
        
        await interaction.followup.send("✅ Registro concluído! Seu card de apresentação foi postado.", ephemeral=True)

class RegistrationView(ui.View):
    def __init__(self):
        super().__init__(timeout=None)
    @ui.button(label="Registrar-se Agora", style=discord.ButtonStyle.success, custom_id="register_now_button", emoji="📝")
    async def register(self, interaction: discord.Interaction, button: ui.Button):
        await interaction.response.send_modal(RegistrationModal())