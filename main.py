from playwright.sync_api import sync_playwright
import time
import os
import base64
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

def print_debug_screenshot(page):
    """Gera um link de imagem no log do Railway para debug visual"""
    try:
        screenshot_bytes = page.screenshot(full_page=True)
        b64_img = base64.b64encode(screenshot_bytes).decode()
        print("\n--- 📸 SCREENSHOT DE DEBUG ---")
        print(f"data:image/png;base64,{b64_img}")
        print("--- COPIE O CODIGO ACIMA E COLE NO NAVEGADOR ---\n")
    except Exception as e:
        print(f"Não foi possível tirar screenshot: {e}")

def fazer_login(page):
    print("🌐 Abrindo Discord...")
    # Forçamos o idioma via URL para evitar confusão de seletores
    page.goto("https://discord.com/login?lang=pt-BR")
    
    try:
        # Tenta clicar no botão de navegador se aparecer (com timeout curto)
        page.locator("button:has-text('Browser'), button:has-text('Navegador')").click(timeout=5000)
    except:
        pass

    try:
        # Espera o campo de email carregar
        page.wait_for_selector("input[name='email']", timeout=15000)
        page.fill("input[name='email']", EMAIL)
        page.fill("input[name='password']", SENHA)
        
        print("⌨️ Enviando credenciais...")
        # Clica no botão de submit (independente do idioma do texto)
        page.locator("button[type='submit']").click()
        
        # VERIFICAÇÃO: O login deu certo ou parou em algum bloqueio?
        try:
            # Esperamos a URL mudar para o canal. Se em 15s não mudar, algo barrou.
            page.wait_for_url("**/channels/**", timeout=15000)
            print("✅ Login realizado com sucesso!")
        except:
            print("⚠️ Login demorando ou bloqueado. Verificando tela...")
            print_debug_screenshot(page) # Aqui você verá se tem CAPTCHA ou Verificação de E-mail
            
    except Exception as e:
        print(f"❌ Erro no processo de login: {e}")
        print_debug_screenshot(page)
        raise e

def monitorar_killfeed(page):
    # Garante que está na URL correta
    if page.url != URL:
        page.goto(URL, wait_until="networkidle")

    print("🔎 Esperando killfeed...")
    # Aumentamos o timeout para o primeiro carregamento no servidor
    try:
        page.wait_for_selector("div[class*='embedDescription']", timeout=60000)
    except:
        print("❌ Timeout: Killfeed não apareceu na tela.")
        print_debug_screenshot(page)
        return

    kills_processadas = set()
    print("🚀 Monitoramento iniciado")

    while True:
        try:
            # Pegamos os spans dentro das descrições de embed
            elementos = page.locator("div[class*='embedDescription'] span").all()

            for el in elementos:
                texto = el.inner_text().strip()

                if texto and texto not in kills_processadas:
                    kills_processadas.add(texto)
                    
                    dados = parse_killfeed(texto)

                    if dados:
                        killer = dados["killer"]
                        vitima = dados["vitima"]

                        is_killer_avg = jogador_avg(killer)
                        is_vitima_avg = jogador_avg(vitima)

                        # Filtros de AVG
                        if not is_killer_avg and not is_vitima_avg:
                            continue 

                        if is_killer_avg and is_vitima_avg:
                            print(f"⚠️ Fogo Amigo: {killer} vs {vitima}")
                            continue

                        print(f"🔥 REGISTRANDO: {killer} ⚔️ {vitima}")
                        salvar_kill(killer, vitima, dados["arma"], dados["distancia"])
                    else:
                        # Log opcional para ver o que o parser está recebendo e falhando
                        # print(f"Texto não parseado: {texto}")
                        pass

        except Exception as erro:
            print("⚠️ erro no loop de leitura:", erro)

        time.sleep(INTERVALO)

def main():
    init_db()
    while True:
        try:
            with sync_playwright() as p:
                # IMPORTANTE: headless=True para o Railway
                browser = p.chromium.launch(
                    headless=True,
                    args=["--no-sandbox", "--disable-setuid-sandbox"]
                )

                context = browser.new_context(
                    user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36",
                    locale="pt-BR"
                )
                
                page = context.new_page()
                fazer_login(page)
                monitorar_killfeed(page)
                
        except Exception as erro:
            print(f"❌ erro geral: {erro}")
            print("🔄 reiniciando em 10s")
            time.sleep(10)

if __name__ == "__main__":
    main()