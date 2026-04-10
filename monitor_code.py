import time
from watchdog.observers import Observer
from watchdog.events import FileSystemEventHandler


class MyHandler(FileSystemEventHandler):
    def on_modified(self, event):
        if not event.is_directory and event.src_path.endswith('.py'):
            if event.event_type == 'modified':
                modificacao = time.strftime('%H:%M:%S',time.localtime(time.time()))
            return 

# pynput     
# Quando o usuario apertar um botão, e tiver na aba da IDE: Ele vai pegar o horario e vai registrar.
# Quando o usuario sair da IDE, ele vai registrar e vai esperar com que ele volte pra aba.
# Quando o usuario voltar pra aba, ele vai contar o tempo até o primeiro clique


        

    
            
