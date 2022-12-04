import errno
import socket
import logging

from threading import Thread, Event
from queue import Empty, Queue
from time import sleep
from typing import Callable
from datetime import datetime

from airtouch2.AT2Aircon import AT2Aircon
from airtouch2.AT2Group import AT2Group

from airtouch2.protocol.constants import MessageLength
from airtouch2.protocol.messages import RequestState, ResponseMessage
from airtouch2.protocol.messages.CommandMessage import CommandMessage

from airtouch2.diff_bytes import print_diff_with_addresses

SocketClosedErrors = (errno.ECONNABORTED,  errno.ECONNRESET,
                      errno.ENOTCONN, errno.ESHUTDOWN, errno.ECONNREFUSED)

NetworkOrHostDownErrors = (errno.EHOSTUNREACH, errno.ECONNREFUSED,  errno.ETIMEDOUT, errno.ENETDOWN, errno.ENETUNREACH, errno.ENETRESET, errno.ECONNABORTED)

_LOGGER = logging.getLogger(__name__)

class AT2Client:

    def __init__(self, host: str, dump: bool=False):
        self._host_ip: str = host
        self._host_port: int = 8899
        self._sock: socket.socket = socket.socket(
            socket.AF_INET, socket.SOCK_STREAM)
        self._sock.settimeout(None)
        self._stop_threads: bool = True
        self._cmd_queue: Queue[CommandMessage] = Queue()
        self.newest_response: ResponseMessage = None
        self._previous_response: bytes = None
        self._new_response: Event = Event()
        self._new_response_or_command: Event = Event()
        self.aircons: list[AT2Aircon] = []
        self.groups: list[AT2Group] = []
        self.system_name = "UNKNOWN"
        self._threads: list[Thread] = []
        self._active: bool = False
        self._callbacks: list[Callable] = []
        self._socket_broken = False
        self._data_updated = Event()
        self._dump = dump

    def __del__(self):
        if self._active:
            self.stop()

    def start(self) -> bool:
        if not self._connect():
            return False
        self._threads = [Thread(target=self._handle_incoming),
                         Thread(target=self._main_loop)]
        self._stop_threads = False
        for t in self._threads:
            t.start()
        self._active = True
        self.update_state()
        return True

    def _connect(self) -> bool:
        _LOGGER.debug(
            f'Connecting to {self._host_ip} on port {self._host_port}')
        try:
            self._sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            self._sock.settimeout(None)
            self._sock.connect((self._host_ip, self._host_port))
        except OSError as e:
            _LOGGER.warning(f"Could not connect to host {self._host_ip}")
            if isinstance(e, socket.gaierror):
                # provided ip or port is rubbish/invalid
                pass
            elif e.errno not in NetworkOrHostDownErrors:
                raise e
            self._sock.close()
            return False
        _LOGGER.debug("Connected to airtouch2 server")
        return True

    def _shutdown_and_close_socket(self):
        try:
            self._sock.shutdown(socket.SHUT_RDWR)
        except OSError as e:
            if e.errno not in SocketClosedErrors:
                raise e
            _LOGGER.debug(
                f"Socket shutdown() call failed:\n  OSError: [Errno {e.errno}] {e.strerror}")
        self._sock.close()

    def _reset(self):
        # Originally in here I was also resetting self.aircons. In the context of this
        # client its fine, it will find them again when it gets a response message.
        # However the homeassistant entity is created with a reference to an aircon
        # which is then cleared so either it can't be cleared (hence why I removed it)
        # or there needs to be some callback that updates the homeassistant entity with
        # the new objet.
        self._new_response_or_command.clear()
        self._new_response.clear()
        self._data_updated.clear()
        self._socket_broken = False
        self.newest_response = None
        self.system_name = "UNKNOWN"
        # get rid of any commands on the queue
        while not self._cmd_queue.qsize() == 0:
            try:
                self._cmd_queue.get_nowait()
            except Empty:
                pass

    def stop(self):
        if self._active:
            self._stop_threads = True
            _LOGGER.debug("Closing socket...")
            self._shutdown_and_close_socket()
            self._data_updated.clear()
            self._new_response_or_command.set()
            _LOGGER.debug("Joining threads...")
            for t in self._threads:
                t.join()
            self._reset()
            self._threads.clear()
            self._active = False
            _LOGGER.debug("Shutdown successful")

        else:
            _LOGGER.debug("stop() called when client already inactive")

    def add_callback(self, func: Callable):
        self._callbacks.append(func)

        def remove_callback() -> None:
            if func in self._callbacks:
                self._callbacks.remove(func)

        return remove_callback

    def send_command(self, command: CommandMessage) -> None:
        self._cmd_queue.put(command)
        self._new_response_or_command.set()

    def update_state(self, block=True):
        self._data_updated.clear()
        self.send_command(RequestState())
        if block:
            self._data_updated.wait()

    def _reconnect(self) -> None:
        _LOGGER.debug("Reconnecting client...")
        self._shutdown_and_close_socket()
        self._reset()
        retries = 0
        while not self._connect():
            sleep(0.001 * (10**retries) if retries < 4 else 10)
            retries += 1
            if not retries % 50 or retries == 4:
                _LOGGER.debug(
                    "Server is not responding, will continue trying to reconnect every 10s")
        self.update_state(block=False)

    def _await_response(self) -> bytes:
        # taken (almost) straight from https://docs.python.org/3/howto/sockets.html
        chunks = []
        bytes_recd = 0
        while bytes_recd < MessageLength.RESPONSE:
            try:
                chunk = self._sock.recv(
                    MessageLength.RESPONSE - bytes_recd) if not self._stop_threads else b''
            except OSError as e:
                if e.errno not in SocketClosedErrors:
                    raise e
                chunk = b''
            if chunk == b'':
                # socket broken or closed
                break
            chunks.append(chunk)
            bytes_recd = bytes_recd + len(chunk)
        return b''.join(chunks)

    def _handle_incoming(self) -> None:
        while not self._stop_threads:
            while not self._socket_broken:
                resp = self._await_response()
                if len(resp) == 0:
                    self._socket_broken = True
                    break
                if len(resp) != MessageLength.RESPONSE:
                    _LOGGER.warning("Received invalid response, ignoring")
                    continue
                _LOGGER.debug("Received new valid response")
                self.newest_response = ResponseMessage(resp)
                self._new_response.set()
                self._new_response_or_command.set()
                if self._dump:
                    if self._previous_response:
                        print_diff_with_addresses(self._previous_response, resp)
                    with open('response_' + datetime.now().strftime("%m-%d-%Y_%H-%M-%S") + '.dump', 'wb') as f:
                        f.write(resp)
                self._previous_response = resp

            if not self._stop_threads and self._socket_broken:
                _LOGGER.debug("Socket connection was broken")
                self._reconnect()

    def _process_last_response(self):
        self._new_response.clear()
        self._new_response_or_command.clear()
        resp = self.newest_response
        self.newest_response = None
        # TODO: Check if dual unit system and handle 2 ACs
        # Aircons / units
        if not self.aircons:
            self.aircons.append(AT2Aircon(0, self, resp))
            _LOGGER.debug(self.aircons[0])
        else:
            for aircon in self.aircons:
                aircon.update(resp)
                _LOGGER.debug(aircon)
        # Groups
        if not self.groups or len(self.groups) != resp.num_groups:
            # TODO: callback to inform homeassistant
            self.groups.clear()
            for i in range(resp.num_groups):
                self.groups.append(AT2Group(self, i, resp))
        else:
            for group in self.groups:
                group.update(resp)
                _LOGGER.debug(group)
        self._data_updated.set()
        for func in self._callbacks:
            func()

    def _main_loop(self) -> None:
        """Main loop"""
        while not self._stop_threads:
            # wait for either a server message to be emitted or a command to be put on the queue
            _LOGGER.debug("Waiting for new data to arrive or command to send")
            self._new_response_or_command.wait()
            _LOGGER.debug("Main loop waiter Event triggered")
            # process a message if that's what triggered the event
            if self.newest_response:
                self._process_last_response()

            # process commands if that's what triggered the event
            while self._cmd_queue.qsize() > 0 and not self._socket_broken:
                _LOGGER.debug("There are commands in the queue")
                try:
                    cmd = self._cmd_queue.get(block=False)
                except Empty:
                    _LOGGER.debug("Tried to get command but queue was empty")
                    break
                self._new_response.clear()
                if not self._socket_broken:
                    _LOGGER.debug(f"Sending {cmd.__class__.__name__}")
                    self._sock.sendall(cmd.serialize())
                    self._new_response.wait(timeout=5)
                    if self.newest_response:
                        self._process_last_response()
