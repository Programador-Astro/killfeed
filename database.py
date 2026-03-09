import sqlite3
import psycopg
from psycopg.rows import dict_row
import os
from dotenv import load_dotenv

load_dotenv()

DATABASE_URL = os.getenv("DATABASE_URL")

# ==========================
# CONEXÃO
# ==========================

def get_connection():
    if DATABASE_URL:
        # PostgreSQL (Railway) - Usando dict_row para retornar como dicionário
        return psycopg.connect(DATABASE_URL, row_factory=dict_row)
    
    # SQLite (local)
    conn = sqlite3.connect("killfeed.db")
    conn.row_factory = sqlite3.Row # Permite acessar colunas pelo nome
    return conn

# ==========================
# INIT DB
# ==========================

def init_db():
    conn = get_connection()
    cursor = conn.cursor()

    if DATABASE_URL:
        cursor.execute("""
        CREATE TABLE IF NOT EXISTS kills (
            id SERIAL PRIMARY KEY,
            killer TEXT NOT NULL,
            vitima TEXT NOT NULL,
            arma TEXT,
            distancia INTEGER,
            timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
        """)
    else:
        cursor.execute("PRAGMA journal_mode=WAL")
        cursor.execute("PRAGMA synchronous=NORMAL")
        cursor.execute("""
        CREATE TABLE IF NOT EXISTS kills (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            killer TEXT NOT NULL,
            vitima TEXT NOT NULL,
            arma TEXT,
            distancia INTEGER,
            timestamp DATETIME DEFAULT CURRENT_TIMESTAMP
        )
        """)

    cursor.execute("CREATE INDEX IF NOT EXISTS idx_killer ON kills(killer)")
    cursor.execute("CREATE INDEX IF NOT EXISTS idx_vitima ON kills(vitima)")
    
    conn.commit()
    conn.close()
    print("✅ Banco de dados pronto")

# ==========================
# SALVAR KILL
# ==========================

def salvar_kill(killer, vitima, arma, distancia):
    try:
        # 🛡️ TRAVA DE SEGURANÇA: Só prossegue se pelo menos um tiver a tag [A.V.G]
        tag = "[?]"
        if tag.upper() not in killer.upper() and tag.upper() not in vitima.upper():
            # Se ninguém for do clã, ignora silenciosamente e não gasta banco de dados
            return 

        conn = get_connection()
        cursor = conn.cursor()

        # Limpeza básica da distância se vier como string
        if isinstance(distancia, str):
            try:
                distancia = int(distancia.lower().replace("m", "").strip())
            except:
                distancia = 0

        sql = "INSERT INTO kills (killer, vitima, arma, distancia) VALUES (%s, %s, %s, %s)"
        if not DATABASE_URL:
            sql = sql.replace("%s", "?")

        cursor.execute(sql, (killer, vitima, arma, distancia))
        conn.commit()
        
    except Exception as e:
        print("Erro ao salvar kill:", e)
    finally:
        # Verifica se a conexão foi aberta antes de tentar fechar
        try:
            conn.close()
        except:
            pass

# ==========================
# LEADERBOARD (RANKING)
# ==========================

def leaderboard():
    conn = get_connection()
    cursor = conn.cursor()

    cursor.execute("""
        SELECT killer, vitima, arma, distancia
        FROM kills
    """)

    rows = cursor.fetchall()
    conn.close()

    players = defaultdict(lambda: {
        "player": "",
        "kills": 0,
        "deaths": 0,
        "arma_count": defaultdict(int),
        "distancias": []
    })

    for killer, vitima, arma, distancia in rows:
        # REGRA: Só processa as estatísticas de quem tem a tag [A.V.G]
        
        # Se o matador for AVG, computa a kill
        if "[?]" in killer.upper():
            players[killer]["player"] = killer
            players[killer]["kills"] += 1
            players[killer]["arma_count"][arma] += 1
            
            if distancia:
                try:
                    # Resolve o erro do sum(): converte "50m" ou "50" para 50
                    dist_num = int(str(distancia).replace('m', '').strip())
                    players[killer]["distancias"].append(dist_num)
                except:
                    pass

        # Se a vítima for AVG, computa a morte
        if "[?]" in vitima.upper():
            players[vitima]["player"] = vitima
            players[vitima]["deaths"] += 1

    ranking = []

    for p in players.values():
        # Filtro final: só entra no ranking se tiver nome e for AVG
        if not p["player"] or "[?]" not in p["player"].upper():
            continue

        kills = p["kills"]
        deaths = p["deaths"]

        kd = round(kills / deaths, 2) if deaths > 0 else float(kills)

        # arma favorita
        arma_fav = "N/A"
        if p["arma_count"]:
            arma_fav = max(p["arma_count"], key=p["arma_count"].get)

        # distancia média
        distancia_media = 0
        if p["distancias"]:
            # Agora p["distancias"] só tem números, o sum() funciona!
            distancia_media = round(sum(p["distancias"]) / len(p["distancias"]), 1)

        ranking.append({
            "player": p["player"],
            "kills": kills,
            "deaths": deaths,
            "kd": kd,
            "arma": arma_fav,
            "distancia_media": distancia_media
        })

    ranking.sort(key=lambda x: x["kills"], reverse=True)
    return ranking


# ==========================
# DESTAQUES
# ==========================

def destaques():
    ranking = leaderboard()

    if not ranking:
        vazio = {"player": "N/A", "kills": 0, "deaths": 0, "kd": 0, "arma": "N/A", "distancia_media": 0}
        return {
            "mais_kills": vazio,
            "melhor_kd": vazio,
            "menos_mortes": vazio
        }

    # O ranking já está filtrado, então os destaques serão apenas do clã
    mais_kills = max(ranking, key=lambda x: x["kills"])
    melhor_kd = max(ranking, key=lambda x: x["kd"])
    menos_mortes = min(ranking, key=lambda x: x["deaths"])

    return {
        "mais_kills": mais_kills,
        "melhor_kd": melhor_kd,
        "menos_mortes": menos_mortes
    }