# event.src_path.endswith('.py')
import time
from watchdog.observers import Observer
from watchdog.events import FileSystemEventHandler


class MyHandler(FileSystemEventHandler):
    def on_modified(self, event):
        if event.is_directory or not event.src_path.endswith('.py'):
            return 
        
        print(f'File {event.src_path} has been modified') #####

        #logica

        #elif event.event_type == 'created':
            # Event is created, you can process it now
            #print("Watchdog received created event - % s." % event.src_path)
        #elif event.event_type == 'modified':
            # Event is modified, you can process it now
            #print("Watchdog received modified event - % s." % event.src_path) ######
            
