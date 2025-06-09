import discord
from discord.ext import commands
import logging
import os

# Importa os mapas de ELO para montar a tabela de progressão
from database.models import ELO_TIERS_MAP, ELO_EMOJI_MAP

logger = logging.getLogger(__name__)

# --- Configuração ---
try:
    GUIDE_CHANNEL_ID = int(os.getenv('GUIDE_CHANNEL_ID'))
except (TypeError, ValueError):
    logger.critical("ERRO CRÍTICO: GUIDE_CHANNEL_ID não está configurado ou é inválido no .env!")
    GUIDE_CHANNEL_ID = 0

class GuideCog(commands.Cog):
    """
    Este Cog é responsável por postar e manter uma mensagem guia
    explicando o funcionamento dos sistemas do bot.
    """
    def __init__(self, bot: commands.Bot):
        self.bot = bot
        # Agenda a tarefa de postagem para rodar quando o bot iniciar
        self.bot.loop.create_task(self.post_guide_on_startup())
        logger.info("Cog do Guia carregado.")

    def _create_guide_embed(self) -> discord.Embed:
        """Cria e retorna o embed com o guia completo do sistema de duelos e ranking."""
        
        embed = discord.Embed(
            title="📜 Guia da Arena: Duelos e Sistema de Ranking",
            description="Boas-vindas, combatente! Este guia explica como nosso sistema de duelos e ranking funciona.",
            color=discord.Color.from_rgb(255, 215, 0) # Dourado
        )
        
        # Seção 1: Como Funciona o Duelo
        embed.add_field(
            name="1️⃣ Como Desafiar um Oponente",
            value=(
                "A forma mais fácil de desafiar alguém é através do menu de contexto:\n"
                "∙ **No PC:** **Clique com o botão direito** no nome do usuário.\n"
                "∙ **No Celular:** **Toque e segure** o dedo sobre o nome do usuário.\n\n"
                "No menu que aparecer, vá em **`Apps`** e selecione **`Desafiar para Duelo`**. Seu oponente receberá o convite por Mensagem Direta (DM)."
            ),
            inline=False
        )
        
        embed.add_field(
            name="2️⃣ A Partida",
            value=(
                "Se o desafio for aceito, um canal de texto privado será criado para os dois duelistas. Usem este canal para combinar as regras (ex: X1 no Howling Abyss, primeiro a destruir a torre, etc.).\n"
                "Após o fim da partida, o vencedor deve retornar a este canal e clicar no botão **`Declarar Vitória`** para registrar o resultado."
            ),
            inline=False
        )

        # Seção 2: O Sistema de ELO
        embed.add_field(
            name="🏆 O Cálculo de ELO Justo",
            value=(
                "Nosso sistema de ELO é dinâmico para garantir partidas justas e uma progressão recompensadora.\n"
                "∙ **Vitórias contra oponentes de ELO mais alto rendem mais pontos.**\n"
                "∙ **Derrotas para oponentes de ELO mais baixo custam mais pontos.**\n\n"
                "Além disso, o sistema se adapta à sua experiência:\n"
                "∙ **Jogadores Novos (< 20 partidas):** Suas partidas têm um 'Fator K' maior, o que significa que seus ganhos e perdas de ELO são mais acentuados. Isso ajuda você a encontrar seu ranking verdadeiro mais rápido.\n"
                "∙ **Jogadores Experientes (20+ partidas):** O 'Fator K' é menor, tornando seu ELO mais estável e refletindo sua consistência."
            ),
            inline=False
        )

        # Seção 3: Tabela de Elos
        elo_table_part1 = []
        elo_table_part2 = []
        
        sorted_elos = sorted(ELO_TIERS_MAP.items(), key=lambda item: item[1])
        midpoint = len(sorted_elos) // 2
        
        for i, (rank_full, min_points) in enumerate(sorted_elos):
            elo_name = rank_full.split(" ")[0]
            elo_emoji = ELO_EMOJI_MAP.get(elo_name, "⚫")
            line = f"{elo_emoji} **{rank_full}:** `{min_points}` Pontos"
            if i < midpoint:
                elo_table_part1.append(line)
            else:
                elo_table_part2.append(line)
            
        embed.add_field(
            name="📈 Progressão de Elo (Elos Iniciais)",
            value="\n".join(elo_table_part1),
            inline=True
        )
        embed.add_field(
            name="📈 Progressão de Elo (Elos Avançados)",
            value="\n".join(elo_table_part2),
            inline=True
        )
        
        embed.set_footer(text="Bons duelos e que vença o melhor!")
        
        return embed

    async def post_guide_on_startup(self):
        """Verifica se o guia já existe no canal e o posta ou edita se necessário."""
        await self.bot.wait_until_ready()
        
        if GUIDE_CHANNEL_ID == 0:
            logger.warning("GUIDE_CHANNEL_ID não definido no .env. O guia não será postado.")
            return
            
        channel = self.bot.get_channel(GUIDE_CHANNEL_ID)
        if not channel:
            logger.error(f"Não foi possível encontrar o canal do guia com o ID {GUIDE_CHANNEL_ID}.")
            return

        logger.info(f"Verificando a existência do guia no canal '{channel.name}'...")
        
        guide_embed = self._create_guide_embed()
        
        # Procura por uma mensagem do bot que já seja o guia
        async for message in channel.history(limit=10):
            if message.author == self.bot.user and message.embeds and message.embeds[0].title == guide_embed.title:
                # Se encontrar, edita a mensagem para garantir que está sempre atualizada
                await message.edit(embed=guide_embed)
                logger.info("Guia já existe e foi atualizado no canal.")
                return

        # Se não encontrou, posta um novo
        logger.info("Guia não encontrado. Postando um novo...")
        await channel.send(embed=guide_embed)
        logger.info(f"Guia postado com sucesso no canal '{channel.name}'.")

async def setup(bot: commands.Bot):
    await bot.add_cog(GuideCog(bot))