# Declarações
from groq import Groq
from dotenv import load_dotenv
import pygetwindow as gw
import os, time, json, sqlite3

load_dotenv()

client = Groq(
    api_key= os.getenv("GROQ_API_KEY"),
)

def main():
    tempo_inicio = time.time() # Define tempo_inicio como o horario de inicio do programa
    titulo_anterior = "" # Inicialiaza titulo_anterior, usada pra armazenar o nome da janela anterior
    f = duracao = 0 # Define f (frequencia de distração) e duração como 0
    janelas = []
    
    while True:
        try:
            janela = gw.getActiveWindow() # Define janela
            if janela is not None:
                titulo = janela.title # Define titulo como o titulo da janela atual
        
                duracao = round(time.time() - tempo_inicio)

                # Identifica a troca de janela
                if titulo is not None and titulo != titulo_anterior:
                    print(f"JANELA: {titulo}")
                    log = {"janela": titulo, "duração": duracao, "timestamp": time.strftime('%H:%M:%S',time.localtime(tempo_inicio))}
                    janelas.append(log)
                    tempo_inicio = time.time() # Reinicia o tempo do uso da janela

                
            titulo_anterior = titulo # Atualiza titulo da janela anterior
            
    
            time.sleep(1)
        except KeyboardInterrupt:
            print("\n--- [!] Monitoramento Finalizado pelo Usuário ---")
        
            if not janelas:
                print("Nenhum dado coletado.")
                return
            break

    # PASSO 1: Tentar classificar com a IA
    try:
        print("Enviando para classificação ... Aguarde.")
        janelas_classificadas = classifica_janela(janelas)
        
        if janelas_classificadas:
            print("Classificação concluída com sucesso!")

            # 1. Transformar o texto em um dicionário Python real
            dados_processados = json.loads(janelas_classificadas)

            for item in dados_processados["janelas"]:
                if item['categoria'] == "Non-Task-Related":
                    f += 1

            with open('classificacao.json', 'w', encoding='utf-8') as arquivo:
                json.dump(dados_processados, arquivo, indent=4, ensure_ascii=False)
                print("✔ Resultados salvos em 'classificacao.json'")
                print(f"Frequencia de Distrações: {f}")
                # Aqui entra o bglh de salvar no SQLite       
    except Exception as e:
        print(f"Erro na IA: {e}")

def classifica_janela(janelas):

    prompt = f"""Classifique a lista de janelas a seguir como Task-Related ou Non-Task-Related sabendo que a atividade principal da pessoa é programar em Python.
    Retorne apenas o JSON original com um novo campo chamado 'categoria'. No caso de janelas como youtube, verifique se o título do vídeo é relacionado.
    
    Dados: {json.dumps(janelas)}"""
    chat_completion = client.chat.completions.create(
        messages=[
            {
                "role": "user",
                "content": prompt
            }
        ],
        response_format={"type": "json_object"},
        model="llama-3.3-70b-versatile",
    )

    return chat_completion.choices[0].message.content

main()