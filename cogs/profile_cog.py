import discord
from discord import app_commands
from discord.ext import commands
import logging
from typing import Optional

# Importa os componentes necessários
from database.player_service import PlayerService
from database.connection import get_db
from utils.embeds import create_profile_embed

logger = logging.getLogger(__name__)

class ProfileCog(commands.Cog):
    def __init__(self, bot: commands.Bot):
        self.bot = bot
        db = get_db()
        self.player_service = PlayerService(db.players)
        logger.info("Cog de Perfil carregado.")

    @app_commands.command(name="perfil", description="Exibe o perfil de um jogador da Arena.")
    @app_commands.describe(usuario="O usuário do qual você quer ver o perfil (deixe em branco para ver o seu).")
    async def profile(self, interaction: discord.Interaction, usuario: Optional[discord.Member] = None):
        """Exibe o perfil do autor da interação ou do membro mencionado."""
        
        # Define o alvo do comando: o usuário mencionado ou quem executou o comando
        target_member = usuario or interaction.user
        
        await interaction.response.defer()
        
        # Busca os dados do jogador no banco
        player_data = await self.player_service.get_player_by_id(target_member.id)
        
        if not player_data or not player_data.get('is_registered'):
            return await interaction.followup.send(f"❌ O usuário **{target_member.display_name}** não possui um registro na Arena.", ephemeral=True)

        # Cria o embed do perfil usando nossa nova função
        profile_embed = await create_profile_embed(target_member, player_data)
        
        await interaction.followup.send(embed=profile_embed)


async def setup(bot: commands.Bot):
    await bot.add_cog(ProfileCog(bot))