import sqlite3
import psycopg
import os
from dotenv import load_dotenv

load_dotenv()

DATABASE_URL = os.getenv("DATABASE_URL")


# ==========================
# CONEXÃO
# ==========================

def get_connection():

    if DATABASE_URL:
        # PostgreSQL (Railway)
        return psycopg.connect(DATABASE_URL)

    # SQLite (local)
    return sqlite3.connect("killfeed.db")


# ==========================
# INIT DB
# ==========================

def init_db():

    conn = get_connection()
    cursor = conn.cursor()

    if DATABASE_URL:
        # PostgreSQL
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

        cursor.execute(
            "CREATE INDEX IF NOT EXISTS idx_killer ON kills(killer)"
        )

        cursor.execute(
            "CREATE INDEX IF NOT EXISTS idx_vitima ON kills(vitima)"
        )

        cursor.execute(
            "CREATE INDEX IF NOT EXISTS idx_timestamp ON kills(timestamp)"
        )

    else:
        # SQLite
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

        if isinstance(distancia, str):
            distancia = int(distancia.replace("m", "").strip())

        if DATABASE_URL:
            # PostgreSQL
            cursor.execute("""
                INSERT INTO kills (killer, vitima, arma, distancia)
                VALUES (%s, %s, %s, %s)
            """, (killer, vitima, arma, distancia))

        else:
            # SQLite
            cursor.execute("""
                INSERT INTO kills (killer, vitima, arma, distancia)
                VALUES (?, ?, ?, ?)
            """, (killer, vitima, arma, distancia))

        conn.commit()

    except Exception as e:
        print("Erro ao salvar kill:", e)

    finally:
        conn.close()