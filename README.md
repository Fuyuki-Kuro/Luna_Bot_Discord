# Wild Rift Nexus Bot

---

## Índice

* [Sobre o Projeto](#sobre-o-projeto)
* [Funcionalidades](#funcionalidades)
* [Tecnologias Utilizadas](#tecnologias-utilizadas)
* [Como Usar](#como-usar)
    * [Pré-requisitos](#pré-requisitos)
    * [Configuração do Ambiente](#configuração-do-ambiente)
    * [Obtendo o Token do Bot Discord](#obtendo-o-token-do-bot-discord)
    * [Configuração do MongoDB](#configuração-do-mongodb)
    * [Variáveis de Ambiente](#variáveis-de-ambiente)
    * [Executando o Bot](#executando-o-bot)
* [Estrutura do Projeto](#estrutura-do-projeto)
* [Comandos do Bot](#comandos-do-bot)
* [Contribuindo](#contribuindo)
* [Licença](#licença)
* [Contato](#contato)

---

## Sobre o Projeto

O **Wild Rift Nexus Bot** é um bot para Discord robusto e multifuncional, desenvolvido em **Python** utilizando a biblioteca `discord.py` para interação com o Discord, `MongoDB` como banco de dados NoSQL para persistência de dados, e `python-dotenv` para o gerenciamento seguro de variáveis de ambiente.

Este projeto ambicioso visa aprimorar a experiência da comunidade de jogadores de Wild Rift no Discord, oferecendo um conjunto de ferramentas poderosas para gerenciamento de membros, organização de equipes e guildas, e a criação e automação de torneios. Nosso objetivo é transformar servidores de Discord em verdadeiros centros de comunidade para jogadores de Wild Rift, facilitando a organização e o engajamento.

---

## Funcionalidades

O Wild Rift Nexus Bot oferece uma gama de funcionalidades essenciais para a comunidade:

* **Gerenciamento de Cargos e Rotas:**
    * Atribuição e organização de cargos dentro do servidor, como as rotas específicas do jogo (Topo, Selva, Meio, Atirador, Suporte).
    * Facilita a comunicação e a formação de grupos com base nas preferências de rota dos jogadores.
* **CRUD de Equipes:**
    * Permite a criação, visualização, atualização e exclusão de equipes de até 5 membros.
    * Ideal para amigos que desejam jogar juntos ou para jogadores que buscam um time fixo para ranqueadas ou torneios.
    * Sistema de convite de membros e transferência de liderança de equipe.
    * Potencial para criação de canais de voz/texto privados para cada equipe.
* **CRUD de Guildas (Clãs):**
    * Funcionalidade para criar, gerenciar e exibir guildas (clãs), proporcionando uma estrutura para comunidades maiores e mais organizadas.
    * Registro de membros, líderes e informações adicionais da guilda.
* **Sistema de Torneios Automatizado:**
    * Gerencia a criação, inscrição e acompanhamento de torneios regulares (ex: semanais).
    * Suporte à geração de chaves (simples ou dupla eliminação) para organização dos confrontos.
    * Ferramentas para reporte de resultados pelos próprios times e atualização automática dos placares.
    * Notificações e lembretes automáticos sobre o status do torneio e próximos jogos.
    * Ranking de equipes baseado no desempenho em torneios.
* **Persistência de Dados com MongoDB:**
    * Todas as informações críticas (equipes, guildas, torneios, configurações) são armazenadas de forma eficiente e escalável no MongoDB.

---

## Tecnologias Utilizadas

As seguintes tecnologias e bibliotecas foram utilizadas no desenvolvimento deste projeto:

* **Python 3.9+**
* **discord.py**: Biblioteca para interação com a API do Discord.
* **pymongo**: Driver oficial do MongoDB para Python.
* **python-dotenv**: Para carregar variáveis de ambiente de um arquivo `.env`.
* **dnspython**: (Opcional, mas recomendado) Necessário para conexões com MongoDB Atlas (SRV records).
* **MongoDB**: Banco de dados NoSQL para armazenamento de dados.

---

## Como Usar

Para colocar o Wild Rift Nexus Bot para funcionar, siga os passos abaixo:

### Pré-requisitos

* **Python 3.9+** instalado.
* Uma conta no **Discord** e permissões para criar e gerenciar aplicações/bots.
* Uma instância do **MongoDB** (local ou na nuvem, como o MongoDB Atlas) rodando e acessível.

### Configuração do Ambiente

1.  **Clone o repositório:**
    ```bash
    git clone [https://github.com/seu-usuario/wild-rift-nexus-bot.git](https://github.com/seu-usuario/wild-rift-nexus-bot.git)
    cd wild-rift-nexus-bot
    ```

2.  **Crie e ative um ambiente virtual:**
    É uma boa prática usar ambientes virtuais para gerenciar as dependências do projeto isoladamente.
    ```bash
    python -m venv venv
    ```
    * **No Windows:**
        ```bash
        .\venv\Scripts\activate
        ```
    * **No macOS/Linux:**
        ```bash
        source venv/bin/activate
        ```

3.  **Instale as dependências:**
    Com o ambiente virtual ativado, instale todas as bibliotecas necessárias:
    ```bash
    pip install -r requirements.txt
    ```

### Obtendo o Token do Bot Discord

1.  Vá para o [Portal do Desenvolvedor do Discord](https://discord.com/developers/applications).
2.  Crie uma **Nova Aplicação** ou selecione uma existente.
3.  Vá para a aba **Bot** no menu lateral esquerdo.
4.  Clique em "Add Bot" e confirme.
5.  **Copie o Token** do seu bot (clique em "Copy" sob "TOKEN"). **Mantenha este token seguro e nunca o compartilhe publicamente.**
6.  **Ative os Intents Privilegiados**: Na mesma página do Bot, role para baixo e ative os intents **`PRESENCE INTENT`**, **`SERVER MEMBERS INTENT`** e **`MESSAGE CONTENT INTENT`** (se seu bot for ler conteúdo de mensagens). Estes são cruciais para o funcionamento de muitas funcionalidades do bot.
7.  **Convide o Bot para o seu servidor:**
    * Na aba "OAuth2" > "URL Generator", selecione "bot" em "SCOPES".
    * Em "BOT PERMISSIONS", selecione as permissões necessárias (ex: `Administrator` para facilitar, ou granularmente `Manage Roles`, `Send Messages`, `Read Message History`, etc.).
    * Copie o URL gerado e cole no seu navegador para convidar o bot para o seu servidor.

### Configuração do MongoDB

Certifique-se de que sua instância do MongoDB esteja rodando e acessível. Se você estiver usando o MongoDB Atlas, obtenha a URI de conexão completa. Se estiver usando localmente, a URI padrão geralmente é `mongodb://localhost:27017/`.

### Variáveis de Ambiente

Crie um arquivo chamado `.env` na raiz do projeto (no mesmo nível de `main.py`) e adicione as seguintes variáveis:

### Estrutura do Projeto

wild_rift_bot/
│
├── .env                 # Variáveis de ambiente (TOKEN do Discord, URI do MongoDB)
├── .gitignore           # O que o Git deve ignorar (ex: .env, __pycache__)
├── requirements.txt     # Dependências do projeto
│
├── main.py              # Ponto de entrada principal do bot
│
├── cogs/                # Módulos (cogs) para organizar os comandos
│   ├── __init__.py
│   ├── admin.py         # Comandos de administração (gerenciamento de cargos, etc.)
│   ├── teams.py         # Comandos CRUD para equipes
│   ├── guilds.py        # Comandos CRUD para guildas
│   ├── tournaments.py   # Comandos para torneios
│   └── wild_rift.py     # Comandos específicos de Wild Rift (estatísticas, notícias, etc.)
│
├── database/            # Módulo para interação com o MongoDB
│   ├── __init__.py
│   ├── connection.py    # Gerencia a conexão com o MongoDB
│   └── models.py        # Definição dos modelos de dados (equipes, guildas, torneios)
│
└── utils/               # Utilitários e funções auxiliares
    ├── __init__.py
    ├── constants.py     # Constantes (IDs de canais, mensagens padrão)
    ├── embeds.py        # Funções para criar embeds personalizados
    └── permissions.py   # Funções para checagem de permissões

# Comandos do Wild Rift Nexus Bot

Este documento serve como um guia rápido para todos os comandos disponíveis no **Wild Rift Nexus Bot**. Use o prefixo `!` antes de cada comando (ex: `!help`).

---

## 📜 Comandos Gerais

| Comando          | Descrição                                         | Exemplo de Uso       | Permissões Necessárias               |
| :--------------- | :------------------------------------------------ | :------------------- | :----------------------------------- |
| `!help`          | Exibe uma lista de todos os comandos do bot.     | `!help`              | `@everyone`                          |
| `!ping`          | Verifica a latência (ping) do bot.              | `!ping`              | `@everyone`                          |
| `!info`          | Exibe informações gerais sobre o bot.            | `!info`              | `@everyone`                          |

---

## 👥 Comandos de Equipe

Estes comandos permitem que os jogadores criem, gerenciem e interajam com suas equipes no servidor.

| Comando              | Descrição                                                              | Exemplo de Uso                                  | Permissões Necessárias          |
| :------------------- | :--------------------------------------------------------------------- | :---------------------------------------------- | :------------------------------ |
| `!create_team <nome>`| Cria uma nova equipe com o nome especificado. O criador se torna o líder. | `!create_team Dragões Anciões`                  | `@everyone`                     |
| `!join_team <nome>`  | Entra em uma equipe existente.                                          | `!join_team Dragões Anciões`                    | `@everyone`                     |
| `!leave_team`        | Sai da equipe atual.                                                  | `!leave_team`                                   | Membro de uma equipe          |
| `!view_team [nome]`  | Exibe detalhes sobre sua equipe atual ou uma equipe específica.         | `!view_team` (sua equipe) <br> `!view_team T_Rex` | `@everyone`                     |
| `!invite_to_team <@membro>` | (Líder) Convida um membro para sua equipe.                           | `!invite_to_team @jogador123`                   | Líder da Equipe                 |
| `!kick_from_team <@membro>` | (Líder) Remove um membro da sua equipe.                              | `!kick_from_team @jogadorXYZ`                   | Líder da Equipe                 |
| `!transfer_leader <@membro>`| (Líder) Transfere a liderança da equipe para outro membro.           | `!transfer_leader @novo_lider`                  | Líder da Equipe                 |
| `!delete_team <nome>`| (Líder) Deleta sua equipe. Esta ação é irreversível.                   | `!delete_team Dragões Anciões`                  | Líder da Equipe                 |

---

## 🛡️ Comandos de Guilda

Comandos para gerenciar e interagir com as guildas (clãs) do servidor.

| Comando              | Descrição                                                              | Exemplo de Uso                                  | Permissões Necessárias          |
| :------------------- | :--------------------------------------------------------------------- | :---------------------------------------------- | :------------------------------ |
| `!create_guild <nome>`| Cria uma nova guilda. O criador se torna o líder.                     | `!create_guild Irmandade da Grieta`             | `@everyone`                     |
| `!join_guild <nome>` | Entra em uma guilda existente.                                          | `!join_guild Irmandade da Grieta`               | `@everyone`                     |
| `!leave_guild`       | Sai da guilda atual.                                                  | `!leave_guild`                                  | Membro de uma guilda          |
| `!view_guild [nome]` | Exibe detalhes sobre sua guilda atual ou uma guilda específica.         | `!view_guild` (sua guilda) <br> `!view_guild GuildaAlpha` | `@everyone`                     |
| `!delete_guild <nome>`| (Líder) Deleta sua guilda. Esta ação é irreversível.                  | `!delete_guild Irmandade da Grieta`             | Líder da Guilda                 |

---

## 🏆 Comandos de Torneio

Ferramentas para criar, gerenciar e participar de torneios.

| Comando                   | Descrição                                                           | Exemplo de Uso                                                  | Permissões Necessárias          |
| :------------------------ | :------------------------------------------------------------------ | :-------------------------------------------------------------- | :------------------------------ |
| `!create_tournament <nome> <data> <hora> <num_equipes>` | (Admin) Cria um novo torneio com um nome, data, hora e número máximo de equipes. | `!create_tournament CopaNexus 2025-06-15 18:00 8`              | `Gerenciar Servidor`            |
| `!list_tournaments`       | Lista todos os torneios ativos e futuros.                           | `!list_tournaments`                                             | `@everyone`                     |
| `!register_for_tournament <nome_do_torneio>` | (Líder da Equipe) Inscreve sua equipe em um torneio.           | `!register_for_tournament CopaNexus`                            | Líder da Equipe                 |
| `!unregister_from_tournament <nome_do_torneio>` | (Líder da Equipe) Retira sua equipe de um torneio.               | `!unregister_from_tournament CopaNexus`                         | Líder da Equipe                 |
| `!start_tournament <nome_do_torneio>` | (Admin) Inicia um torneio, gerando a chave e notificando as equipes. | `!start_tournament CopaNexus`                                   | `Gerenciar Servidor`            |
| `!report_score <nome_do_torneio> <minha_equipe> <score_minha_equipe> <equipe_adversaria> <score_adversario>` | (Líder da Equipe) Reporta o placar de uma partida do torneio. | `!report_score CopaNexus Dragões 2 1 T_Rex`                     | Líder da Equipe                 |
| `!view_bracket <nome_do_torneio>` | Exibe a chave atual do torneio.                                | `!view_bracket CopaNexus`                                       | `@everyone`                     |
| `!end_tournament <nome_do_torneio>` | (Admin) Finaliza um torneio e anuncia o vencedor.                | `!end_tournament CopaNexus`                                     | `Gerenciar Servidor`            |

---

## ⚙️ Comandos de Administração

Estes comandos exigem permissões elevadas e são destinados a moderadores ou administradores do servidor.

| Comando                   | Descrição                                                              | Exemplo de Uso                                  | Permissões Necessárias          |
| :------------------------ | :--------------------------------------------------------------------- | :---------------------------------------------- | :------------------------------ |
| `!set_role <@membro> <nome_do_cargo>` | Atribui um cargo a um membro específico.                           | `!set_role @Jogador Atirador`                   | `Gerenciar Cargos`              |
| `!remove_role <@membro> <nome_do_cargo>` | Remove um cargo de um membro específico.                           | `!remove_role @Jogador Suporte`                 | `Gerenciar Cargos`              |
| `!set_tournament_channel <#canal>` | Define o canal padrão para anúncios de torneios.                 | `!set_tournament_channel #torneios-wr`          | `Gerenciar Canais`              |
| `!clear <quantidade>`     | Deleta um número específico de mensagens no canal.                    | `!clear 10`                                     | `Gerenciar Mensagens`           |

---

## 📊 Comandos de Wild Rift (Potenciais Integrações)

Estes comandos dependem de futuras integrações com APIs externas (se disponíveis e públicas) ou dados da comunidade.

| Comando                 | Descrição                                                             | Exemplo de Uso                                  | Permissões Necessárias          |
| :---------------------- | :-------------------------------------------------------------------- | :---------------------------------------------- | :------------------------------ |
| `!wr_stats <nome_jogador>` | (Futuro) Busca e exibe estatísticas de um jogador de Wild Rift.      | `!wr_stats SeuNickWR`                           | `@everyone`                     |
| `!wr_news`              | (Futuro) Exibe as últimas notícias e atualizações do Wild Rift.      | `!wr_news`                                      | `@everyone`                     |
| `!leaderboard <rank>`   | (Futuro) Exibe o top 10 jogadores de um determinado rank no servidor. | `!leaderboard Grão-Mestre`                      | `@everyone`                     |

---

**Observações:**

* O prefixo padrão para todos os comandos é `!`.
* Comandos entre `< >` são **obrigatórios**.
* Comandos entre `[ ]` são **opcionais**.
* Certifique-se de ter as permissões necessárias no Discord para executar certos comandos.

---