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
EMAIL = os.getenv("DISCORD_EMAIL")
SENHA = os.getenv("DISCORD_PASSWORD")
INTERVALO = 2

def fazer_login(page):
    print("🌐 Abrindo Discord...")
    page.goto(URL)
    try:
        page.get_by_text("Continuar no Navegador").click(timeout=5000)
    except:
        pass

    if page.locator("input[name='email']").is_visible(timeout=5000):
        page.fill("input[name='email']", EMAIL)
        page.fill("input[name='password']", SENHA)
        page.get_by_role("button", name="Entrar").click()
        page.wait_for_timeout(8000)
        print("✅ Login realizado")

def monitorar_killfeed(page):
    print("🔎 Esperando killfeed...")
    page.wait_for_selector("div[class*='embedDescription']", timeout=30000)
    
    kills_processadas = set()
    print("🚀 Monitoramento iniciado")

    while True:
        try:
            # Pegamos os elementos atuais na tela
            elementos = page.locator("div[class*='embedDescription'] span").all()

            for el in elementos:
                texto = el.inner_text().strip()

                if texto and texto not in kills_processadas:
                    # Adicionamos ao set IMEDIATAMENTE para evitar o loop em caso de erro no parser
                    kills_processadas.add(texto)
                    
                    dados = parse_killfeed(texto)

                    # ... dentro do loop de monitorar_killfeed em main.py

                    if dados:
                        killer = dados["killer"]
                        vitima = dados["vitima"]

                        is_killer_avg = jogador_avg(killer)
                        is_vitima_avg = jogador_avg(vitima)

                        # 🛑 FILTRO CRÍTICO: Se NINGUÉM for AVG, ignore completamente e não salve nada
                        if not is_killer_avg and not is_vitima_avg:
                            # print(f"ℹ️ Ignorado (Sem membros AVG): {killer} vs {vitima}") # Opcional para debug
                            continue 

                        # LÓGICA DE REGISTRO:
                        # 1. Evita Fogo Amigo (Ambos são AVG)
                        if is_killer_avg and is_vitima_avg:
                            print(f"⚠️ Fogo Amigo ignorado: {killer} vs {vitima}")
                            continue

                        # 2. Registra apenas se UM for AVG (Membro matando inimigo OU Membro morrendo)
                        print(f"\n🔥 REGISTRANDO: {killer} ⚔️ {vitima}")
                        salvar_kill(
                            killer,
                            vitima,
                            dados["arma"],
                            dados["distancia"]
                        )
                    elif is_killer_avg and is_vitima_avg:
                        print(f"⚠️ Fogo Amigo ignorado: {killer} vs {vitima}")
                    # Caso contrário, o código apenas ignora silenciosamente

        except Exception as erro:
            print("⚠️ erro no loop:", erro)

        time.sleep(INTERVALO)

def main():
    init_db()
    while True:
        try:
            with sync_playwright() as p:
                browser = p.chromium.launch(headless=False) # Mude para False se quiser ver o navegador

                context = browser.new_context(
                    user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36",
                    locale="pt-BR"
                )
                page = context.new_page()
                fazer_login(page)
                monitorar_killfeed(page)
        except Exception as erro:
            print("❌ erro geral:", erro)
            print("🔄 reiniciando em 10s")
            time.sleep(10)

if __name__ == "__main__":
    main()