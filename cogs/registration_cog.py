import discord
from discord import app_commands
from discord.ext import commands, tasks
import logging
import os
import time
import asyncio

from database.player_service import PlayerService
from database.connection import get_db
from ui.registration_ui import RegistrationView 
from ui.player_card_ui import PlayerCardView

logger = logging.getLogger(__name__)

try:
    MAX_REMINDERS = int(os.getenv('MAX_REMINDERS_BEFORE_KICK', 3))
    REG_LOG_WEBHOOK_URL = os.getenv('REGISTRATION_LOG_WEBHOOK_URL')
    SERVER_ID = int(os.getenv('SERVER_ID'))
except (TypeError, ValueError):
    logger.critical("Variáveis de ambiente de registro não configuradas!")
    MAX_REMINDERS = 3
    REG_LOG_WEBHOOK_URL = None
    SERVER_ID = 0

class RegistrationCog(commands.Cog):
    ROLE_COLORS = {
        "Top": discord.Color.from_rgb(245, 66, 66),
        "Jungle": discord.Color.from_rgb(66, 245, 114),
        "Mid": discord.Color.from_rgb(141, 66, 245),
        "ADC": discord.Color.from_rgb(245, 234, 66),
        "Support": discord.Color.from_rgb(66, 215, 245)
    }

    def __init__(self, bot: commands.Bot):
        self.bot = bot
        db = get_db()
        self.player_service = PlayerService(db.players)
        
        self.bot.add_view(RegistrationView())
        self.bot.add_view(PlayerCardView())
        
        self.kick_unregistered_task.start()
        self.bot.loop.create_task(self.setup_roles_on_startup())
        logger.info("Cog de Registro Automático carregado e tarefas iniciadas.")

    def cog_unload(self):
        self.kick_unregistered_task.cancel()

    @commands.Cog.listener()
    async def on_member_join(self, member: discord.Member):
        if member.bot or member.guild.id != SERVER_ID: return
        await self.player_service.get_or_create_player(member)
        logger.info(f"Registro inicial criado para o novo membro: {member.display_name}")
        await asyncio.sleep(10)
        await self.send_registration_dm(member)

    @tasks.loop(hours=24)
    async def kick_unregistered_task(self):
        await self.bot.wait_until_ready()
        logger.info("[TAREFA] Iniciando verificação diária de registros...")
        if SERVER_ID == 0:
            return logger.error("[TAREFA] SERVER_ID não configurado.")
        guild = self.bot.get_guild(SERVER_ID)
        if not guild: return
        
        logger.info("[TAREFA] Sincronizando membros do servidor com o banco de dados...")
        for member in guild.members:
            if not member.bot:
                await self.player_service.get_or_create_player(member)
        
        unregistered_players = await self.player_service.get_unregistered_players()
        logger.info(f"[TAREFA] Encontrados {len(unregistered_players)} jogadores não registrados para verificar.")
        
        for player_data in unregistered_players:
            member = guild.get_member(player_data['_id'])
            if not member:
                await self.player_service.delete_player(player_data['_id'])
                continue
                
            last_sent = player_data.get('last_reminder_sent_at')
            if not last_sent or (time.time() - last_sent) > 82800:
                if player_data['registration_reminders_sent'] >= MAX_REMINDERS:
                    try:
                        await member.send("Você foi removido do servidor por não completar o registro a tempo.")
                        await member.kick(reason="Não completou o registro.")
                        await self.log_to_webhook(f"👢 Membro expulso: **{member.display_name}** (`{member.id}`)")
                        await self.player_service.delete_player(member.id)
                    except Exception as e:
                        logger.error(f"Falha ao expulsar {member.display_name}: {e}")
                else:
                    await self.send_registration_dm(member)

    async def send_registration_dm(self, member: discord.Member):
        player_data = await self.player_service.get_player_by_id(member.id)
        if not player_data: return
        
        reminders_sent = player_data.get('registration_reminders_sent', 0)
        
        if reminders_sent == 0:
            title = "👋 Bem-vindo(a) à Arena!"
            description = "Para participar de todos os nossos eventos e ter acesso completo ao servidor, por favor, complete seu registro clicando no botão abaixo."
            color = discord.Color.blue()
            footer = "O registro é rápido e essencial para a comunidade."
        else:
            title = f"OPA, CAMPEÃO! CUIDADO COM O GANK! (Aviso {reminders_sent + 1}/{MAX_REMINDERS})"
            description = "O Barão tá quase nascendo e você ainda não se registrou pra lutar com a gente! Não dê mole, clique no botão abaixo pra não tomar um gank da administração e ser kickado.\n\nFalta pouco pra virar lenda!"
            color = discord.Color.orange()
            footer = "Manter o registro em dia é a primeira call pra vitória!"
        
        embed = discord.Embed(title=title, description=description, color=color)
        embed.set_footer(text=footer)
        
        try:
            await member.send(embed=embed, view=RegistrationView())
            await self.player_service.increment_reminder(member.id)
            logger.info(f"DM de registro (Lembrete #{reminders_sent + 1}) enviada para {member.display_name}")
        except discord.Forbidden:
            logger.warning(f"Não foi possível enviar DM para {member.name}.")

    async def setup_roles_on_startup(self):
        await self.bot.wait_until_ready()
        if SERVER_ID == 0: return
        
        guild = self.bot.get_guild(SERVER_ID)
        if not guild: return
        
        existing_roles = {role.name for role in guild.roles}
        roles_to_create = ["Top", "Jungle", "Mid", "ADC", "Support"]
        
        logger.info("Verificando a existência dos cargos de rota...")
        for role_name in roles_to_create:
            if role_name not in existing_roles:
                try:
                    role_color = self.ROLE_COLORS.get(role_name, discord.Color.default())
                    await guild.create_role(name=role_name, colour=role_color, reason="Criação automática de cargo de rota.")
                    logger.info(f"Cargo '{role_name}' criado com sucesso.")
                except discord.Forbidden:
                    logger.error(f"Sem permissão para criar o cargo '{role_name}'. Verifique a permissão 'Gerenciar Cargos'.")
                    break
                except Exception as e:
                    logger.error(f"Erro ao criar o cargo '{role_name}': {e}")

    async def log_to_webhook(self, message: str):
        if REG_LOG_WEBHOOK_URL:
            try:
                webhook = discord.Webhook.from_url(REG_LOG_WEBHOOK_URL, client=self.bot)
                await webhook.send(message)
            except Exception as e:
                logger.error(f"Falha ao enviar log para webhook: {e}")

async def setup(bot: commands.Bot):
    await bot.add_cog(RegistrationCog(bot))