import socket
from threading import Thread, Event
from StablePriorityQueue import StablePriorityQueue
from AT2Aircon import AT2Aircon
from protocol.constants import MessageLength

from protocol.messages import Message, CommandMessage, RequestState, ResponseMessage

class AT2Client:

    def __init__(self):
        self._host_ip: str = "192.168.1.15"
        self._host_port: int = 8899
        self._sock: socket.socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self._stop_threads: bool = True
        self._msg_queue: StablePriorityQueue[Message] = StablePriorityQueue()
        #self._cmd_queue: Queue[CommandMessage] = Queue()
        self._new_response: Event =  Event()
        self._aircons: list[AT2Aircon] = []
        self._threads: list[Thread] = []
        self._active: bool = False
        self._sock.settimeout(None)

    def __del__(self):
        self.stop()
    
    def start(self) -> None:
        self._connect()
        self._threads = [Thread(target=self._handle_incoming), Thread(target=self._main_loop)]
        #self._threads = [Thread(target=self._main_loop_nonblocking)]
        self._stop_threads = False
        for t in self._threads:
            t.start()
        self._active = True
        self.update_state()

    def _connect(self) -> bool:
        try:
            self._sock.connect((self._host_ip, self._host_port))
        except TimeoutError:
            print("Could not connect to airtouch 2 server")
            return False
        print("Connected to airtouch 2 server")
        return True

    def _stop_common(self):
        if self._active:
            self._stop_threads = True
            print("Closing socket...")
            self._sock.shutdown(socket.SHUT_RDWR)
            self._sock.close()
            # shutdown signal has highest priority
            self._msg_queue.put(None, priority=0)

    def _stop_and_join_main_thread(self):
        self._stop_common()
        self._threads[1].join()
        self._active = False

    def stop(self):
        self._stop_common()
        print("Joining threads...")
        for t in self._threads:
            t.join()
        self._active = False
        print("Shutdown successful")

    def send_command(self, command: CommandMessage) -> None:
        # commands have lower priority (2) than responses (1)
        self._msg_queue.put(command, priority=2)

    def update_state(self):
        self.send_command(RequestState())

    def _await_response(self) -> bytes:
        # taken (almost) straight from https://docs.python.org/3/howto/sockets.html
        chunks = []
        bytes_recd = 0
        while bytes_recd < MessageLength.RESPONSE:
            chunk = self._sock.recv(MessageLength.RESPONSE - bytes_recd) if not self._stop_threads else b''
            if chunk == b'':
                print("Socket connection broken")
                break
            chunks.append(chunk)
            bytes_recd = bytes_recd + len(chunk)
        return b''.join(chunks)

    def _handle_incoming(self) -> None:
        socket_broken = False
        while not self._stop_threads:
            resp = self._await_response()
            if len(resp) == 0:
                socket_broken = True
                break
            if len(resp) != MessageLength.RESPONSE:
                print("Invalid response, skipping")
                continue
            # responses have higher priority (1) than commands (2)
            self._msg_queue.put(ResponseMessage(resp), priority=1)
            self._new_response.set()
        
        if not self._stop_threads and socket_broken:
            print("Socket connection was broken, trying to recover...")
            print("Stopping main thread...")
            self._stop_and_join_main_thread()
            print("Restarting client...")
            # get a new socket
            self._sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            self.start()
    
    def _process_response(self, msg: ResponseMessage):
        # check message if there are 1 or 2 aircons - not sure how to do this yet
        # do the stuff, update aircons, zones etc...
        if not self._aircons:
            self._aircons.append(AT2Aircon(0, self, msg))
        else:
            for aircon in self._aircons:
                aircon.update(msg)

    def _main_loop(self) -> None:
        """Main loop"""
        # for every command sent there should be a response from the server that we should read first
        # if there are no commands to send than we should just wait for a response message to be emitted
        while not self._stop_threads:
            # wait for either new command msg or new response msg, response has higher priority in this queue
            msg: Message = self._msg_queue.get()

            # shutdown signal, None is put on the queue by _stop_common()
            if msg is None:
                break

            print(f"Got {msg.__class__.__name__} from queue")
            if isinstance(msg, CommandMessage):
                self._new_response.clear()
                self._sock.sendall(msg.serialize())
                # for every command sent, there should be a response, so wait for it
                self._new_response.wait()

            if isinstance(msg, ResponseMessage):
                # probably should compute and check hash then request again if mismatch
                print("Received response message:")
                self._process_response(msg)
                for aircon in self._aircons:
                    print(aircon)
