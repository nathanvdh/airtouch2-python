import errno
import socket
import logging

from threading import Thread, Event
from queue import Empty, Queue
from time import sleep
from typing import Callable

from airtouch2.AT2Aircon import AT2Aircon

from airtouch2.protocol.constants import MessageLength
from airtouch2.protocol.messages import CommandMessage, RequestState, ResponseMessage

SocketClosedErrors = (errno.ECONNABORTED,  errno.ECONNRESET, errno.ENOTCONN, errno.ESHUTDOWN, errno.ECONNREFUSED)

_LOGGER = logging.getLogger(__name__)

class AT2Client:

    def __init__(self, host: str):
        self._host_ip: str = host
        self._host_port: int = 8899
        self._sock: socket.socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self._sock.settimeout(None)
        self._stop_threads: bool = True
        self._cmd_queue: Queue[CommandMessage] = Queue()
        self._last_response: ResponseMessage = None
        self._new_response: Event =  Event()
        self._new_response_or_command: Event = Event()
        self.aircons: list[AT2Aircon] = []
        self.system_name = "UNKNOWN"
        self._threads: list[Thread] = []
        self._active: bool = False
        self._callbacks: list[Callable] = []
        self._socket_broken = False
        self._data_updated = Event()

    def __del__(self):
        self.stop()
    
    def start(self) -> bool:
        if not self._connect():
            return False
        self._threads = [Thread(target=self._handle_incoming), Thread(target=self._main_loop)]
        self._stop_threads = False
        for t in self._threads:
            t.start()
        self._active = True
        self.update_state()
        return True

    def _connect(self) -> bool:
        _LOGGER.debug(f'Connecting to {self._host_ip} on port {self._host_port}')
        try:
            self._sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            self._sock.settimeout(None)
            self._sock.connect((self._host_ip, self._host_port))
        except OSError as e:
            _LOGGER.warning(f"Could not connect to host {self._host_ip}")
            if isinstance(e, socket.gaierror):
                pass
            elif e.errno not in (errno.EHOSTUNREACH, errno.ECONNREFUSED,  errno.ETIMEDOUT):
                raise e
            self._sock.close()
            return False
        _LOGGER.debug("Connected to airtouch2 server")
        return True

    def _stop_common(self):
        if self._active:
            self._stop_threads = True
            _LOGGER.debug("Closing socket...")
            try:
                self._sock.shutdown(socket.SHUT_RDWR)
            except OSError as e:
                if e.errno not in SocketClosedErrors:
                    raise e
                _LOGGER.debug(f"Socket shutdown() call failed:\n  OSError: [Errno {e.errno}] {e.strerror}")
            self._sock.close()
            self._data_updated.clear()
            self._new_response_or_command.set()

    def _reset(self):
        self._new_response_or_command.clear()
        self._new_response.clear()
        self._data_updated.clear()
        self.aircons.clear()
        self._threads.clear()
        self._socket_broken = False
        self._active = False
        self._last_response = None
        self._stop_threads = True
        self.system_name = "UNKNOWN"
        while not self._cmd_queue.empty():
            try:
                self._cmd_queue.get_nowait()
            except Empty:
                pass

    def _stop_and_join_main_thread(self):
        self._stop_common()
        _LOGGER.debug("Joining main thread")
        self._threads[1].join()
        self._reset()

    def stop(self):
        self._stop_common()
        _LOGGER.debug("Joining threads...")
        for t in self._threads:
            t.join()
        self._reset()
        _LOGGER.debug("Shutdown successful")


    def add_callback(self, func: Callable):
        self._callbacks.append(func)
        def remove_callback() -> None:
            if func in self._callbacks:
                self._callbacks.remove(func)

        return remove_callback

    def send_command(self, command: CommandMessage) -> None:
        self._cmd_queue.put(command)
        self._new_response_or_command.set()

    def update_state(self):
        self._data_updated.clear()
        self.send_command(RequestState())
        self._data_updated.wait()

    def _await_response(self) -> bytes:
        # taken (almost) straight from https://docs.python.org/3/howto/sockets.html
        chunks = []
        bytes_recd = 0
        while bytes_recd < MessageLength.RESPONSE:
            try:
                chunk = self._sock.recv(MessageLength.RESPONSE - bytes_recd) if not self._stop_threads else b''
            except OSError as e:
                if e.errno not in SocketClosedErrors:
                    raise e
                chunk=b''
            if chunk == b'':
                _LOGGER.debug("Socket closed/broken")
                break
            chunks.append(chunk)
            bytes_recd = bytes_recd + len(chunk)
        return b''.join(chunks)

    def _handle_incoming(self) -> None:
        while not self._stop_threads:
            resp = self._await_response()
            if len(resp) == 0:
                self._socket_broken = True
                break
            if len(resp) != MessageLength.RESPONSE:
                _LOGGER.warning("Received invalid response, ignoring")
                continue
            _LOGGER.debug("handle_incoming received new response")
            self._last_response = ResponseMessage(resp)
            self._new_response.set()
            self._new_response_or_command.set()

        if not self._stop_threads and self._socket_broken:
            _LOGGER.debug("Socket connection was broken, trying to recover...")
            self._stop_and_join_main_thread()
            _LOGGER.debug("Restarting client...")
            retries = 0
            while not self.start():
                sleep(0.001 * (10**retries) if retries < 4 else 10)
                retries+=1
                if not retries % 50:
                    _LOGGER.debug("Server is not responding, will continue trying to reconnect every 10s")

    def _process_last_response(self):
        # only process if we have a new one
        if self._last_response:
            resp = self._last_response
            self._last_response = None
            self._new_response.clear()
            self._new_response_or_command.clear()
            # check message if there are 1 or 2 aircons - not sure how to do this yet
            # do the stuff, update aircons, zones etc...
            if not self.aircons:
                self.aircons.append(AT2Aircon(0, self, resp))
                _LOGGER.debug(self.aircons[0])
            else:
                for aircon in self.aircons:
                    aircon.update(resp)
                    _LOGGER.debug(aircon)
            self._data_updated.set()
            for func in self._callbacks:
                _LOGGER.debug("Triggering callback")
                func()

    def _main_loop(self) -> None:
        """Main loop"""
        while not self._stop_threads:
            # wait for either a server message to be emitted or a command to be put on the queue
            _LOGGER.debug("Waiting for new data to receive or command to send")
            self._new_response_or_command.wait()
            _LOGGER.debug("Main loop waiter Event triggered")
            # process a message if that's what triggered the event
            self._process_last_response()
            
            # process commands if that's what triggered the event
            while self._cmd_queue.qsize() > 0 and not self._socket_broken:
                _LOGGER.debug("There are commands in the queue")
                try:
                    cmd = self._cmd_queue.get(block=False)
                except Empty:
                    _LOGGER.debug("Command queue was empty")
                    break
                self._new_response.clear()
                _LOGGER.debug(f"Sending {cmd.__class__.__name__}")
                if not self._socket_broken:
                    self._sock.sendall(cmd.serialize())
                    self._new_response.wait()
                    self._process_last_response()
