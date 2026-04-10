import webbrowser, models, monitor_window, monitor_code, threading

#usar thread pra fazer múltiplas tarefas (monitorar janela e monitorar arquivo) ao mesmo tempo

id_usuario = 0 #vou trocar

def main():
    #observer.start()
    #time.sleep(1)

    finalizar_sessao(id_usuario)
    

def finalizar_sessao(id_usuario):
    print('Obrigada por participar da pesquisa!')
    print('Você será redirecionado para o forms onde irá responder o questionário NASA-TLX')
    
    url = f'https://docs.google.com/forms/d/e/1FAIpQLScx9W64I_nljPGzolt0O_YwOpxafN1VdZvmOTFiXqFwSkGKvw/viewform?usp=sharing&ouid={id_usuario}'

    webbrowser.open_new_tab(url)

if __name__ == "__main__":
    main()