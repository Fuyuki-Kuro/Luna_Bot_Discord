import discord
import datetime
from typing import Dict, Any

# Importamos o mapa de emojis para usá-lo aqui
from database.models import ELO_EMOJI_MAP

async def create_player_card_embed(member: discord.Member, player_data: Dict[str, Any]) -> discord.Embed:
    """Cria e retorna um embed de apresentação para um jogador recém-registrado."""
    
    player_elo_str = player_data.get('individual_current_elo', 'N/A')
    elo_emoji = ELO_EMOJI_MAP.get(player_elo_str, "⚫")

    embed = discord.Embed(
        title=f"Novo Combatente na Arena!",
        description=f"**{member.mention}** acaba de se registrar e está pronto para a batalha.",
        color=discord.Color.green()
    )
    
    if member.display_avatar:
        embed.set_thumbnail(url=member.display_avatar.url)

    embed.add_field(name="Nick no Jogo", value=f"`{player_data.get('wr_nickname', 'Não informado')}`", inline=True)
    embed.add_field(name="Região", value=player_data.get('wr_region', 'N/A'), inline=True)
    
    roles_list = player_data.get('preferred_roles', [])
    roles_str = ', '.join(roles_list) if roles_list else "Não informado"
    embed.add_field(name="Rotas Preferidas", value=roles_str, inline=False)
    
    # --- MUDANÇA APLICADA AQUI ---
    elo_points = player_data.get('individual_elo_points', 0)
    elo_division = player_data.get('individual_current_division', '')
    embed.add_field(
        name="Elo", 
        value=f"{elo_emoji} **{player_elo_str} {elo_division}**\n`{elo_points}` Pontos", 
        inline=False
    )
    
    embed.set_footer(text=f"ID do Usuário: {member.id}")
    embed.timestamp = datetime.datetime.now(datetime.timezone.utc)
    
    return embed

async def create_duel_result_embed(winner: discord.Member, loser: discord.Member, duel_data: Dict[str, Any], winner_new_elo: int, loser_new_elo: int) -> discord.Embed:
    """Cria o embed com o resultado detalhado de um duelo para o histórico."""
    
    elo_change = duel_data['points_change']
    
    embed = discord.Embed(
        title=f"⚔️ Resultado do Duelo: {winner.display_name} vs. {loser.display_name}",
        color=discord.Color.green()
    )
    
    embed.add_field(
        name=f"🏆 Vencedor: {winner.display_name}",
        value=f"Elo Anterior: `{duel_data['challenger_elo_at_match'] if winner.id == duel_data['challenger_id'] else duel_data['opponent_elo_at_match']}`\n"
              f"**Elo Novo: `{winner_new_elo}` (+{elo_change} Pontos)**",
        inline=True
    )
    
    embed.add_field(
        name=f"💔 Perdedor: {loser.display_name}",
        value=f"Elo Anterior: `{duel_data['challenger_elo_at_match'] if loser.id == duel_data['challenger_id'] else duel_data['opponent_elo_at_match']}`\n"
              f"**Elo Novo: `{loser_new_elo}` (-{elo_change} Pontos)**",
        inline=True
    )
    
    embed.timestamp = datetime.datetime.now(datetime.timezone.utc)
    embed.set_footer(text=f"ID do Duelo: {duel_data['_id']}")
    
    return embed
