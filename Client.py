from queue import Queue
import select
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

    def stop(self):
        # TODO: do socket programming properly with select so can cleanly shutdown
        if self._active:
            self._stop_threads = True
            print("Closing socket...")
            self._sock.shutdown(socket.SHUT_RDWR)
            self._sock.close()
            # shutdown signal has highest priority
            self._msg_queue.put(None, priority=0)
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
        # commands have lower priority than responses
        self._msg_queue.put(command, priority=2)
        #self._cmd_queue.put(command)

    def update_state(self):
        self.send_command(RequestState())

    def _handle_incoming(self) -> None:
        while not self._stop_threads:
            resp = self._await_response()
            if len(resp) != MessageLength.RESPONSE:
                print("Invalid response, skipping")
                continue
            # responses have higher priority than commands
            self._msg_queue.put(ResponseMessage(resp), priority=1)
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
        # for every command sent there should be a response from the server that we should read first
        # if there are no commands to send than we should just wait for a response message to be emitted
        while not self._stop_threads:
            # wait for either new command msg or new response msg, response has higher priority
            msg: Message = self._msg_queue.get()

            # shutdown signal
            if msg is None:
                break

            print(f"Got {msg.__class__.__name__} from queue")
            if isinstance(msg, CommandMessage):
                self._new_response.clear()
                self._sock.sendall(msg.serialize())
                # for every command sent, there should be a response, so wait for it
                self._new_response.wait()

            if isinstance(msg, ResponseMessage):
                # probably should compute hash and request again if mismatch
                print("Received response message:")
                self._process_response(msg)
                for aircon in self._aircons:
                    print(aircon)


    # I tried to do it with select, without the complicated StablePriorityQueue that contains both message types
    # but with non-blocking select() this is just polling and hence pegs the CPU 100% all the time
    # If I make select() block until _sock is ready to read then its the same as a blocking recv() which defeats the whole purpose of this,
    # I don't understand what to do here and I'm frustrated because surely this is common for client software
    # somebody please tell me how to do this properly
    # def _main_loop_nonblocking(self) -> None:
    #     """Use nonblocking sockets"""
    #     self._sock.setblocking(False)
    #     waiting_response = False
    #     while not self._stop_threads:
    #         #print("Top of loop")
    #         ready_to_read, _, _ = select.select([self._sock], [], [], 0)
    #         #print("select() call made")

    #         #if not (ready_to_read):
    #         #    print("Timed out")

    #         while ready_to_read:
    #             resp = self._await_response()
    #             if len(resp) != MessageLength.RESPONSE:
    #                 print("Invalid response, skipping")
    #             else:
    #                 self._process_response(ResponseMessage(resp))
    #                 waiting_response = False
    #                 for aircon in self._aircons:
    #                     print(aircon)
    #             #print("Making another select() call...")
    #             ready_to_read, _, _ = select.select([self._sock], [], [], 0)
    #             #print("select() call made")
            
    #         if not waiting_response:
    #             _, ready_to_write, _ = select.select([], [self._sock], [], 0)
    #             if ready_to_write:
    #                 if not self._cmd_queue.empty():
    #                     print("Sending command...")
    #                     self._sock.sendall(self._cmd_queue.get().serialize())
    #                     waiting_response = True


