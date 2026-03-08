from playwright.sync_api import sync_playwright
import time
import os
from dotenv import load_dotenv
from parser import parse_killfeed
from database import init_db, salvar_kill
from utils import jogador_avg
import logging
from playwright.sync_api import sync_playwright, Page, Error as PlaywrightError
# Configuração básica para exibir as mensagens no terminal
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
    datefmt="%H:%M:%S"
)

# Criar a instância do logger que o código utiliza
logger = logging.getLogger(__name__)
# ==========================
# CONFIG
# ==========================
load_dotenv()

URL = "https://discord.com/channels/996414449143529523/1411432013067714662"
EMAIL = os.getenv("DISCORD_EMAIL")
SENHA = os.getenv("DISCORD_PASSWORD")
INTERVALO = 2

def fazer_login(page: Page) -> None:
    logger.info("🌐 Abrindo Discord...")
    
    try:
        # 1. Vai para a página e espera o carregamento básico
        page.goto("https://discord.com/login", wait_until="domcontentloaded")
        
        # 2. Espera os campos aparecerem
        page.wait_for_selector("input[name='email']", timeout=30000)
        page.fill("input[name='email']", EMAIL)
        page.fill("input[name='password']", SENHA)
        
        logger.info("Enviando credenciais...")

        # 3. Tenta clicar no botão de forma mais robusta
        # Em vez de depender do nome "Entrar", pegamos o botão do tipo 'submit'
        botao_login = page.locator("button[type='submit']")
        
        # Se o botão estiver visível, clica. Se não, tenta pelo texto (PT ou EN)
        if botao_login.count() > 0:
            botao_login.click()
        else:
            # Fallback caso a estrutura mude: procura por texto
            page.locator("button:has-text('Entrar'), button:has-text('Log In')").click()
        
        # 4. Aumentamos um pouco o tempo para o login processar no servidor
        logger.info("Aguardando autenticação...")
        page.wait_for_timeout(12000)
        
        # 5. Verifica se ainda estamos na página de login (pode ter dado erro de senha ou captcha)
        if "login" in page.url:
            logger.warning("⚠️ Ainda na página de login. Verifique se apareceu um Captcha ou erro de senha.")
        
        logger.info("✅ Login processado. Navegando para o canal...")
        page.goto(URL, wait_until="networkidle")
        
    except PlaywrightError as e:
        logger.error(f"Falha durante o processo de login: {e}")
        raise

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
                browser = p.chromium.launch(headless=True) # Mude para False se quiser ver o navegador
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