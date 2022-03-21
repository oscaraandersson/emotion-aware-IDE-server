import threading
import sys
import socket
import time
from VSCParser import MESSAGE_LEN, VSCParser

def get_port(argv):
    if len(argv) != 2:
        print("Incorrect arguments!")
        return None
    try:
        port = int(sys.argv[1])
    except Exception as e:
        print(e)
        return None
    return port


class ServerManager:
    def __init__(self, port, frequency=1):
        # If fail to create server descructor does not recognize it
        self._destructor_bool = False
        # Create server
        self._srvr = VSCParser(port, frequency)
        # Create server thread
        self._srvr_thread = threading.Thread(target=self._srvr.start_server)
        self._destructor_bool = True
        self.shutting_down = False
        self.wait_for_stop = threading.Event()
        self.wait_for_stop.set()
        self._srvr.add_notify(self._unlock_wait)
    
    def __del__(self):
        # Safely dispose thread and server
        if self._destructor_bool and self._srvr_thread.is_alive():
            # Needs to shut down asap
            self._srvr.force_stop()
            self._srvr.unpause()
            # Wait for thread
            self._srvr_thread.join()
    
    def _unlock_wait(self):
        self.wait_for_stop.set()
    
    def wait_for_exit(self):
        if self.shutting_down:
            self.wait_for_stop.wait()
            self.shutting_down = False
        else:
            raise Exception(
                "Exit needs to be called before main thread waits for exit."
                )

    def start(self):
        if not self._srvr.running:
            self._srvr_thread.start()
        else:
            self._srvr.unpause()
    
    def stop(self):
        self._srvr.pause()
    
    def exit(self, force_exit = False):
        # Force exit or empty buffer first
        if self._srvr.running:
            if force_exit:
                self._srvr.force_stop()
            else:
                self._srvr.send_all_stop()
            self.shutting_down = True
            self.wait_for_stop.clear()
            self._srvr.unpause()
    
    def send(self, msg:bytes, jump_queue = False):
        # Force message or put in queue
        success = True
        if jump_queue:
            success = self._srvr.force_buffer_message(msg)
        else:
            success = self._srvr.buffer_message(msg)
        if not success:
            raise Exception("ServerManager.send: Message does not match the constant message length.")