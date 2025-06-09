def calculate_elo(winner_rating: int, loser_rating: int, winner_k: int, loser_k: int) -> tuple[int, int]:
    """
    Calcula a mudança de ELO para o vencedor e o perdedor,
    usando Fatores K individuais.
    Retorna uma tupla com (pontos_ganhos_pelo_vencedor, pontos_perdidos_pelo_perdedor).
    """
    # Probabilidade de vitória do vencedor contra o perdedor
    probability_of_winning = 1 / (1 + 10 ** ((loser_rating - winner_rating) / 400))
    
    # Mudança de pontos para o vencedor (resultado real foi 1)
    winner_points_change = winner_k * (1 - probability_of_winning)
    
    # Mudança de pontos para o perdedor (resultado real foi 0)
    loser_points_change = loser_k * (0 - (1 - probability_of_winning))
    
    return round(winner_points_change), round(loser_points_change)