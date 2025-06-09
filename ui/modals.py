import discord
from discord import ui
import logging
import os

from database.player_service import PlayerService
# Importa a nova função de embed
from utils.embeds import create_player_card_embed

logger = logging.getLogger(__name__)

# Carrega o ID do canal de cards
try:
    PLAYER_CARD_CHANNEL_ID = int(os.getenv('PLAYER_CARD_CHANNEL_ID'))
except (TypeError, ValueError):
    PLAYER_CARD_CHANNEL_ID = 0

class RegistrationModal(ui.Modal, title="Formulário de Registro"):
    wr_nickname = ui.TextInput(label="Seu Nick no Wild Rift (ex: Nick#TAG)", required=True)
    wr_region = ui.TextInput(label="Sua região (ex: BR, LAS, NA)", required=True, max_length=5)
    preferred_roles = ui.TextInput(label="Suas rotas preferidas (separadas por vírgula)", style=discord.TextStyle.paragraph, required=True)

    async def on_submit(self, interaction: discord.Interaction):
        await interaction.response.defer(ephemeral=True)
        
        registration_cog = interaction.client.get_cog("RegistrationCog")
        if not registration_cog:
            return await interaction.followup.send("❌ Erro interno do bot.", ephemeral=True)
        
        player_service = registration_cog.player_service
        roles_list = [role.strip().capitalize() for role in self.preferred_roles.value.split(',')]
        
        await player_service.update_player_registration(
            member_id=interaction.user.id,
            nickname=self.wr_nickname.value,
            region=self.wr_region.value.upper(),
            roles=roles_list
        )
        
        # Lógica de atribuição de cargos (já existente)
        guild = interaction.guild
        member = interaction.user
        roles_to_add = [role for role_name in roles_list if (role := discord.utils.find(lambda r: r.name.lower() == role_name.lower(), guild.roles))]
        if roles_to_add:
            try:
                await member.add_roles(*roles_to_add, reason="Rotas definidas no registro.")
            except discord.Forbidden:
                logger.error(f"Sem permissão para adicionar cargos para {member.display_name}.")

        # --- NOVA LÓGICA PARA ENVIAR O CARD ---
        if PLAYER_CARD_CHANNEL_ID != 0:
            card_channel = interaction.guild.get_channel(PLAYER_CARD_CHANNEL_ID)
            if card_channel:
                try:
                    # Busca os dados mais recentes para garantir que tudo está atualizado
                    player_data = await player_service.get_player_by_id(member.id)
                    if player_data:
                        card_embed = await create_player_card_embed(member, player_data)
                        await card_channel.send(embed=card_embed)
                except Exception as e:
                    logger.error(f"Falha ao enviar o card de jogador para {member.display_name}: {e}")
            else:
                logger.warning(f"Canal de cards (ID: {PLAYER_CARD_CHANNEL_ID}) não encontrado.")
        # --- FIM DA NOVA LÓGICA ---
        
        await interaction.followup.send(
            "✅ Seu registro foi concluído e seus cargos de rota foram definidos! Um card de apresentação foi postado. Bem-vindo(a) à Arena!", 
            ephemeral=True
        )