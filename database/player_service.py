import time
from typing import Optional, List, Dict, Any

from motor.motor_asyncio import AsyncIOMotorCollection
from .models import PlayerData, ELO_TIERS_MAP

class PlayerService:
    def __init__(self, collection: AsyncIOMotorCollection):
        self.collection = collection

    def _get_rank_from_points(self, points: int) -> tuple[str, str]:
        """
        Função auxiliar para determinar o nome do elo e divisão com base nos pontos.
        """
        for rank_full, min_points in sorted(ELO_TIERS_MAP.items(), key=lambda item: item[1], reverse=True):
            if points >= min_points:
                rank_parts = rank_full.split()
                elo_name = rank_parts[0]
                division = rank_parts[1] if len(rank_parts) > 1 else ""
                return elo_name, division
        return "Ferro", "IV"

    async def get_player_by_id(self, member_id: int) -> Optional[PlayerData]:
        """Busca um jogador pelo seu ID do Discord."""
        return await self.collection.find_one({"_id": member_id})

    async def get_or_create_player(self, member) -> PlayerData:
        """Busca um jogador ou cria um registro inicial com todos os campos necessários."""
        player_data = await self.get_player_by_id(member.id)
        if player_data:
            return player_data
        
        new_player: PlayerData = {
            "_id": member.id,
            "discord_id": member.id,
            "username": member.name,
            "is_registered": False,
            "registration_reminders_sent": 0,
            "last_reminder_sent_at": None,
            "wr_nickname": None,
            "wr_region": None,
            "wwr_official_rank": "Não ranqueado",
            "preferred_roles": [],
            "individual_elo_points": 0,
            "individual_current_elo": "Ferro",
            "individual_current_division": "IV",
            "is_in_promo": False,
            "promo_wins": 0,
            "promo_losses": 0,
            "win_streak": 0,
            "demotion_shield_games": 0,
            "individual_match_history": [],
            "created_at": time.time(),
            "last_updated": time.time(),
            "player_card_message_id": None
        }
        await self.collection.insert_one(new_player)
        return new_player

    async def get_unregistered_players(self) -> List[PlayerData]:
        """Busca todos os jogadores que ainda não se registraram."""
        cursor = self.collection.find({"is_registered": False})
        return await cursor.to_list(length=None)

    async def update_player_registration(self, member_id: int, nickname: str, region: str, roles: List[str]):
        """Finaliza o registro de um jogador, atualizando seus dados."""
        await self.collection.update_one(
            {"_id": member_id},
            {"$set": {
                "is_registered": True,
                "wr_nickname": nickname,
                "wr_region": region,
                "preferred_roles": roles,
                "last_updated": time.time()
            }}
        )

    async def update_player_after_duel(self, player_id: int, result: str, points_change: int, opponent_id: int, opponent_elo_before_match: int) -> Dict[str, Any]:
        """
        Atualiza o ELO de um jogador após um duelo, recalcula seu rank e salva a partida no histórico.
        """
        player = await self.get_player_by_id(player_id)
        if not player:
            return {"status": "error", "message": "Jogador não encontrado."}

        # Lógica de Sequência de Vitórias (Win Streak)
        current_streak = player.get('win_streak', 0)
        if result == "win":
            new_streak = current_streak + 1
            # Se atingiu uma sequência de 3 ou mais, aplica um bônus de 10 pontos
            points_bonus = 10 if new_streak >= 3 else 0
        else: # Se for derrota, reseta a sequência
            new_streak = 0
            points_bonus = 0
            
        final_points_change = points_change + points_bonus
        
        # Lógica de ELO e atualização de Rank
        new_points = player.get("individual_elo_points", 0) + final_points_change
        new_elo, new_division = self._get_rank_from_points(new_points)

        updates = {
            "individual_elo_points": new_points,
            "individual_current_elo": new_elo,
            "individual_current_division": new_division,
            "win_streak": new_streak,
            "last_updated": time.time()
        }
        
        match_result = {
            "opponent_id": opponent_id,
            "opponent_elo_at_match": opponent_elo_before_match,
            "points_change": final_points_change,
            "timestamp": time.time()
        }
        
        await self.collection.update_one(
            {"_id": player_id},
            {
                "$set": updates,
                "$push": { "individual_match_history": match_result }
            }
        )
        
        return {"status": "updated", "points": final_points_change, "bonus": points_bonus}

    async def increment_reminder(self, member_id: int):
        """Incrementa a contagem de lembretes de registro enviados."""
        await self.collection.update_one(
            {"_id": member_id},
            {"$inc": {"registration_reminders_sent": 1}, "$set": {"last_reminder_sent_at": time.time()}}
        )

    async def set_player_card_message_id(self, member_id: int, message_id: int):
        """Salva o ID da mensagem do card do jogador no banco de dados."""
        await self.collection.update_one(
            {"_id": member_id},
            {"$set": {"player_card_message_id": message_id}}
        )

    async def delete_player(self, member_id: int):
        """Deleta um jogador do banco de dados."""
        await self.collection.delete_one({"_id": member_id})