#Coordena as threads do Selenium, monitor de janelas e monitor de teclado.
#Todo o cálculo é adiado para o pós-processamento; apenas eventos brutos são escritos aqui.

import webbrowser, monitor_window, monitor_code, threading, selenium_runner
import csv
import threading
from pathlib import Path


# Estado compartilhado do experimento (leituras/escritas thread-safe via GIL para tipos simples)
estado = {
    "executando": True,          # se o programa está ativo
    "atividade_atual": "",       # URL atual do freecodecamp
    "janela_focada_titulo": "",  # Título da janela ativa
    "na_aba_da_tarefa": False,   # True quando freecodecamp está em foco
    "url_ativa": "",             # URL ativa no momento
    "navegador": None,           # referência ao WebDriver, preenchida por selenium_runner
}

# Lock para escritas thread-safe nos CSVs
lock_csv = threading.Lock()
# Lock para proteger comandos no WebDriver entre threads
lock_navegador = threading.Lock()   


# ──────────────────────────────────────────────
# Inicialização dos CSVs
# ──────────────────────────────────────────────
def inicializar_csvs(id_usuario: str) -> dict:
    #Cria os três arquivos CSV com cabeçalhos e retorna os escritores abertos
    base = Path(".")

    caminho_nav = base / f"usuario_{id_usuario}_navegacao.csv"
    caminho_tec = base / f"usuario_{id_usuario}_teclado.csv"
    caminho_srv = base / f"usuario_{id_usuario}_survey.csv"

    arquivo_nav = open(caminho_nav, "w", newline="", encoding="utf-8") #arquivo do monitor de telas
    arquivo_tec = open(caminho_tec, "w", newline="", encoding="utf-8") #arquivo do monitor de teclado
    arquivo_srv = open(caminho_srv, "w", newline="", encoding="utf-8") #arquivo do questionário de cansaço de frustração

    escritor_nav = csv.writer(arquivo_nav)
    escritor_tec = csv.writer(arquivo_tec)
    escritor_srv = csv.writer(arquivo_srv)

    escritor_nav.writerow(["timestamp", "url_janela_ativa", "janela_focada_titulo", "na_aba_da_tarefa"])
    escritor_tec.writerow(["timestamp", "atividade_atual", "janela_focada_titulo"])
    escritor_srv.writerow(["timestamp", "atividade_atual", "momento", "dimensao", "nota"])

    arquivo_nav.flush()
    arquivo_tec.flush()
    arquivo_srv.flush()

    print(f"[CSV] Arquivos criados:\n  {caminho_nav}\n  {caminho_tec}\n  {caminho_srv}")

    return {
        "nav": {"arquivo": arquivo_nav, "escritor": escritor_nav},
        "tec": {"arquivo": arquivo_tec, "escritor": escritor_tec},
        "srv": {"arquivo": arquivo_srv, "escritor": escritor_srv},
    }


def fechar_csvs(handles: dict) -> None:
    for handle in handles.values():
        try:
            handle["arquivo"].flush()
            handle["arquivo"].close()
        except Exception as e:
            print(f"[CSV] Erro ao fechar arquivo: {e}")


# ──────────────────────────────────────────────
# Encerramento da sessão
# ──────────────────────────────────────────────
def finalizar_sessao(id_usuario: str) -> None:
    print("\nObrigada por participar da pesquisa!")
    print("Você será redirecionado para o formulário NASA-TLX...")
    url = (
        "https://docs.google.com/forms/d/e/"
        "1FAIpQLScx9W64I_nljPGzolt0O_YwOpxafN1VdZvmOTFiXqFwSkGKvw/"
        f"viewform?usp=sharing&ouid={id_usuario}"
    )
    #webbrowser.open_new_tab(url)


# ──────────────────────────────────────────────
# Ponto de entrada
# ──────────────────────────────────────────────
def main():
    #pretendo mudar essa forma de pegar o id pelo input do usuário
    id_usuario = input("Digite o ID do participante (ex: 001): ").strip()
    if not id_usuario:
        id_usuario = "000" #se a pessoa não digitar, então o id vai ser esse

    handles = inicializar_csvs(id_usuario)

    # Threads de monitoramento em segundo plano (daemon=True para encerrar junto com o programa)
    thread_janela = threading.Thread(
        target=monitor_window.monitorar_janela, #função definida no arquivo monitor_window? vou ver melhor
        args=(estado, handles["nav"]["escritor"], lock_csv, lock_navegador),
        daemon=True,
        name="thread-janela",
    )
    thread_teclado = threading.Thread(
        target=monitor_code.rodar_monitor_teclado,
        args=(estado, handles["tec"]["escritor"], lock_csv),
        daemon=True,
        name="thread-teclado",
    )

    thread_janela.start()
    thread_teclado.start()

    # Selenium roda na thread principal para controlar o fluxo do experimento
    try:
        #verificar o selenium_runner.py pra ver a implementação dessa função, parametros, etc
        selenium_runner.rodar_experimento(estado=estado,escritor_csv_survey=handles["srv"]["escritor"],lock_csv=lock_csv, lock_navegador=lock_navegador)
    except KeyboardInterrupt:
        print("\n[!] Interrompido pelo usuário.")
    finally:
        # Sinaliza todas as threads para parar
        estado["executando"] = False

        # Aguarda os monitores finalizarem a iteração atual
        thread_janela.join(timeout=3)
        thread_teclado.join(timeout=3)

        fechar_csvs(handles)
        print("\n[✔] Dados salvos. Encerrando sessão...")
        finalizar_sessao(id_usuario)


if __name__ == "__main__":
    main()