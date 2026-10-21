# arquivo pra testar o uso do selenium
# aqui ta a lógica de abrir a aba do navegador com os desafios e perguntar frustração e cansaço
import csv
import threading
import time
from selenium.common.exceptions import NoSuchWindowException, WebDriverException, UnexpectedAlertPresentException
from selenium.webdriver.chrome.service import Service
import undetected_chromedriver as uc
from selenium.webdriver.support.wait import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from datetime import datetime, timedelta

"""
selenium_runner.py — Driver Selenium do Experimento
Abre os desafios diários do FreeCodeCamp, aplica perguntas de survey pré/pós
e escreve as respostas brutas no CSV. Renomeado de testando.py.
"""

# ──────────────────────────────────────────────
# Gerador de lista de atividades
# ──────────────────────────────────────────────
def selecionar_atividade(quantidade):
    #a lógica aq é q todas as url's são iguais a unc coisa q muda é o final (a data do desafio)
    #então é a unica coisa que vamos alterar
    links = []
    hoje = datetime.now()
    for i in range(1, quantidade + 1):
        data_tarefa = hoje - timedelta(days=i * 30)
        data_formatada = data_tarefa.strftime("%Y-%m-%d")
        links.append(f"https://www.freecodecamp.org/learn/daily-coding-challenge/{data_formatada}")
    return links


# ──────────────────────────────────────────────
# Helper do survey inline
# ──────────────────────────────────────────────
_TEMPLATE_HTML_SURVEY = """
<html>
<body style="font-family: Arial; display: flex; justify-content: center;
             align-items: center; height: 100vh; margin: 0; background: #1a1a2e;">
    <div style="background: white; padding: 40px; border-radius: 12px;
                text-align: center; box-shadow: 0 4px 20px rgba(0,0,0,0.3); min-width: 320px;">
        <h2 style="margin-bottom: 20px; color: #333;">{pergunta}</h2>
        <input id="resp" type="number" min="1" max="10" autofocus
               style="font-size: 2em; width: 80px; text-align: center;
                      padding: 10px; border: 2px solid #ccc; border-radius: 8px;">
        <br><br>
        <button onclick="document.title = document.getElementById('resp').value"
                style="font-size: 1.1em; padding: 10px 30px; background: #4CAF50;
                       color: white; border: none; border-radius: 8px; cursor: pointer;">
            Confirmar
        </button>
        <p style="color: #888; font-size: 0.9em; margin-top: 15px;">Digite um valor de 1 a 10</p>
    </div>
</body>
</html>
"""


def perguntar(navegador, pergunta, timeout) -> str:
    """
    Exibe uma página HTML de survey inline e aguarda o participante confirmar.
    Retorna a resposta como string (título da página definido pelo onclick do botão).
    Lança WebDriverException / NoSuchWindowException se o navegador for fechado.
    """
    navegador.get("about:blank")
    html = _TEMPLATE_HTML_SURVEY.format(pergunta=pergunta)
    html_seguro = html.replace("`", "\\`")
    navegador.execute_script(f"document.write(`{html_seguro}`);")

    WebDriverWait(navegador, timeout).until(
        lambda d: d.title not in ("", "about:blank")
    )
    return navegador.title


def perguntar_com_validacao(navegador, pergunta, timeout) -> int:
    #Repete a pergunta até o participante digitar um valor entre 1 e 10
    while True:
        try:
            resposta = perguntar(navegador, pergunta, timeout)
            valor = int(resposta)
            if 1 <= valor <= 10:
                return valor
            print(f"[survey] Valor fora do intervalo ({resposta}). Repetindo...")
        except ValueError:
            print("[survey] Resposta não numérica. Repetindo...")


def escrever_survey(
    escritor: csv.writer,
    lock: threading.Lock,
    timestamp: float,
    atividade_atual: str,
    momento: str,    # "antes" | "apos"
    dimensao: str,   # "cansaco" | "frustracao"
    nota: int,
) -> None:
    with lock:
        #timestamp, url da atividade_atual, antes/após, cansaço/frustração, 1-10
        escritor.writerow([timestamp, atividade_atual, momento, dimensao, nota])


def obter_url_pela_titulo(navegador, lock_navegador, titulo_janela_os: str):
    """
    Consulta, via CDP (Target.getTargets), todas as abas conhecidas pelo
    Chrome controlado pelo Selenium, e retorna a URL da aba cujo título
    corresponda ao título de janela detectado pelo SO (pygetwindow).

    IMPORTANTE: não usa switch_to.window() — essa consulta é passiva e não
    ativa/foca nenhuma aba, então não interfere na navegação real do
    participante.
    """
    if navegador is None or not titulo_janela_os:
        return None

    try:
        with lock_navegador:
            resultado = navegador.execute_cdp_cmd("Target.getTargets", {})
    except WebDriverException:
        return None

    for target in resultado.get("targetInfos", []):
        if target.get("type") != "page":
            continue
        titulo_aba = target.get("title", "")
        if titulo_aba and titulo_janela_os.startswith(titulo_aba):
            return target.get("url")

    return None
    
# Loop principal do experimento
def rodar_experimento(estado: dict,escritor_csv_survey: csv.writer,lock_csv: threading.Lock,lock_navegador: threading.Lock, quantidade_atividades: int = 2,) -> None:
    #alterar essa quantidade de atividades

    #Conduz o experimento com Selenium:
      #1. Para cada atividade: survey pré → navegar → aguardar conclusão → survey pós
      #2. Atualiza estado["atividade_atual"] antes de cada navegação
      #3. Define estado["executando"] = False ao fechar o navegador ou ao terminar todas as atividades

    lista_atividades = selecionar_atividade(quantidade_atividades) #retorna uma lista com as URLs das atividades

    servico = Service(executable_path="./chromedriver.exe") #talvez não seja necessário
    opcoes = uc.ChromeOptions()
    opcoes.add_argument("--disable-gpu")
    opcoes.add_argument("--disable-software-rasterizer")

    navegador = uc.Chrome(options=opcoes, service=servico, version_main=152)
    navegador.maximize_window()
    estado["navegador"] = navegador


    try:
        for atividade in lista_atividades:

            # ── Survey pré-atividade ─────────────────────────────
            try:
                cansaco = perguntar_com_validacao(navegador, "Nível de cansaço antes da atividade? (1–10)", 120) #verificar função
            except (NoSuchWindowException, WebDriverException, UnexpectedAlertPresentException):
                print("[selenium] Navegador fechado durante survey pré-atividade. Encerrando.")
                estado["executando"] = False #encerra o funcionamento do programa e fecha as threads
                return

            escrever_survey(escritor_csv_survey, lock_csv,time.time(), atividade, "antes", "cansaco", cansaco,) #verificar
            print(f"[survey] Cansaço antes: {cansaco}")

            # ── Navegar para a atividade ─────────────────────────
            estado["atividade_atual"] = atividade #url da atividade atual, mudar o csv
            try:
                navegador.get(atividade) #abrir a atividade no navegador
            except (NoSuchWindowException, WebDriverException):
                print("[selenium] Navegador fechado ao navegar. Encerrando.")
                estado["executando"] = False
                return

            # ── Aguardar o participante terminar (redirecionado para /archive) ──
            print(f"[selenium] Aguardando conclusão de {atividade} ...")
            while True:
                try:
                    if not navegador.window_handles:
                        estado["executando"] = False
                        return
                    if "/archive" in navegador.current_url: #navegador.current_url é o que vamos usar pra fazer a validação da janela ativa
                        break
                except (NoSuchWindowException, WebDriverException, UnexpectedAlertPresentException):
                    print("[selenium] Janela perdida durante atividade. Encerrando.")
                    estado["executando"] = False
                    return
                except Exception as e:
                    print(f"[selenium] Erro inesperado no loop de espera: {e}")
                    estado["executando"] = False
                    return
                time.sleep(1)

            # ── Survey pós-atividade ─────────────────────────────
            try:
                frustracao = perguntar_com_validacao(navegador, "Nível de frustração após a atividade? (1–10)", 120)
            except (NoSuchWindowException, WebDriverException, UnexpectedAlertPresentException):
                print("[selenium] Navegador fechado durante survey pós-atividade. Encerrando.")
                estado["executando"] = False
                return

            escrever_survey(escritor_csv_survey, lock_csv,time.time(), atividade, "apos", "frustracao", frustracao,)
            print(f"[survey] Frustração depois: {frustracao}")
            print(f"\n✅ {atividade} — cansaço: {cansaco} | frustração: {frustracao}\n")

    finally:
        # Sempre sinaliza as threads para parar e fecha o navegador
        estado["executando"] = False #encerra quando todas as atividadesda lista foram concluídas
        try:
            navegador.quit()
        except Exception:
            pass
        print("[selenium] Experimento finalizado.")
