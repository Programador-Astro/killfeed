from stats import leaderboard, destaques

ranking = leaderboard()

print("\n🏆 LEADERBOARD AVG\n")

for i, p in enumerate(ranking, 1):

    print(
        f"{i}. {p['player']} | "
        f"Kills:{p['kills']} "
        f"Deaths:{p['deaths']} "
        f"K/D:{p['kd']} "
        f"Arma:{p['arma']} "
        f"Dist:{p['distancia_media']}m"
    )

print("\n🔥 DESTAQUES\n")

d = destaques()

print("Mais kills:", d["mais_kills"]["player"])
print("Melhor KD:", d["melhor_kd"]["player"])
print("Menos mortes:", d["menos_mortes"]["player"])