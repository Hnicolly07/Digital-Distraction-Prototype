import pygetwindow as gw
#import watchdog
import time
import sqlite3

titulo_anterior = ""
relacionadas = ['Visual Studio Code', 'PyCharm','Python','Stack Overflow', 'Git', 'ChatGPT', 'Python Documentation','Documentation']
f = duracao = 0 #frequência de distração
  
while True:
    try:
        janela = gw.getActiveWindow()
        if janela is not None:
            titulo = janela.title
    
            if titulo not in relacionadas and titulo != titulo_anterior:
                f += 1
                # duração time.perf_counter() ou time.time()
        titulo_anterior = titulo

        time.sleep(3)
    except KeyboardInterrupt:
        print(f'Frequência de interrupções: {f}')
        print(f'Resumption Lag: {f * 5}') #(custo)