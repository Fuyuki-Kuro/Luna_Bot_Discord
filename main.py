import discord
from discord.ext import commands
import os
from dotenv import load_dotenv
import asyncio
import logging

# Configurações de Logs para o bot Discord
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger('discord')

# Carrega as ariáveis de ambiente do arquivo .env
load_dotenv()
DISCORD_BOT_TOKEN = os.getenv('BOT_DICORD_TOKEN')
MONGO_URI=str(os.getenv('MONGO_URI_NEW'))
BOT_PREFIX=os.getenv('BOT_PREFIX')

# importa a função de conexão do banco de dados
from database.connection import connect_db, close_db

# Configura as Intents do Discord
intents = discord.Intents.default()
intents.members = True          # Garante que a intent SERVER MEMBERS INTENT seja solicitada
intents.message_content = True  # Garante que a intent MESSAGE CONTENT INTENT seja solicitada
intents.guilds = True           # Já inclui acesso básico a guildas
intents.presences = True   

# Inicializa o cliente do bot
bot = commands.Bot(
    command_prefix=BOT_PREFIX,
    intents=intents,
    member_cache_flags=discord.MemberCacheFlags.all() # <-- ESTA LINHA É CRÍTICA!
)

@bot.event
async def on_ready():
    """Evento disparado quando o bot está pronto e connectado ao Discord"""
    logger.info(f'Logged in as {bot.user.name} (ID: {bot.user.id})')
    logger.info(f'Prefix commands: {BOT_PREFIX}')
    logger.info('Conectando ao MongoDB...')
    try:
        await connect_db(MONGO_URI, 'Arena')
        logger.info('Conectado ao MongoDB!')
    except Exception as e:
        logger.error(f'Erro ao conectar ao MongoDB: {e}')
        await close_db()
        return
    
    await load_cogs()
    logger.info('Todos os cogs foram carregados com sucesso')
    logger.info('Bot pronto para uso!')

@bot.event
async def on_disconnect():
    """Evento disparado quando o bot é desconectado do Discord"""
    logger.info('Bot desconectado do Discord. Fechando conexão com MongoDB')
    await close_db()

async def load_cogs():
    """Carrega todos os cogs do diretório 'cogs'"""
    for filename in os.listdir('./cogs'):
        if filename.endswith('.py') and not filename.startswith('__'):
            try:
                await bot.load_extension(f'cogs.{filename[:-3]}')
                logger.info(f'Cog {filename[:-3]} carregado com sucesso')
            except Exception as e:
                logger.info(f'Falha ao carregar cog "{filename[:-3]}": {e}')

@bot.command()
@commands.is_owner()
async def reload(ctx: commands.Context, cog_name: str = None):
    """
    Recarrega um cog específico ou todos os cogs.
    Uso: /reload [nome_do_cog]
    """
    if cog_name:
        try:
            await bot.reload_extension(f'cogs.{cog_name}')
            await ctx.send(f'Cog {cog_name} recarregado com sucesso')
            logger.info(f'Cog {cog_name} recarregado com sucesso')
        except commands.ExtensionNotLoaded:
            await ctx.send(f'Cog {cog_name} não está carregado')
            logger.info(f'Cog {cog_name} não está carregado')
        except Exception as e:
            await ctx.send(f'Erro ao recarregar cog {cog_name}: {e}')
    
    else:
        # Recarregar todos os cogs
        for filename in os.listdir('./cogs'):
            if filename.endswith('.py') and not filename.startswith('__'):
                try:
                    await bot.reload_extension(f'cogs.{filename[:-3]}')
                    logger.info(f'Cog {filename[:-3]} recarregado com sucesso')
                except Exception as e:
                    logger.info(f'Falha ao recarregar cog "{filename[:-3]}": {e}')
        await ctx.send('Todos os cogs foram recarregados com sucesso')

@bot.command()
@commands.is_owner()
async def sync(ctx: commands.Context):
    """Sincroniza os comandos de app com o Discord (apenas para o dono do bot)."""
    try:
        # Sincroniza os comandos para a guilda atual. É mais rápido que a sincronização global.
        guild = ctx.guild
        ctx.bot.tree.copy_global_to(guild=guild)
        synced = await ctx.bot.tree.sync(guild=guild)
        
        await ctx.send(f"✅ Sincronizados {len(synced)} comandos para este servidor.")
        print(f"Sincronizados {len(synced)} comandos para o servidor '{guild.name}'.")
    except Exception as e:
        await ctx.send(f"❌ Falha ao sincronizar comandos: {e}")
        print(f"Falha ao sincronizar comandos: {e}")

async def main():
    """Função principal para iniciar o bot"""
    await bot.start(DISCORD_BOT_TOKEN)

if __name__ == '__main__':
    asyncio.run(main())