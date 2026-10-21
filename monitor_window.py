# rastreia mudanças de foco a cada segundo e escreve linhas brutas no CSV de navegação.
# classificação em relacionada e não relacionada foi removida, só será feita no processamento dos dados

import csv
import threading
import time
import pygetwindow as gw
import selenium_runner

# palavras-chave que indicam que o participante está na janela da tarefa
# no momento está apenas como freecodecamp mas penso em expandir
PALAVRA_TAREFA = "freecodecamp"


def eh_janela_da_tarefa(titulo) -> bool: #aqui não dá pra passar o titulo, tem que passar a url apenas
    #retorna True quando a janela ativa pertence à atividade do freecodecamp
    if PALAVRA_TAREFA in titulo.lower():
        return True
    return False


# VOU ALTERAR
def escrever_linha_nav(escritor,lock,timestamp,url_ativa,titulo,na_aba):
    #Adiciona uma linha de evento de navegação ao CSV de forma thread-safe
    with lock:
        #timestamp, url ativa no momento, titulo, true/false
        escritor.writerow([timestamp, url_ativa, titulo, na_aba])


def monitorar_janela(estado: dict,escritor_csv: csv.writer,lock_csv: threading.Lock,lock_navegador: threading.Lock,intervalo_poll: float = 1.0,) -> None:
    """
    Thread em segundo plano — roda enquanto estado["executando"] for True.

    A cada mudança de foco detectada:
      - Atualiza estado["janela_focada_titulo"] e estado["na_aba_da_tarefa"]
      - Escreve imediatamente uma linha de evento bruto no CSV de navegação
    """
    titulo_anterior: str = ""

    print("[monitor_janela] Monitoramento de janela iniciado.")

    while estado["executando"]: # esse estado está sendo controlado na main
        try:
            janela = gw.getActiveWindow() #pega a janela ativa no sistema (função do proprio pygetwindow)
            if janela is None: #se a janela estiver vazia
                time.sleep(intervalo_poll)
                continue #apenas continue esperando um titulo de janela aparecer

            titulo: str = janela.title or "" # "" se n tiver titulo

            if titulo != titulo_anterior: #se o titulo for diferente do titulo anterior já registrado, então houve uma mudança de janela
                timestamp = time.time() #pegue o momento exato da mudança
                na_aba = eh_janela_da_tarefa(titulo) #verifique se está na janela da tarefa principal (freecodecamp)

                navegador = estado.get("navegador")
                url_real = selenium_runner.obter_url_pela_titulo(navegador, lock_navegador, titulo)
                url_final = url_real if url_real is not None else ""

                # Atualiza estado compartilhado
                estado["janela_focada_titulo"] = titulo
                estado["na_aba_da_tarefa"] = na_aba 
                estado["url_ativa"] = url_final

                # escreve tudo no csv
                escrever_linha_nav(escritor_csv, lock_csv, timestamp, url_final, titulo, na_aba)
                # provavelmente vou mudar pra ter o timestamp final e inicial da atividade
                #  ou pegar o de inicio dessa e o inicio da proxima

                print(f"[monitor_janela] Foco → '{titulo}' | tarefa={na_aba}")
                titulo_anterior = titulo

        except Exception as e: #caso dê erro, ele vai printar o erro
            # Nunca deixa a thread de monitoramento cair — apenas loga e continua
            print(f"[monitor_janela] Erro ignorado: {e}")

        time.sleep(intervalo_poll)

    print("[monitor_janela] Thread encerrada.")