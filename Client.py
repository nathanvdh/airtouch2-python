import socket
from threading import Thread, Event
from queue import Empty, Queue

from AT2Aircon import AT2Aircon

from protocol.constants import MessageLength
from protocol.messages import CommandMessage, RequestState, ResponseMessage

class AT2Client:

    def __init__(self):
        self._host_ip: str = "192.168.1.15"
        self._host_port: int = 8899
        self._sock: socket.socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self._stop_threads: bool = True
        self._cmd_queue: Queue[CommandMessage] = Queue()
        self._last_response: ResponseMessage = None
        self._new_response: Event =  Event()
        self._new_response_or_command: Event = Event()
        self._aircons: list[AT2Aircon] = []
        self._threads: list[Thread] = []
        self._active: bool = False
        self._sock.settimeout(None)

    def __del__(self):
        self.stop()
    
    def start(self) -> None:
        self._connect()
        self._threads = [Thread(target=self._handle_incoming), Thread(target=self._main_loop)]
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
            self._new_response_or_command.set()

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
        self._cmd_queue.put(command)
        self._new_response_or_command.set()

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
            print("handle_incoming received new response")
            self._last_response = ResponseMessage(resp)
            self._new_response.set()
            self._new_response_or_command.set()

        if not self._stop_threads and socket_broken:
            print("Socket connection was broken, trying to recover...")
            print("Stopping main thread...")
            self._stop_and_join_main_thread()
            print("Restarting client...")
            # get a new socket
            self._sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            self.start()

    def _process_last_response(self):
        # actually only process if we have a new one
        if self._last_response:
            resp = self._last_response
            self._last_response = None
            self._new_response.clear()
            self._new_response_or_command.clear()
            # check message if there are 1 or 2 aircons - not sure how to do this yet
            # do the stuff, update aircons, zones etc...
            if not self._aircons:
                self._aircons.append(AT2Aircon(0, self, resp))
                print(self._aircons[0])
            else:
                for aircon in self._aircons:
                    aircon.update(resp)
                    print(aircon)

    def _main_loop(self) -> None:
        """Main loop"""
        while not self._stop_threads:
            # wait for either a server message to be emitted or a command to be put on the queue
            print("Waiting for something to happen")
            self._new_response_or_command.wait()
            print("Something happened")
            # process a message if that's what triggered the event
            self._process_last_response()
            
            # process commands if that's what triggered the event
            while self._cmd_queue.qsize() > 0:
                print("There are commands in the queue")
                try:
                    cmd = self._cmd_queue.get(block=False)
                except Empty:
                    print("command queue was empty")
                    break
                self._new_response.clear()
                print(f"Sending {cmd.__class__.__name__}")
                self._sock.sendall(cmd.serialize())
                self._new_response.wait()
                self._process_last_response()
