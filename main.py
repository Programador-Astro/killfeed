from playwright.sync_api import sync_playwright
import time
import os
from dotenv import load_dotenv
from parser import parse_killfeed
from database import init_db, salvar_kill
from utils import jogador_avg

# ==========================
# CONFIG
# ==========================
load_dotenv()
URL = "https://discord.com/channels/996414449143529523/1411432013067714662"

EMAIL = os.getenv("DISCORD_EMAIL", "seu_email_aqui")
SENHA = os.getenv("DISCORD_PASSWORD", "sua_senha_aqui")

INTERVALO = 2


# ==========================
# LOGIN
# ==========================

def fazer_login(page):

    print("🌐 Abrindo Discord...")
    page.goto(URL)

    try:
        page.get_by_text("Continuar no Navegador").click(timeout=5000)
    except:
        pass

    page.wait_for_selector("input[name='email']", timeout=15000)

    page.fill("input[name='email']", EMAIL)
    page.fill("input[name='password']", SENHA)

    page.get_by_role("button", name="Entrar").click()

    page.wait_for_timeout(8000)

    print("✅ Login realizado")


# ==========================
# MONITOR
# ==========================

def monitorar_killfeed(page):

    print("🔎 Esperando killfeed...")

    page.wait_for_selector("div[class*='embedDescription']", timeout=20000)

    kills_processadas = set()

    print("🚀 Monitoramento iniciado")

    while True:

        try:

            elementos = page.locator("div[class*='embedDescription'] span").all()

            for el in elementos:

                texto = el.inner_text().strip()

                if texto and texto not in kills_processadas:

                    dados = parse_killfeed(texto)

                    if dados:

                        killer = dados["killer"]
                        vitima = dados["vitima"]

                        # 🔎 FILTRO AVG
                        if jogador_avg(killer) or jogador_avg(vitima):

                            print("\n🔥 KILL AVG DETECTADA")
                            print("Killer:", killer)
                            print("vitima:", vitima)
                            print("Arma:", dados["arma"])
                            print("Distância:", dados["distancia"])
                            if jogador_avg(killer) and jogador_avg(vitima):
                                print(">> Killer e Vitima são AVG")
                            else:
                                salvar_kill(
                                    killer,
                                    vitima,
                                    dados["arma"],
                                    dados["distancia"]
                                )

                    kills_processadas.add(texto)

        except Exception as erro:

            print("⚠️ erro:", erro)

        time.sleep(INTERVALO)


# ==========================
# MAIN
# ==========================

def main():

    init_db()

    while True:

        try:

            with sync_playwright() as p:

                browser = p.chromium.launch(
                    headless=True,
                    args=[
                        "--no-sandbox",
                        "--disable-dev-shm-usage",
                        "--disable-blink-features=AutomationControlled"
                    ]
                )

                context = browser.new_context()
                page = context.new_page()

                fazer_login(page)

                monitorar_killfeed(page)

        except Exception as erro:

            print("❌ erro geral:", erro)
            print("🔄 reiniciando em 10s")

            time.sleep(10)


if __name__ == "__main__":
    main()