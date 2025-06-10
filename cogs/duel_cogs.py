import discord
from discord import app_commands, ui
from discord.ext import commands
import logging
import time
import asyncio
import os
from typing import Any, Dict

# Importa todos os nossos módulos auxiliares
from database.player_service import PlayerService
from database.duel_service import DuelService
from database.connection import get_db
from ui.duel_ui import DuelChallengeView, DuelPanelView, DisputeDecisionView
from utils.elo_calculator import calculate_elo
from utils.embeds import create_duel_result_embed, create_player_card_embed

logger = logging.getLogger(__name__)

# Carrega as configurações do .env
try:
    SERVER_ID = int(os.getenv('SERVER_ID'))
    DUEL_HISTORY_CHANNEL_ID = int(os.getenv('DUEL_HISTORY_CHANNEL_ID'))
    PLAYER_CARD_CHANNEL_ID = int(os.getenv('PLAYER_CARD_CHANNEL_ID'))
    MOD_ROLE_ID = int(os.getenv('MOD_ROLE_ID'))
except (TypeError, ValueError):
    logger.critical("ERRO CRÍTICO: IDs de canal ou de cargo não configurados no .env!")
    SERVER_ID, DUEL_HISTORY_CHANNEL_ID, PLAYER_CARD_CHANNEL_ID, MOD_ROLE_ID = 0, 0, 0, 0

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
        
        self.bot.add_view(DisputeDecisionView(duel_data={"_id":0, "challenger_id":0, "opponent_id":0}))
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

    @commands.Cog.listener("on_message")
    async def on_duel_screenshot(self, message: discord.Message):
        if message.author.bot or not message.guild or not message.attachments: return
        duel = await self.duel_service.collection.find_one({"channel_id": message.channel.id, "status": "awaiting_screenshot"})
        if not duel: return
        if message.author.id == duel.get('reported_winner_id'):
            screenshot = message.attachments[0]
            if not screenshot.content_type.startswith("image/"): return
            logger.info(f"Screenshot recebido de {message.author.display_name} para o duelo {duel['_id']}")
            await self.duel_service.update_duel(duel['_id'], {"status": "awaiting_confirmation", "screenshot_url": screenshot.url})
            updated_duel = await self.duel_service.get_duel_by_id(duel['_id'])
            opponent_id = duel['challenger_id'] if message.author.id == duel['opponent_id'] else duel['opponent_id']
            opponent = message.guild.get_member(opponent_id)
            try:
                if panel_message_id := duel.get('panel_message_id'):
                    panel_message = await message.channel.fetch_message(panel_message_id)
                    await panel_message.edit(content=f"{opponent.mention}, seu oponente reportou vitória com a evidência acima. **Confirme ou dispute o resultado.**", view=DuelPanelView(updated_duel))
                if prompt_message_id := duel.get('prompt_message_id'):
                    prompt_msg = await message.channel.fetch_message(prompt_message_id)
                    await prompt_msg.delete()
                await message.add_reaction("✅")
            except (discord.NotFound, discord.Forbidden) as e:
                logger.error(f"Não foi possível encontrar ou editar a mensagem do painel/prompt de duelo: {e}")

    @commands.Cog.listener("on_interaction")
    async def on_duel_interaction(self, interaction: discord.Interaction):
        if interaction.type != discord.InteractionType.component or not interaction.data.get("custom_id"): return
        custom_id = interaction.data["custom_id"]
        if not custom_id.startswith("duel_"): return
        try:
            parts = custom_id.split("_")
            action = parts[1]
            duel_id = parts[2]
            winner_id = int(parts[3]) if len(parts) > 3 else None
        except (ValueError, IndexError):
            return logger.error(f"custom_id malformado recebido: {custom_id}")
        if action == "accept": await self.handle_duel_accept(interaction, duel_id)
        elif action == "decline": await self.handle_duel_decline(interaction, duel_id)
        elif action == "report": await self.handle_report_winner(interaction, duel_id)
        elif action == "confirm": await self.handle_confirm_defeat(interaction, duel_id)
        elif action == "dispute": await self.handle_dispute(interaction, duel_id)
        elif action == "modwin": await self.handle_mod_decision(interaction, duel_id, winner_id)

    async def handle_duel_accept(self, interaction: discord.Interaction, duel_id: str):
        duel = await self.duel_service.get_duel_by_id(duel_id)
        if not duel or duel['status'] != 'pending' or interaction.user.id != duel['opponent_id']:
            return await interaction.response.send_message("❌ Este convite é inválido ou não é para você.", ephemeral=True, delete_after=10)
        await interaction.message.delete()
        await interaction.response.send_message(f"✅ Duelo aceito! Criando uma área privada para o confronto...", ephemeral=True)
        server_id = int(os.getenv('SERVER_ID'))
        guild = self.bot.get_guild(server_id)
        if not guild: return logger.error(f"Erro crítico: Servidor com ID {server_id} não encontrado.")
        challenger = guild.get_member(duel['challenger_id'])
        opponent = guild.get_member(duel['opponent_id'])
        if not challenger or not opponent:
            await self.duel_service.update_duel(duel_id, {"status": "cancelled"})
            return 
        overwrites = {guild.default_role: discord.PermissionOverwrite(read_messages=False, connect=False), challenger: discord.PermissionOverwrite(read_messages=True, connect=True, speak=True), opponent: discord.PermissionOverwrite(read_messages=True, connect=True, speak=True), guild.me: discord.PermissionOverwrite(read_messages=True, manage_channels=True)}
        try:
            category_name = f"⚔️ Duelo: {challenger.name} vs {opponent.name}"
            category = await guild.create_category(name=category_name[:100], overwrites=overwrites, reason=f"Duelo {duel_id}")
            text_channel = await category.create_text_channel(name="💬-chat-do-duelo")
            await category.create_voice_channel(name="🔊 Call do Duelo")
        except discord.Forbidden:
            return logger.error("Bot sem permissão de 'Gerenciar Canais' para criar a categoria/canais de duelo.")
        await self.duel_service.update_duel(duel_id, {"status": "in_progress", "channel_id": text_channel.id, "accepted_at": time.time()})
        panel_embed = discord.Embed(title="🔥 Painel de Duelo 🔥", description=f"O duelo entre {challenger.mention} e {opponent.mention} começou!\nQue vença o melhor!", color=discord.Color.red())
        panel_embed.set_footer(text="Após a partida, o vencedor deve clicar no botão para reportar o resultado.")
        duel_doc_for_panel = await self.duel_service.get_duel_by_id(duel_id)
        await text_channel.send(embed=panel_embed, view=DuelPanelView(duel_doc_for_panel))
    
    async def handle_duel_decline(self, interaction: discord.Interaction, duel_id: str):
        duel = await self.duel_service.get_duel_by_id(duel_id)
        if not duel or interaction.user.id != duel['opponent_id']:
            return await interaction.response.send_message("❌ Este convite não é para você.", ephemeral=True, delete_after=10)
        await self.duel_service.update_duel(duel_id, {"status": "cancelled"})
        challenger = self.bot.get_user(duel['challenger_id'])
        await interaction.message.edit(content=f"Você recusou o desafio de {challenger.mention if challenger else 'um jogador'}.", view=None)

    async def handle_report_winner(self, interaction: discord.Interaction, duel_id: str):
        duel = await self.duel_service.get_duel_by_id(duel_id)
        if not duel or interaction.user.id not in [duel['challenger_id'], duel['opponent_id']] or duel['status'] != 'in_progress':
            return await interaction.response.send_message("❌ Você não pode reportar este resultado.", ephemeral=True)
        await self.duel_service.update_duel(duel_id, {"status": "awaiting_screenshot", "reported_winner_id": interaction.user.id, "panel_message_id": interaction.message.id})
        await interaction.response.edit_message(view=None)
        prompt_message = await interaction.channel.send(f"📸 {interaction.user.mention}, por favor, envie o **screenshot da tela de vitória** para validar o resultado. Você tem 2 minutos.")
        await self.duel_service.update_duel(duel_id, {"prompt_message_id": prompt_message.id})

    async def handle_confirm_defeat(self, interaction: discord.Interaction, duel_id: str):
        await interaction.response.defer()
        duel = await self.duel_service.get_duel_by_id(duel_id)
        reported_winner_id = duel.get('reported_winner_id')
        if not duel or duel['status'] != 'awaiting_confirmation' or interaction.user.id == reported_winner_id:
            return await interaction.followup.send("❌ Você não pode confirmar este resultado.", ephemeral=True)
        winner_id, loser_id = reported_winner_id, interaction.user.id
        await self.finalize_duel(interaction, duel, winner_id, loser_id)

    @app_commands.checks.has_permissions(manage_messages=True)
    async def handle_mod_decision(self, interaction: discord.Interaction, duel_id: str, winner_id: int):
        await interaction.response.defer()
        duel = await self.duel_service.get_duel_by_id(duel_id)
        if not duel or duel['status'] != 'disputed':
            return await interaction.followup.send("❌ Este duelo não está mais aguardando uma decisão.", ephemeral=True)
        loser_id = duel['opponent_id'] if winner_id == duel['challenger_id'] else duel['challenger_id']
        duel_channel = self.bot.get_channel(duel['channel_id'])
        await self.finalize_duel(interaction, duel, winner_id, loser_id, duel_channel=duel_channel)

    async def handle_dispute(self, interaction: discord.Interaction, duel_id: str):
        await interaction.response.defer()
        duel = await self.duel_service.get_duel_by_id(duel_id)
        if not duel: return
        await self.duel_service.update_duel(duel_id, {"status": "disputed"})
        mod_channel_id = int(os.getenv('MOD_CHANNEL_ID', 0))
        mod_role = interaction.guild.get_role(MOD_ROLE_ID)
        mod_ping = f"{mod_role.mention}, uma disputa foi aberta!" if mod_role else "**Atenção, @Moderadores!**"
        challenger = interaction.guild.get_member(duel['challenger_id'])
        opponent = interaction.guild.get_member(duel['opponent_id'])
        reported_winner = interaction.guild.get_member(duel['reported_winner_id'])
        dispute_embed = discord.Embed(title=f"❗ Disputa de Duelo: {challenger.display_name} vs {opponent.display_name}", description=f"O resultado reportado por {reported_winner.mention} foi disputado por {interaction.user.mention}.", color=discord.Color.yellow())
        if screenshot_url := duel.get('screenshot_url'):
            dispute_embed.set_image(url=screenshot_url)
        dispute_embed.set_footer(text=f"ID do Duelo: {duel_id}")
        mod_channel = interaction.guild.get_channel(mod_channel_id)
        if mod_channel:
            mod_panel_embed = discord.Embed(title="Painel de Moderação", description="Selecione o vencedor do duelo abaixo para finalizar a partida.", color=discord.Color.orange())
            await mod_channel.send(content=mod_ping, embed=dispute_embed)
            await mod_channel.send(embed=mod_panel_embed, view=DisputeDecisionView(duel))
        await interaction.message.edit(content="❗ **Disputa registrada!** A moderação foi notificada e irá analisar o caso. Este canal está agora trancado.", embed=None, view=None)

    async def finalize_duel(self, interaction: discord.Interaction, duel: Dict[str, Any], winner_id: int, loser_id: int, duel_channel: discord.TextChannel = None):
        winner_data, loser_data = await self.player_service.get_player_by_id(winner_id), await self.player_service.get_player_by_id(loser_id)
        winner_elo_before, loser_elo_before = winner_data['individual_elo_points'], loser_data['individual_elo_points']
        K_FACTOR_NEW_PLAYER, K_FACTOR_ESTABLISHED = 40, 24
        winner_k = K_FACTOR_NEW_PLAYER if len(winner_data.get('individual_match_history', [])) < 20 else K_FACTOR_ESTABLISHED
        loser_k = K_FACTOR_NEW_PLAYER if len(loser_data.get('individual_match_history', [])) < 20 else K_FACTOR_ESTABLISHED
        winner_points_change, loser_points_change = calculate_elo(winner_elo_before, loser_elo_before, winner_k, loser_k)
        winner_result = await self.player_service.update_player_after_duel(winner_id, "win", winner_points_change, loser_id, loser_elo_before)
        await self.player_service.update_player_after_duel(loser_id, "loss", loser_points_change, winner_id, winner_elo_before)
        final_winner_points_gain = winner_result.get("points", 0)
        updated_duel = await self.duel_service.update_duel(duel['_id'], {"status": "completed", "winner_id": winner_id, "loser_id": loser_id, "points_change": final_winner_points_gain, "completed_at": time.time()})
        
        server_id = int(os.getenv('SERVER_ID'))
        player_card_channel_id = int(os.getenv('PLAYER_CARD_CHANNEL_ID'))
        duel_history_channel_id = int(os.getenv('DUEL_HISTORY_CHANNEL_ID'))
        guild = self.bot.get_guild(server_id)
        winner, loser = guild.get_member(winner_id), guild.get_member(loser_id)
        winner_new_data, loser_new_data = await self.player_service.get_player_by_id(winner_id), await self.player_service.get_player_by_id(loser_id)
        
        card_channel = guild.get_channel(player_card_channel_id)
        if card_channel:
            if winner_new_data and (msg_id := winner_new_data.get('player_card_message_id')) and (msg := await self.safe_fetch_message(card_channel, msg_id)):
                await msg.edit(embed=await create_player_card_embed(winner, winner_new_data))
            if loser_new_data and (msg_id := loser_new_data.get('player_card_message_id')) and (msg := await self.safe_fetch_message(card_channel, msg_id)):
                await msg.edit(embed=await create_player_card_embed(loser, loser_new_data))
        
        history_channel = guild.get_channel(duel_history_channel_id)
        if history_channel:
            history_embed = await create_duel_result_embed(winner, loser, updated_duel, winner_new_data['individual_elo_points'], loser_new_data['individual_elo_points'])
            await history_channel.send(embed=history_embed)
            
        description = f"**Vencedor:** {winner.mention}\n**Perdedor:** {loser.mention}\n\n**{winner.display_name}** ganhou **{final_winner_points_gain}** pontos de ELO!"
        if winner_result.get("bonus", 0) > 0:
            description += f" (incluindo **+{winner_result['bonus']}** de bônus por sequência de vitórias!)"
        result_embed = discord.Embed(title=f"🏆 Duelo Finalizado!", description=description, color=discord.Color.green())
        
        channel_to_clean = duel_channel or interaction.channel
        
        if interaction.response.is_done():
            await interaction.followup.send(embed=result_embed)
        else:
            await interaction.response.send_message(embed=result_embed)
        
        await interaction.message.edit(view=None)
        await channel_to_clean.send("Esta categoria e seus canais serão deletados em 30 segundos...")
        await asyncio.sleep(30)
        
        if category := channel_to_clean.category:
            for channel in category.channels:
                try: await channel.delete(reason="Duelo finalizado.")
                except Exception as e: logger.error(f"Não foi possível deletar o canal {channel.name}: {e}")
            try: await category.delete(reason="Duelo finalizado.")
            except Exception as e: logger.error(f"Não foi possível deletar a categoria {category.name}: {e}")
        else:
             await channel_to_clean.delete(reason="Duelo finalizado.")
        
    async def safe_fetch_message(self, channel: discord.TextChannel, message_id: int):
        try:
            return await channel.fetch_message(message_id)
        except (discord.NotFound, discord.Forbidden):
            return None

async def setup(bot: commands.Bot):
    await bot.add_cog(DuelCog(bot))