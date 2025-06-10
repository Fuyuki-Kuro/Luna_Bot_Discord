import discord
from discord import ui
import logging
import os

from utils.embeds import create_player_card_embed
from database.player_service import PlayerService

logger = logging.getLogger(__name__)

try:
    PLAYER_CARD_CHANNEL_ID = int(os.getenv('PLAYER_CARD_CHANNEL_ID'))
    SERVER_ID = int(os.getenv('SERVER_ID'))
except (TypeError, ValueError):
    PLAYER_CARD_CHANNEL_ID = 0
    SERVER_ID = 0

class RegistrationModal(ui.Modal, title="Formulário de Registro"):
    # --- MUDANÇA AQUI: O construtor agora aceita dados existentes ---
    def __init__(self, existing_data: dict = None):
        super().__init__()
        
        # Usa os dados existentes para preencher os campos, ou deixa em branco se for um novo registro
        self.wr_nickname.default = existing_data.get('wr_nickname', '') if existing_data else ''
        self.wr_region.default = existing_data.get('wr_region', '') if existing_data else ''
        roles_list = existing_data.get('preferred_roles', []) if existing_data else []
        self.preferred_roles.default = ', '.join(roles_list)

    wr_nickname = ui.TextInput(label="Seu Nick no Wild Rift (ex: Nome#TAG)", required=True)
    wr_region = ui.TextInput(label="Sua região (ex: BR, LAS, NA)", required=True, max_length=5)
    preferred_roles = ui.TextInput(label="Suas rotas preferidas (separadas por vírgula)", style=discord.TextStyle.paragraph, required=True)

    async def on_submit(self, interaction: discord.Interaction):
        await interaction.response.defer(ephemeral=True)
        
        nickname_value = self.wr_nickname.value
        if '#' not in nickname_value or len(nickname_value.split('#')) != 2 or not nickname_value.split('#')[0] or not nickname_value.split('#')[1]:
            return await interaction.followup.send("❌ **Formato de Nick Inválido!** Use `Nome#TAG`.", ephemeral=True)
        
        registration_cog = interaction.client.get_cog("RegistrationCog")
        player_service = registration_cog.player_service
        
        roles_list = [role.strip().capitalize() for role in self.preferred_roles.value.split(',')]
        
        # Esta função agora serve tanto para criar quanto para atualizar
        await player_service.update_player_registration(
            member_id=interaction.user.id, nickname=nickname_value,
            region=self.wr_region.value.upper(), roles=roles_list
        )
        
        guild = interaction.client.get_guild(SERVER_ID)
        member = guild.get_member(interaction.user.id) if guild else None

        if guild and member:
            # Lógica para atualizar cargos: remove os antigos e adiciona os novos
            all_role_names = ["Top", "Jungle", "Mid", "ADC", "Support"]
            roles_to_remove = [role for role_name in all_role_names if (role := discord.utils.get(guild.roles, name=role_name)) and role in member.roles]
            if roles_to_remove:
                await member.remove_roles(*roles_to_remove, reason="Atualização de rotas de registro.")

            roles_to_add = [role for role_name in roles_list if (role := discord.utils.find(lambda r: r.name.lower() == role_name.lower(), guild.roles))]
            if roles_to_add:
                await member.add_roles(*roles_to_add, reason="Atualização de rotas de registro.")

        # Lógica para atualizar ou enviar o card do jogador
        if PLAYER_CARD_CHANNEL_ID != 0 and guild and member:
            card_channel = guild.get_channel(PLAYER_CARD_CHANNEL_ID)
            player_data = await player_service.get_player_by_id(member.id)
            if card_channel and player_data:
                card_embed = await create_player_card_embed(member, player_data)
                
                # Se o card já existe, edita. Se não, envia um novo.
                if card_message_id := player_data.get('player_card_message_id'):
                    try:
                        card_message = await card_channel.fetch_message(card_message_id)
                        await card_message.edit(embed=card_embed)
                    except discord.NotFound:
                        new_card_message = await card_channel.send(embed=card_embed)
                        await player_service.set_player_card_message_id(member.id, new_card_message.id)
                else:
                    new_card_message = await card_channel.send(embed=card_embed)
                    await player_service.set_player_card_message_id(member.id, new_card_message.id)
        
        await interaction.followup.send("✅ Seu registro foi atualizado com sucesso!", ephemeral=True)

class RegistrationView(ui.View):
    def __init__(self):
        super().__init__(timeout=None)
    @ui.button(label="Registrar-se Agora", style=discord.ButtonStyle.success, custom_id="register_now_button", emoji="📝")
    async def register(self, interaction: discord.Interaction, button: ui.Button):
        # A lógica para decidir se é um novo registro ou edição ficará no comando /registrar
        # Aqui, apenas abrimos o modal. A lógica de preenchimento será feita no comando.
        await interaction.response.send_modal(RegistrationModal())