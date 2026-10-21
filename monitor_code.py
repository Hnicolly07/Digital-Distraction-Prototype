# Registra cada tecla pressionada como um evento bruto com timestamp
# Usa um listener pynput não-bloqueante para permitir encerramento limpo via estado["executando"]
import csv
import threading
import time
from pynput import keyboard

#ALTERAR
def escrever_linha_teclado(escritor: csv.writer,lock: threading.Lock,timestamp: float,atividade_atual: str,titulo_janela: str,) -> None:
    with lock:
        escritor.writerow([timestamp, atividade_atual, titulo_janela]) #ALTERAR


def rodar_monitor_teclado(estado,escritor_csv,lock_csv) -> None:

    def ao_pressionar_tecla(tecla):
        # Callback chamado pela thread interna do pynput — deve ser rápido
        if not estado["executando"]:
            return False  # Retornar False encerra o listener
        
        if not estado["na_aba_da_tarefa"]: #vai garantir que só funcione na janela focada FALTA TESTAR!!
            
            return
        
        timestamp = time.time()
        escrever_linha_teclado(escritor_csv,lock_csv,timestamp,estado["atividade_atual"],estado["janela_focada_titulo"],) #ALTERAR

    print("[monitor_teclado] Monitor de teclado iniciado.")

    # Início não-bloqueante — evita que Listener.join() trave o encerramento no Windows
    listener = keyboard.Listener(on_press=ao_pressionar_tecla)
    listener.start()

    # Loop de espera: verifica o estado a cada 0,5 s para encerramento rápido
    while estado["executando"]:
        time.sleep(0.5)

    # Para o listener pynput de forma limpa quando executando → False
    listener.stop()
    print("[monitor_teclado] Thread encerrada.")

#pseudocódigo
# Quando o usuario apertar um botão, e tiver na aba da IDE: Ele vai pegar o horario e vai registrar.
# Quando o usuario sair da IDE, ele vai registrar e vai esperar com que ele volte pra aba.
# Quando o usuario voltar pra aba, ele vai contar o tempo até o primeiro clique