import sqlite3
from utils import jogador_avg

DB_NAME = "killfeed.db"


def get_connection():
    return sqlite3.connect(DB_NAME)


# ==========================
# PEGAR PLAYERS AVG
# ==========================

def get_players_avg():

    conn = get_connection()
    cursor = conn.cursor()

    cursor.execute("""
    SELECT DISTINCT killer FROM kills
    UNION
    SELECT DISTINCT vitima FROM kills
    """)

    players = [row[0] for row in cursor.fetchall()]

    conn.close()

    return [p for p in players if jogador_avg(p)]


# ==========================
# KILLS
# ==========================

def get_kills(player):

    conn = get_connection()
    cursor = conn.cursor()

    cursor.execute(
        "SELECT COUNT(*) FROM kills WHERE killer = ?", (player,)
    )

    kills = cursor.fetchone()[0]

    conn.close()

    return kills


# ==========================
# MORTES
# ==========================

def get_deaths(player):

    conn = get_connection()
    cursor = conn.cursor()

    cursor.execute(
        "SELECT COUNT(*) FROM kills WHERE vitima = ?", (player,)
    )

    deaths = cursor.fetchone()[0]

    conn.close()

    return deaths


# ==========================
# K/D
# ==========================

def get_kd(player):

    kills = get_kills(player)
    deaths = get_deaths(player)

    if deaths == 0:
        return kills

    return round(kills / deaths, 2)


# ==========================
# ARMA MAIS USADA
# ==========================

def arma_favorita(player):

    conn = get_connection()
    cursor = conn.cursor()

    cursor.execute("""
        SELECT arma, COUNT(*) as total
        FROM kills
        WHERE killer = ?
        GROUP BY arma
        ORDER BY total DESC
        LIMIT 1
    """, (player,))

    result = cursor.fetchone()

    conn.close()

    if result:
        return result[0]

    return "N/A"


# ==========================
# DISTANCIA MEDIA
# ==========================

def distancia_media(player):

    conn = get_connection()
    cursor = conn.cursor()

    cursor.execute("""
        SELECT distancia
        FROM kills
        WHERE killer = ?
    """, (player,))

    distancias = cursor.fetchall()

    conn.close()

    valores = []

    for d in distancias:

        try:
            valores.append(int(d[0].replace("m", "")))
        except:
            pass

    if not valores:
        return 0

    return round(sum(valores) / len(valores), 1)


# ==========================
# LEADERBOARD
# ==========================

def leaderboard():

    players = get_players_avg()

    ranking = []

    for p in players:

        stats = {
            "player": p,
            "kills": get_kills(p),
            "deaths": get_deaths(p),
            "kd": get_kd(p),
            "arma": arma_favorita(p),
            "distancia_media": distancia_media(p)
        }

        ranking.append(stats)

    ranking.sort(key=lambda x: x["kills"], reverse=True)

    return ranking


# ==========================
# DESTAQUES
# ==========================

def destaques():

    ranking = leaderboard()

    if not ranking:
        return {}

    mais_kills = max(ranking, key=lambda x: x["kills"])
    melhor_kd = max(ranking, key=lambda x: x["kd"])
    menos_mortes = min(ranking, key=lambda x: x["deaths"])

    return {
        "mais_kills": mais_kills,
        "melhor_kd": melhor_kd,
        "menos_mortes": menos_mortes
    }