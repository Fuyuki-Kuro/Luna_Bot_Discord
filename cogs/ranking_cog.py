import discord
from discord.ext import commands, tasks
import logging
import os

# Importa os módulos necessários
from database.player_service import PlayerService
from database.connection import get_db
from database.models import ELO_EMOJI_MAP

logger = logging.getLogger(__name__)

# Carrega a configuração do canal
try:
    RANKING_CHANNEL_ID = int(os.getenv('RANKING_CHANNEL_ID'))
except (TypeError, ValueError):
    logger.critical("ERRO CRÍTICO: RANKING_CHANNEL_ID não está configurado ou é inválido no .env!")
    RANKING_CHANNEL_ID = 0

class RankingCog(commands.Cog):
    """
    Este Cog gerencia a postagem e atualização automática do placar de líderes.
    """
    def __init__(self, bot: commands.Bot):
        self.bot = bot
        db = get_db()
        self.player_service = PlayerService(db.players)
        self.ranking_message_id = None # Armazenará o ID da mensagem do ranking
        
        # Inicia a tarefa em loop para rodar a cada 24 horas
        self.update_leaderboard.start()
        logger.info("Cog de Ranking carregado e tarefa diária iniciada.")

    def cog_unload(self):
        """Garante que a tarefa seja cancelada se o cog for descarregado."""
        self.update_leaderboard.cancel()

    @tasks.loop(hours=24)
    async def update_leaderboard(self):
        """A tarefa que busca os dados e atualiza a mensagem do ranking."""
        logger.info("Iniciando atualização diária do placar de líderes...")
        
        channel = self.bot.get_channel(RANKING_CHANNEL_ID)
        if not channel:
            logger.error(f"Canal de ranking com ID {RANKING_CHANNEL_ID} não encontrado.")
            return

        top_players = await self.player_service.get_leaderboard_players(limit=10)

        if not top_players:
            logger.info("Nenhum jogador registrado encontrado para o ranking.")
            return

        # Monta o embed com os dados mais recentes
        embed = self._create_leaderboard_embed(top_players)

        # Lógica para editar a mensagem antiga ou postar uma nova
        ranking_message = await self.get_ranking_message(channel)
        
        if ranking_message:
            try:
                await ranking_message.edit(embed=embed)
                logger.info("Placar de líderes atualizado com sucesso (mensagem editada).")
            except discord.NotFound:
                logger.warning("Mensagem de ranking anterior não encontrada. Postando uma nova.")
                new_message = await channel.send(embed=embed)
                self.ranking_message_id = new_message.id
        else:
            new_message = await channel.send(embed=embed)
            self.ranking_message_id = new_message.id
            logger.info("Placar de líderes postado com sucesso (nova mensagem).")

    @update_leaderboard.before_loop
    async def before_update_leaderboard(self):
        """Espera o bot estar pronto antes de iniciar o loop."""
        await self.bot.wait_until_ready()

    def _create_leaderboard_embed(self, top_players) -> discord.Embed:
        """Função auxiliar para criar o embed do ranking."""
        embed = discord.Embed(
            title="🏆 Placar de Líderes da Arena 🏆",
            description="Os 10 melhores duelistas do servidor, atualizado diariamente.",
            color=discord.Color.gold()
        )
        rank_emojis = {1: "🥇", 2: "🥈", 3: "🥉"}
        leaderboard_lines = []

        for i, player_data in enumerate(top_players, 1):
            user = self.bot.get_user(player_data['_id'])
            user_name = user.display_name if user else player_data.get('username', 'Jogador Desconhecido')
            
            rank_icon = rank_emojis.get(i, f"**{i}.**")
            elo_str = player_data.get('individual_current_elo', '')
            elo_emoji = ELO_EMOJI_MAP.get(elo_str, '⚫')
            
            line = (
                f"{rank_icon} **{user_name}**\n"
                f"> {elo_emoji} {elo_str} {player_data.get('individual_current_division', '')} - `{player_data['individual_elo_points']}` Pontos"
            )
            leaderboard_lines.append(line)
        
        embed.description = "\n\n".join(leaderboard_lines)
        embed.set_footer(text=f"Atualizado em: {discord.utils.format_dt(discord.utils.utcnow(), style='f')}")
        return embed
        
    async def get_ranking_message(self, channel: discord.TextChannel) -> discord.Message | None:
        """Busca a mensagem do ranking no canal."""
        # Se já temos o ID em memória, tenta buscá-lo
        if self.ranking_message_id:
            try:
                return await channel.fetch_message(self.ranking_message_id)
            except (discord.NotFound, discord.Forbidden):
                pass
        
        # Se não, procura por uma mensagem do bot que seja o ranking
        async for message in channel.history(limit=50):
            if message.author == self.bot.user and message.embeds:
                if message.embeds[0].title == "🏆 Placar de Líderes da Arena 🏆":
                    self.ranking_message_id = message.id
                    return message
        return None

async def setup(bot: commands.Bot):
    await bot.add_cog(RankingCog(bot))