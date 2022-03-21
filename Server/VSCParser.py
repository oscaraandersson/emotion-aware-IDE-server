import threading
import time
import socket

MESSAGE_LEN = 19
PLACEHOLD_MSG = '\0'*(MESSAGE_LEN-1) + '\1'
class MsgBuffer:
        def __init__(self, size_N = 10):
            # Max number of messages
            self._N = size_N
            # Size of buffer
            self._size = 0
            # Buffer
            self._buffer = [bytes(PLACEHOLD_MSG, 'utf-8') for i in range(self._N)]
            # Keep track of unread messages
            self.semaphore = threading.Semaphore(0)
            # Manipulation of shared space safely
            self._b_lock = threading.Lock()
            self.head = 0
            self.tail = 0
        
        def _inc(self, index):
            # Frequently used incrementation
            return (index+1)%self._N

        def get_next(self):
            ''' Returns next message to send from buffer '''
            # Down on semaphore, block if there is no message in buffer
            self.semaphore.acquire()
            # Enter critical region
            self._b_lock.acquire()
            # Get latest message and increment counter, update size
            msg = self._buffer[self.head]
            self.head = self._inc(self.head)
            self._size -= 1
            # Exit critical region
            self._b_lock.release()
            return msg
        
        def add_msg(self, msg:bytes):
            """ 
            args:
                msg: message to add to buffer
            """
            # Enter critical region
            self._b_lock.acquire()
            self._buffer[self.tail] = msg
            if self._size != self._N:
                # Buffer is not full, normal procedure
                self.semaphore.release()
                self._size += 1
            else:
                # Buffer is full, adjust tail
                self.head = self._inc(self.head)
            self.tail = self._inc(self.tail)
            # Exit critical region
            self._b_lock.release()
        
        def force_last_msg(self, msg:bytes):
            """
            args: 
                msg: message to force into top of list
            """
            # Enter critical region
            self._b_lock.acquire()
            # Overwrite next element in list with msg
            self._buffer[self.head] = msg
            if self._size == 0:
                # Must let server know there is a new message
                self.tail = self._inc(self.tail)
                self.semaphore.release()
                self._size += 1
            # Exit critical region
            self._b_lock.release()

class VSCParser:
    def __init__(self, port, frequency = 1):
        self.host = "127.0.0.1"
        self.port = port
        self.js_client = None
        self.js_addr = ""
        self._freq = frequency
        self._notify_lst = []
        # Set up socket
        self.socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            # Tries to bind socket to port
        self.socket.bind((self.host, self.port))
        self.running = False
        # Create message handler
        self._buffer = MsgBuffer()
        # Initialize end message, let client know server is shutting down
        self._END_MSG = bytes('\0'*MESSAGE_LEN,"utf-8")
        # Thread lock, pasuing the server
        self._pause_lock = threading.Event()
        self.paused = False
    
    def __del__(self):
        if self.js_client != None:
            self.js_client.close()
        try:
            self.socket.close()
        except Exception:
            pass
    
    def add_notify(self, func):
        self._notify_lst.append(func)
    
    def _notify_exit(self):
        for func in self._notify_lst:
            func()
    
    def start_server(self):
        # Called with a new thread
        if not self.running:
            ACC_CLIENTS = 1
            self.socket.listen(ACC_CLIENTS)
            self.js_client, self.js_addr = self.socket.accept()
            print("Connected by:",self.js_addr)
            self._pause_lock.set()
            self.running = True
            print("Starting transmission.")
            self._instance()

    def _instance(self):
        while self.running:
            # Lock if the server is paused
            self._pause_lock.wait()
            # Get next message from buffer
            byte_msg = self._buffer.get_next()
            # Send message to client
            self.js_client.send(byte_msg)
            # Stop running if message is END_MSG
            if byte_msg == self._END_MSG:
                self.running = False
            else:
                time.sleep(1/self._freq)
        self._notify_exit()

    def pause(self):
        self._pause_lock.clear()
        self.paused = True
    
    def unpause(self):
        self._pause_lock.set()
        self.paused = False
    
    def buffer_message(self, msg:bytes):
        # Add message to buffer, make sure message is correct size
        if len(msg) != MESSAGE_LEN:
            return False
        self._buffer.add_msg(msg)
        return True
    
    def force_buffer_message(self, msg:bytes):
        # Force message to head of queue, make sure message is correct size
        if len(msg) != MESSAGE_LEN:
            return False
        self._buffer.force_last_msg(msg)
        return True

    def send_all_stop(self):
        # Empty buffer before exit
        self._buffer.add_msg(self._END_MSG)
        self.unpause()
    
    def force_stop(self):
        # Skip all messages in buffer and exit
        self._buffer.force_last_msg(self._END_MSG)
        self.unpause()


