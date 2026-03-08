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

    page.goto("https://discord.com/login")

    # esperar página carregar
    page.wait_for_load_state("networkidle")

    # esperar campo de email
    page.wait_for_selector("input[name='email']", timeout=30000)

    page.fill("input[name='email']", EMAIL)
    page.fill("input[name='password']", SENHA)

    page.get_by_role("button", name="Entrar").click()

    # esperar login concluir
    page.wait_for_timeout(10000)

    print("✅ Login realizado")

    # abrir canal do killfeed
    page.goto(URL)

    esperar_chat(page)


# ==========================
# MONITOR
# ==========================
def esperar_chat(page):

    print("⏳ esperando discord carregar...")

    for _ in range(30):

        try:
            mensagens = page.locator("div[role='log']")
            if mensagens.count() > 0:
                print("✅ chat carregado")
                return
        except:
            pass

        time.sleep(2)

    raise Exception("chat não carregou")

def monitorar_killfeed(page):

    print("🔎 Esperando chat carregar...")

    # esperar qualquer mensagem aparecer
    page.wait_for_selector("article", timeout=60000)

    print("🚀 Monitoramento iniciado")

    kills_processadas = set()

    while True:

        try:

            mensagens = page.locator("article")
            total = mensagens.count()

            for i in range(total):

                texto = mensagens.nth(i).inner_text()

                if "m." not in texto:
                    continue

                linhas = texto.split("\n")

                for linha in linhas:

                    linha = linha.strip()

                    if "m." not in linha:
                        continue

                    if linha in kills_processadas:
                        continue

                    dados = parse_killfeed(linha)

                    if dados:

                        killer = dados["killer"]
                        vitima = dados["vitima"]

                        print("\n🎯 Kill detectada")
                        print(linha)

                        if jogador_avg(killer) or jogador_avg(vitima):

                            print("🔥 KILL AVG DETECTADA")

                            if not (jogador_avg(killer) and jogador_avg(vitima)):

                                salvar_kill(
                                    killer,
                                    vitima,
                                    dados["arma"],
                                    dados["distancia"]
                                )

                    kills_processadas.add(linha)

        except Exception as erro:

            print("⚠️ erro monitor:", erro)

        time.sleep(2)


# ==========================
# MAIN
# ==========================

def main():

    init_db()

    while True:

        try:

            with sync_playwright() as p:

                browser = p.chromium.launch(
                headless=False,
                slow_mo=300,
                args=[
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