import socket
from threading import Thread, Event
from queue import PriorityQueue
from AT2Aircon import AT2Aircon
from protocol.constants import MessageLength
from protocol.enums import MessageType

from protocol.messages import Message, CommandMessage, RequestState, ResponseMessage

class AT2Client:

    def __init__(self):
        self._host_ip: str = "192.168.1.15"
        self._host_port: int = 8899
        self._sock: socket.socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self._stop_threads: bool = True
        self._msg_queue: PriorityQueue[Message] = PriorityQueue()
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
        self._stop_threads = False
        for t in self._threads:
            t.start()
        self._active = True
        self.update_state()

    def stop(self):
        # TODO: do socket programming properly with select so can cleanly shutdown
        if self._active:
            self._stop_threads = True
            print("Closing socket...")
            self._sock.shutdown(socket.SHUT_RDWR)
            self._sock.close()
            self._msg_queue.put(None)
            print("Joining threads...")
            for t in self._threads:
                t.join()
            self._active = False
            print("Shutdown successful")

    def _connect(self) -> bool:
        try:
            self._sock.connect((self._host_ip, self._host_port))
        except TimeoutError:
            print("Could not connect to airtouch 2 server")
            return False
        print("Connected to airtouch 2 server")
        return True

    def _await_response(self) -> bytes:
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

    def send_command(self, command: CommandMessage) -> None:
        self._msg_queue.put(command)

    def update_state(self):
        self.send_command(RequestState())

    def _handle_incoming(self) -> None:
        while not self._stop_threads:
            resp = self._await_response()
            if len(resp) != MessageLength.RESPONSE:
                print("Invalid response, skipping")
                continue
            self._msg_queue.put(ResponseMessage(resp))
            self._new_response.set()
    
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
        # for every command sent there should be a response from the server
        # sending many commands in a row can fail without adding a sleep() between them
        # to avoid wasting time sleeping, I want to just process any response messages before
        # sending any command messages, to achieve this a PriorityQueue is used where
        #last_msg_type: MessageType = MessageType.UNDETERMINED
        while not self._stop_threads:
            # wait for either new command msg or new response msg, response has higher priority
            msg: Message = self._msg_queue.get()
            # shutdown signal
            if msg is None:
                break
            
            print(f"Got {msg.type} from queue")
            
            if (msg.type == MessageType.COMMAND):
                self._new_response.clear()
                # serialize() only exists on CommandMessage
                self._sock.sendall(msg.serialize())
                # for every command sent, there should be a response, so wait for it
                self._new_response.wait()
            
            if (msg.type == MessageType.RESPONSE):
                # probably should compute hash and request again if mismatch
                print("Received response message:")
                self._process_response(msg)
                for aircon in self._aircons:
                    print(aircon)

            #last_msg_type = msg.type

