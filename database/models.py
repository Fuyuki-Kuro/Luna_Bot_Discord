from typing import List, Dict, Optional, TypedDict, Any
import time

ELO_TIERS_MAP = {
    "Ferro IV": 0, "Ferro III": 100, "Ferro II": 200, "Ferro I": 300,
    "Bronze IV": 400, "Bronze III": 500, "Bronze II": 600, "Bronze I": 700,
    "Prata IV": 800, "Prata III": 900, "Prata II": 1000, "Prata I": 1100,
    "Ouro IV": 1200, "Ouro III": 1300, "Ouro II": 1400, "Ouro I": 1500,
    "Platina IV": 1600, "Platina III": 1700, "Platina II": 1800, "Platina I": 1900,
    "Esmeralda": 2000, # Elos sem divisões fixas, baseados apenas nos pontos
    "Diamante": 2500,
    "Mestre": 3000,
    "Grão-Mestre": 3500,
    "Desafiante": 4000
}

ELO_EMOJI_MAP = {
    "Ferro": "<:elo_ferro:1368912325243047966>",
    "Bronze": "<:elo_bronze:1368912439176859728>",
    "Prata": "<:elo_prata:1368912302958448701>",
    "Ouro": "<:elo_ouro:1368912384546181265>",
    "Platina": "<:elo_platina:1368912518206066688>",
    "Esmeralda": "<:elo_esmeralda:1368912352233259061>",
    "Diamante": "<:elo_diamante:1368912339709071372>",
    "Mestre": "<:elo_mestre:1368912408797515796>",
    "Grão-Mestre": "<:elo_graomestre:1368912554155446282>",
    "Desafiante": "<:elo_desafiante:1368912532911165490>"
}

class PlayerData(TypedDict):
    _id: int
    discord_id: int
    username: str
    is_registered: bool
    registration_reminders_sent: int
    last_reminder_sent_at: Optional[float]
    wr_nickname: Optional[str]
    wr_region: Optional[str]
    wwr_official_rank: Optional[str]
    preferred_roles: Optional[List[str]]
    
    # Campos de ELO
    individual_elo_points: int
    individual_current_elo: str
    individual_current_division: str
    
    # --- NOVOS CAMPOS PARA O SISTEMA DINÂMICO ---
    is_in_promo: bool                    # True se o jogador está na sua série de promoção
    promo_wins: int                      # Vitórias na série atual
    promo_losses: int                    # Derrotas na série atual
    win_streak: int                      # Contagem de vitórias consecutivas
    demotion_shield_games: int           # Jogos restantes de proteção contra rebaixamento
    
    individual_match_history: List[Dict[str, Any]]
    created_at: float
    last_updated: float
    player_card_message_id: Optional[int]

class DuelMatchData(TypedDict):
    """Representa uma partida de duelo 1v1."""
    _id: Optional[Any]
    challenger_id: int
    opponent_id: int
    
    status: str  # "pending", "in_progress", "completed", "cancelled"
    
    # Será preenchido quando o duelo terminar
    winner_id: Optional[int]
    loser_id: Optional[int]

    # Armazena o ELO dos jogadores no momento da partida
    challenger_elo_at_match: int
    opponent_elo_at_match: int
    
    # Pontos ganhos/perdidos
    points_change: Optional[int]
    
    # ID do canal privado do duelo
    channel_id: Optional[int]

    # Metadados
    created_at: float
    accepted_at: Optional[float]
    completed_at: Optional[float]

# Modelo para uma Equipe
class TeamData(TypedDict):
    """
    Representa uma equipe de 5 jogadores.
    Este modelo será armazenado em uma coleção 'teams'.
    """
    _id: Optional[Any]
    name: str
    leader_id: int
    members: List[int]

    # Status da Equipe
    is_full: bool
    is_locked: bool

    # Campos para o elo da equipe
    team_elo_points: int
    team_current_elo: str
    team_current_division: str

    # Histórico de partidas da equipe (treinos: 5v5, torneios: 5v5/ARAM)
    team_match_history: List[Dict[str, Any]]

    # Metadados
    created_at: float
    last_updated: float
    invite_code: Optional[str]
    private_text_channel_id: Optional[int]
    private_voice_channel_id: Optional[int]
    private_announcement_channel_id: Optional[int]

# Modelo para uma guilda
class GuildData(TypedDict):
    """
    Representa uma guilda (clã) maior que pode conter várias equipes ou jogadores soltos.
    Este modelo será armazenado em uma coleção 'guilds'.
    """
    _id: Optional[Any]
    name: str
    leader_id: int
    members: List[int]
    teams: List[str]
    description: Optional[str]
    rules: Optional[str]
    guild_elo_points: int
    guild_current_elo: str
    guild_current_division: str
    guild_match_history: List[Dict[str, Any]]
    
    # --- CAMPO ADICIONADO ---
    role_id: Optional[int]

    # Metadados
    created_at: float
    last_updated_at: float
    category_id: Optional[int]
    main_channel_id: Optional[int]
    recruitment_channel_id: Optional[int]

# Modelo para um Torneio
class TournamentData(TypedDict):
    """
    Representa um torneio organizado pelo bot.
    Este modelo será armazenado em uma coleção 'tournaments'.
    """
    _id: Optional[Any]
    name: str
    tournament_type: str # "5v5_team" ou "1v1_player"

    start_date: str
    start_time: str
    
    max_participants: int

    # Participantes (Equipes)
    registered_participants: List[str]

    status: str # Status atual do torneio: "pending", "registration_open", "in_progress", "finished", "cancelled"

    # Canais de Comunicação
    annoucement_channel_id: Optional[int]
    match_results_channel_id: Optional[int]

    # Informações da chave/progresso do torneio
    bracket_url: Optional[str] # URL para chave externa (ex: Challonge) ou gerada pelo bot
    current_round: Optional[int] # Rodada atual (se o bot gerenciar a chave internamente)
    matches: Optional[List[Dict[str, Any]]] # Detalhes das partidas (equipes/jogadores, resultado, status)

    # RESULTADOS FINAIS
    winner_name: Optional[str]
    runner_up_name: Optional[str]

    # Metadados
    created_at: float
    last_updated_at: float

# Modelo para um Treino (Partida 5v5 avulsa)
class TrainingMatchData(TypedDict):
    """
    Representa um treino/partida 5v5 avulsa entre equipes.
    Este modelo pode ser armazenado em uma coleção 'training_matches'.
    """
    _id: Optional[Any] # ID do MongoDB (ObjectId)
    team1_name: str    # Nome da primeira equipe
    team2_name: str    # Nome da segunda equipe
    
    team1_score: int   # Pontuação da equipe 1 (ex: 2 para 2-1)
    team2_score: int   # Pontuação da equipe 2 (ex: 1 para 2-1)
    
    winner_name: str   # Nome da equipe vencedora
    loser_name: str    # Nome da equipe perdedora
    
    reported_by_id: int # ID do Discord do usuário que reportou o resultado
    reported_at: float  # Timestamp do reporte
    
    # Elos na hora da partida (para cálculo de pontos)
    team1_elo_at_match: int
    team2_elo_at_match: int

    # Pontos ganhos/perdidos (para referência)
    team1_points_change: int
    team2_points_change: int

    # IDs dos membros que participaram (para cálculo de elo individual)
    team1_member_ids: List[int]
    team2_member_ids: List[int]

    # Metadados
    created_at: float

# Modelo para uma Partida 1v1 (avulsa ou de torneio)
class OneVOneMatchData(TypedDict):
    """
    Representa uma partida 1v1 avulsa ou dentro de um torneio 1v1.
    Pode ser armazenado em uma coleção 'one_v_one_matches'.
    """
    _id: Optional[Any] # ID do MongoDB (ObjectId)
    player1_id: int    # ID do Discord do primeiro jogador
    player2_id: int    # ID do Discord do segundo jogador

    winner_id: int     # ID do Discord do jogador vencedor
    loser_id: int      # ID do Discord do jogador perdedor

    reported_by_id: int # ID do Discord do usuário que reportou o resultado
    reported_at: float  # Timestamp do reporte

    # Elos na hora da partida (para cálculo de pontos)
    player1_elo_at_match: int
    player2_elo_at_match: int

    # Pontos ganhos/perdidos (para referência)
    player1_points_change: int
    player2_points_change: int

    # Contexto da partida
    tournament_id: Optional[Any] # ID do torneio ao qual pertence (se houver)
    tournament_name: Optional[str]

    # Metadatos
    created_at: float




    











