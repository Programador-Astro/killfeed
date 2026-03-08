import sqlite3

DB_NAME = "killfeed.db"


# ==========================
# CONEXÃO
# ==========================

def get_connection():

    conn = sqlite3.connect(
        DB_NAME,
        timeout=10
    )

    conn.row_factory = sqlite3.Row

    return conn


# ==========================
# INIT DB
# ==========================

def init_db():

    conn = get_connection()
    cursor = conn.cursor()

    # melhora concorrência
    cursor.execute("PRAGMA journal_mode=WAL")

    # melhora performance
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

    # índices para performance
    cursor.execute(
        "CREATE INDEX IF NOT EXISTS idx_killer ON kills(killer)"
    )

    cursor.execute(
        "CREATE INDEX IF NOT EXISTS idx_vitima ON kills(vitima)"
    )

    cursor.execute(
        "CREATE INDEX IF NOT EXISTS idx_timestamp ON kills(timestamp)"
    )

    conn.commit()
    conn.close()

    print("✅ Banco de dados pronto")


# ==========================
# SALVAR KILL
# ==========================

def salvar_kill(killer, vitima, arma, distancia):

    try:

        conn = get_connection()
        cursor = conn.cursor()

        # garantir que distância é número
        if isinstance(distancia, str):
            distancia = int(distancia.replace("m", "").strip())

        cursor.execute("""
            INSERT INTO kills (killer, vitima, arma, distancia)
            VALUES (?, ?, ?, ?)
        """, (killer, vitima, arma, distancia))

        conn.commit()

    except Exception as e:

        print("Erro ao salvar kill:", e)

    finally:

        conn.close()