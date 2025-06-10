import time
from typing import Optional, Any
from motor.motor_asyncio import AsyncIOMotorCollection
from bson import ObjectId # Importa o ObjectId do PyMongo
from .models import DuelMatchData

class DuelService:
    def __init__(self, collection: AsyncIOMotorCollection):
        self.collection = collection

    async def create_duel(self, challenger_id: int, opponent_id: int, challenger_elo: int, opponent_elo: int) -> DuelMatchData:
        duel_doc: DuelMatchData = {
            "challenger_id": challenger_id, "opponent_id": opponent_id, "status": "pending",
            "reported_winner_id": None,
            'duel_type': '1v1',
            "winner_id": None, "loser_id": None, "challenger_elo_at_match": challenger_elo,
            "opponent_elo_at_match": opponent_elo, "points_change": None, "channel_id": None,
            "created_at": time.time(), "accepted_at": None, "completed_at": None
        }
        result = await self.collection.insert_one(duel_doc)
        return await self.collection.find_one({"_id": result.inserted_id})

    async def get_active_duel_for_player(self, player_id: int) -> Optional[DuelMatchData]:
        return await self.collection.find_one({
            "$or": [{"challenger_id": player_id}, {"opponent_id": player_id}],
            "status": {"$in": ["pending", "in_progress"]}
        })

    async def get_duel_by_id(self, duel_id: str) -> Optional[DuelMatchData]:
        """Busca um duelo pelo seu ID de documento, convertendo a string para ObjectId."""
        try:
            # --- CORREÇÃO APLICADA AQUI ---
            # Converte a string do ID para o tipo ObjectId antes de buscar.
            return await self.collection.find_one({"_id": ObjectId(duel_id)})
        except Exception:
            # Retorna None se o ID for inválido e não puder ser convertido.
            return None

    async def update_duel(self, duel_id: Any, updates: dict) -> Optional[DuelMatchData]:
        # Converte o ID aqui também por segurança.
        _id = ObjectId(duel_id) if not isinstance(duel_id, ObjectId) else duel_id
        return await self.collection.find_one_and_update(
            {"_id": _id},
            {"$set": updates},
            return_document=True
        )