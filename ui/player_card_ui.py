import discord
from discord import ui

# Importamos a função de criar o embed para poder reutilizá-la
from utils.embeds import create_player_card_embed

class PlayerCardView(ui.View):
    """
    A View que contém os botões para o card de um jogador.
    """
    def __init__(self):
        super().__init__(timeout=None) # Botões permanentes

    @ui.button(label="Atualizar Dados", style=discord.ButtonStyle.primary, custom_id="player_card_update", emoji="🔄")
    async def update_button(self, interaction: discord.Interaction, button: ui.Button):
        """
        Callback para o botão de atualizar.
        Busca os dados mais recentes do jogador e edita a mensagem.
        """
        await interaction.response.defer(ephemeral=True)

        # Pega o ID do membro a partir do rodapé do embed
        try:
            footer_text = interaction.message.embeds[0].footer.text
            member_id = int(footer_text.split(": ")[1])
        except (IndexError, ValueError, AttributeError):
            return await interaction.followup.send("❌ Não foi possível identificar o jogador a partir deste card.", ephemeral=True)
            
        # Pega o cog para acessar o serviço de jogadores
        reg_cog = interaction.client.get_cog("RegistrationCog")
        if not reg_cog:
            return await interaction.followup.send("❌ Erro interno do bot.", ephemeral=True)

        member = interaction.guild.get_member(member_id)
        player_data = await reg_cog.player_service.get_player_by_id(member_id)

        if member and player_data:
            # Cria o novo embed com os dados atualizados
            new_embed = await create_player_card_embed(member, player_data)
            await interaction.message.edit(embed=new_embed)
            await interaction.followup.send("✅ Card atualizado!", ephemeral=True)
        else:
            await interaction.followup.send("❌ Não foi possível encontrar os dados deste jogador.", ephemeral=True)