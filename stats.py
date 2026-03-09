from database import get_connection
from collections import defaultdict

# ==========================
# LEADERBOARD
# ==========================

def leaderboard():
    conn = get_connection()
    cursor = conn.cursor()

    # Buscamos os dados brutos
    cursor.execute("SELECT killer, vitima, arma, distancia FROM kills")
    rows = cursor.fetchall()
    conn.close()

    players = defaultdict(lambda: {
        "player": "",
        "kills": 0,
        "deaths": 0,
        "arma_count": defaultdict(int),
        "distancias": []
    })

    for row in rows:
        # Garante compatibilidade entre SQLite (Row) e Postgres (Dict)
        if isinstance(row, dict):
            killer, vitima, arma, distancia = row['killer'], row['vitima'], row['arma'], row['distancia']
        else:
            killer, vitima, arma, distancia = row

        # REGRA: Só processa estatísticas para quem tem a tag [A.V.G]
        
        # Se o matador for AVG, computa a kill
        if "[?]" in killer.upper():
            players[killer]["player"] = killer
            players[killer]["kills"] += 1
            players[killer]["arma_count"][arma] += 1
            
            if distancia:
                try:
                    # CURA PARA O TYPEERROR: Limpa a string e vira INT antes de ir pra lista
                    d_limpa = int(str(distancia).lower().replace('m', '').strip())
                    players[killer]["distancias"].append(d_limpa)
                except:
                    pass

        # Se a vítima for AVG, computa a morte
        if "[?]" in vitima.upper():
            players[vitima]["player"] = vitima
            players[vitima]["deaths"] += 1

    ranking = []

    for p in players.values():
        if not p["player"]: continue

        kills = p["kills"]
        deaths = p["deaths"]
        kd = round(kills / deaths, 2) if deaths > 0 else float(kills)

        # Arma favorita
        arma_fav = "N/A"
        if p["arma_count"]:
            arma_fav = max(p["arma_count"], key=p["arma_count"].get)

        # Distancia média (Agora sum() recebe apenas INTs)
        distancia_media = 0
        if p["distancias"]:
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

def destaques():
    ranking = leaderboard()
    if not ranking:
        vazio = {"player": "N/A", "kills": 0, "deaths": 0, "kd": 0, "arma": "N/A", "distancia_media": 0}
        return {"mais_kills": vazio, "melhor_kd": vazio, "menos_mortes": vazio}

    return {
        "mais_kills": max(ranking, key=lambda x: x["kills"]),
        "melhor_kd": max(ranking, key=lambda x: x["kd"]),
        "menos_mortes": min(ranking, key=lambda x: x["deaths"])
    }