import discord
from discord import app_commands, ui
from discord.ext import commands
import logging
import time
import asyncio
import os

from database.player_service import PlayerService
from database.duel_service import DuelService
from database.connection import get_db
from ui.duel_ui import DuelChallengeView, DuelPanelView
from utils.elo_calculator import calculate_elo
from utils.embeds import create_duel_result_embed, create_player_card_embed

logger = logging.getLogger(__name__)

try:
    SERVER_ID = int(os.getenv('SERVER_ID'))
    DUEL_HISTORY_CHANNEL_ID = int(os.getenv('DUEL_HISTORY_CHANNEL_ID'))
    PLAYER_CARD_CHANNEL_ID = int(os.getenv('PLAYER_CARD_CHANNEL_ID'))
except (TypeError, ValueError):
    logger.critical("ERRO CRÍTICO: IDs de canal não configurados no .env!")
    SERVER_ID, DUEL_HISTORY_CHANNEL_ID, PLAYER_CARD_CHANNEL_ID = 0, 0, 0

class DuelCog(commands.Cog):
    def __init__(self, bot: commands.Bot):
        self.bot = bot
        db = get_db()
        self.player_service = PlayerService(db.players)
        self.duel_service = DuelService(db.duels)
        
        self.duel_context_menu = app_commands.ContextMenu(
            name="Desafiar para Duelo",
            callback=self.challenge_duel,
        )
        self.bot.tree.add_command(self.duel_context_menu)
        logger.info("Cog de Duelos carregado e comando de menu de contexto registrado.")

    def cog_unload(self):
        self.bot.tree.remove_command(self.duel_context_menu.name, type=self.duel_context_menu.type)

    async def challenge_duel(self, interaction: discord.Interaction, target: discord.Member):
        challenger = interaction.user
        await interaction.response.defer(ephemeral=True)
        if challenger.id == target.id:
            return await interaction.followup.send("❌ Você não pode desafiar a si mesmo.", ephemeral=True)
        if target.bot:
            return await interaction.followup.send("❌ Você não pode desafiar um bot.", ephemeral=True)
        if await self.duel_service.get_active_duel_for_player(challenger.id) or await self.duel_service.get_active_duel_for_player(target.id):
            return await interaction.followup.send("❌ Um dos jogadores já está em um duelo ou tem um desafio pendente.", ephemeral=True)
        challenger_data = await self.player_service.get_player_by_id(challenger.id)
        target_data = await self.player_service.get_player_by_id(target.id)
        if not challenger_data or not target_data or not challenger_data.get('is_registered') or not target_data.get('is_registered'):
             return await interaction.followup.send("❌ Ambos os jogadores precisam estar registrados para duelar.", ephemeral=True)
        new_duel = await self.duel_service.create_duel(challenger.id, target.id, challenger_data['individual_elo_points'], target_data['individual_elo_points'])
        try:
            embed = discord.Embed(title="⚔️ Você foi Desafiado! ⚔️", description=f"**{challenger.display_name}** te desafiou para um duelo 1v1!", color=discord.Color.gold())
            embed.set_footer(text="Você tem 1 hora para responder.")
            await target.send(embed=embed, view=DuelChallengeView(duel_id=new_duel['_id']))
            await interaction.followup.send(f"✅ Desafio enviado para **{target.display_name}**!", ephemeral=True)
        except discord.Forbidden:
            await interaction.followup.send(f"❌ Não consegui enviar o desafio para **{target.display_name}**. Ele pode ter as DMs desabilitadas.", ephemeral=True)
            await self.duel_service.update_duel(new_duel['_id'], {"status": "cancelled"})
        except Exception as e:
            logger.error(f"Erro inesperado ao enviar DM de duelo: {e}")
            await interaction.followup.send("❌ Ocorreu um erro ao enviar o desafio.", ephemeral=True)

    @commands.Cog.listener("on_interaction")
    async def on_duel_interaction(self, interaction: discord.Interaction):
        if interaction.type != discord.InteractionType.component or not interaction.data.get("custom_id"):
            return
        custom_id = interaction.data["custom_id"]
        if not custom_id.startswith("duel_"):
            return
        try:
            _, action, duel_id = custom_id.split("_", 2)
        except ValueError:
            return logger.error(f"custom_id malformado recebido: {custom_id}")
        
        if action == "accept":
            await self.handle_duel_accept(interaction, duel_id)
        elif action == "decline":
            await self.handle_duel_decline(interaction, duel_id)
        elif action == "report":
            await self.handle_report_winner(interaction, duel_id)

    async def handle_duel_accept(self, interaction: discord.Interaction, duel_id: str):
        duel = await self.duel_service.get_duel_by_id(duel_id)
        if not duel or duel['status'] != 'pending' or interaction.user.id != duel['opponent_id']:
            return await interaction.response.send_message("❌ Este convite é inválido ou não é para você.", ephemeral=True, delete_after=10)
        await interaction.message.delete()
        await interaction.response.send_message(f"✅ Duelo aceito! Criando um canal privado...", ephemeral=True)
        guild = self.bot.get_guild(SERVER_ID)
        if not guild:
            return logger.error(f"Erro crítico: Servidor com ID {SERVER_ID} não encontrado.")
        challenger = guild.get_member(duel['challenger_id'])
        opponent = guild.get_member(duel['opponent_id'])
        if not challenger or not opponent:
            await self.duel_service.update_duel(duel_id, {"status": "cancelled"})
            return 
        overwrites = {guild.default_role: discord.PermissionOverwrite(read_messages=False), challenger: discord.PermissionOverwrite(read_messages=True), opponent: discord.PermissionOverwrite(read_messages=True), guild.me: discord.PermissionOverwrite(read_messages=True)}
        channel_name = f"⚔️-duelo-{challenger.name}-vs-{opponent.name}"
        try:
            channel = await guild.create_text_channel(name=channel_name[:100], overwrites=overwrites, reason=f"Duelo {duel_id}")
        except discord.Forbidden:
            return logger.error("Bot sem permissão de 'Gerenciar Canais'.")
        await self.duel_service.update_duel(duel_id, {"status": "in_progress", "channel_id": channel.id, "accepted_at": time.time()})
        panel_embed = discord.Embed(title="🔥 Painel de Duelo 🔥", description="O duelo começou! Que vença o melhor!", color=discord.Color.red())
        panel_embed.add_field(name="Participantes", value=f"{challenger.mention} vs {opponent.mention}")
        panel_embed.set_footer(text="Após a partida, um de vocês deve clicar no botão para declarar a vitória.")
        await channel.send(embed=panel_embed, view=DuelPanelView(duel_id))
    
    async def handle_duel_decline(self, interaction: discord.Interaction, duel_id: str):
        duel = await self.duel_service.get_duel_by_id(duel_id)
        if not duel or interaction.user.id != duel['opponent_id']:
            return await interaction.response.send_message("❌ Este convite não é para você.", ephemeral=True, delete_after=10)
        await self.duel_service.update_duel(duel_id, {"status": "cancelled"})
        challenger = self.bot.get_user(duel['challenger_id'])
        await interaction.message.delete()
        await interaction.response.send_message(f"Você recusou o desafio de {challenger.mention if challenger else 'um jogador'}.", ephemeral=True)

    async def handle_report_winner(self, interaction: discord.Interaction, duel_id: str):
        await interaction.response.defer()
        duel = await self.duel_service.get_duel_by_id(duel_id)
        if not duel or interaction.user.id not in [duel['challenger_id'], duel['opponent_id']] or duel['status'] != 'in_progress':
            return await interaction.followup.send("❌ Você não pode reportar o resultado deste duelo.", ephemeral=True)
        
        winner_id, loser_id = interaction.user.id, duel['opponent_id'] if interaction.user.id == duel['challenger_id'] else duel['challenger_id']
        
        winner_data = await self.player_service.get_player_by_id(winner_id)
        loser_data = await self.player_service.get_player_by_id(loser_id)
        winner_elo_before = winner_data['individual_elo_points']
        loser_elo_before = loser_data['individual_elo_points']
        
        K_FACTOR_NEW_PLAYER, K_FACTOR_ESTABLISHED = 40, 24
        winner_games_played = len(winner_data.get('individual_match_history', []))
        loser_games_played = len(loser_data.get('individual_match_history', []))
        
        winner_k = K_FACTOR_NEW_PLAYER if winner_games_played < 20 else K_FACTOR_ESTABLISHED
        loser_k = K_FACTOR_NEW_PLAYER if loser_games_played < 20 else K_FACTOR_ESTABLISHED
        
        logger.info(f"Cálculo de ELO para {winner_data['username']} (K={winner_k}) vs {loser_data['username']} (K={loser_k})")
        
        winner_points_change, loser_points_change = calculate_elo(winner_elo_before, loser_elo_before, winner_k, loser_k)
        
        winner_result = await self.player_service.update_player_after_duel(
            player_id=winner_id, 
            result="win",
            points_change=winner_points_change, 
            opponent_id=loser_id, 
            opponent_elo_before_match=loser_elo_before
        )
        await self.player_service.update_player_after_duel(
            player_id=loser_id, 
            result="loss",
            points_change=loser_points_change, 
            opponent_id=winner_id, 
            opponent_elo_before_match=winner_elo_before
        )
        
        final_winner_points_gain = winner_result.get("points", 0)
        
        updated_duel = await self.duel_service.update_duel(duel_id, {"status": "completed", "winner_id": winner_id, "loser_id": loser_id, "points_change": final_winner_points_gain, "completed_at": time.time()})
        
        guild = self.bot.get_guild(SERVER_ID)
        winner, loser = guild.get_member(winner_id), guild.get_member(loser_id)
        winner_new_data = await self.player_service.get_player_by_id(winner_id)
        loser_new_data = await self.player_service.get_player_by_id(loser_id)
        
        card_channel = guild.get_channel(PLAYER_CARD_CHANNEL_ID)
        if card_channel:
            if winner_new_data and winner_new_data.get('player_card_message_id'):
                try:
                    msg = await card_channel.fetch_message(winner_new_data['player_card_message_id'])
                    await msg.edit(embed=await create_player_card_embed(winner, winner_new_data))
                except Exception as e:
                    logger.warning(f"Não foi possível atualizar o card do vencedor {winner.display_name}: {e}")
            if loser_new_data and loser_new_data.get('player_card_message_id'):
                try:
                    msg = await card_channel.fetch_message(loser_new_data['player_card_message_id'])
                    await msg.edit(embed=await create_player_card_embed(loser, loser_new_data))
                except Exception as e:
                    logger.warning(f"Não foi possível atualizar o card do perdedor {loser.display_name}: {e}")
        
        history_channel = guild.get_channel(DUEL_HISTORY_CHANNEL_ID)
        if history_channel:
            history_embed = await create_duel_result_embed(winner, loser, updated_duel, winner_new_data['individual_elo_points'], loser_new_data['individual_elo_points'])
            await history_channel.send(embed=history_embed)
            
        description = f"**Vencedor:** {winner.mention}\n**Perdedor:** {loser.mention}\n\n**{winner.display_name}** ganhou **{final_winner_points_gain}** pontos de ELO!"
        win_streak_bonus = winner_result.get("bonus", 0)
        if win_streak_bonus > 0:
            description += f" (incluindo **+{win_streak_bonus}** de bônus por sequência de vitórias!)"
        result_embed = discord.Embed(title=f"🏆 Duelo Finalizado!", description=description, color=discord.Color.green())
        
        await interaction.followup.send(embed=result_embed)
        
        await interaction.message.edit(view=None)
        await interaction.channel.send("Este canal será arquivado em 1 minuto...")
        await asyncio.sleep(60)
        await interaction.channel.delete()

async def setup(bot: commands.Bot):
    await bot.add_cog(DuelCog(bot))