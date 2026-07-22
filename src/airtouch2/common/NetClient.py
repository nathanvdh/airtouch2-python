import asyncio
import errno
import logging
import socket
from typing import Callable
from airtouch2.common.interfaces import CoroCallback, Serializable, TaskCreator

_LOGGER = logging.getLogger(__name__)

NetworkOrHostDownErrors = (errno.EHOSTUNREACH, errno.ECONNREFUSED,  errno.ETIMEDOUT,
                           errno.ENETDOWN, errno.ENETUNREACH, errno.ENETRESET, errno.ECONNABORTED)

def _set_keepalive_options(
    sock: socket.socket, idle_seconds: int, interval_seconds: int, count: int
):
    if hasattr(sock, "SO_KEEPALIVE"):
        sock.setsockopt(socket.SOL_SOCKET, socket.SO_KEEPALIVE, 1)
    if hasattr(sock, "TCP_KEEPIDLE"):
        sock.setsockopt(socket.IPPROTO_TCP, socket.TCP_KEEPIDLE, idle_seconds)
    if hasattr(socket, "TCP_KEEPINTVL"):
        sock.setsockopt(socket.IPPROTO_TCP, socket.TCP_KEEPINTVL, interval_seconds)
    if hasattr(socket, "TCP_KEEPCNT"):
        sock.setsockopt(socket.IPPROTO_TCP, socket.TCP_KEEPCNT, count)
    if hasattr(socket, "TCP_USER_TIMEOUT"):
        sock.setsockopt(
            socket.IPPROTO_TCP,
            socket.TCP_USER_TIMEOUT,
            1000 * (idle_seconds + (interval_seconds * count)),
        )

def _log_completed_task_exception(task: asyncio.Task[None]) -> None:
    try:
        _ = task.result()
    except asyncio.CancelledError:
        pass
    except Exception as e:
        _LOGGER.error(f"{task.get_name()} completed with an exception:\n{type(e).__name__}: {e}")

class NetClient:
    """A generic network client"""

    def __init__(self, host: str, port: int, on_connect: CoroCallback, handle_message: CoroCallback,
                 task_creator: TaskCreator = asyncio.create_task):
        # network
        self._host_ip: str = host
        self._host_port: int = port
        self._reader: asyncio.StreamReader | None = None
        self._writer: asyncio.StreamWriter | None = None

        # async
        self._task_creator: Callable = task_creator
        self._main_loop_task: asyncio.Task[None] | None = None
        self._stop: bool = False

        self._on_connect = on_connect
        self._handle_message = handle_message

    async def connect(self) -> bool:
        """Opens connection to the server, returns True/False if successful/unsuccessful"""
        _LOGGER.debug(f"Connecting to {self._host_ip} on port {self._host_port}")
        try:
            self._reader, self._writer = await asyncio.open_connection(self._host_ip, self._host_port)
        except OSError as e:
            _LOGGER.warning(f"Could not connect to host {self._host_ip}")
            if isinstance(e, socket.gaierror):
                # provided ip or port is rubbish/invalid
                pass
            elif e.errno not in NetworkOrHostDownErrors:
                raise e
            return False
        else:
            _set_keepalive_options(
                self._writer.get_extra_info("socket"),
                idle_seconds=5,
                interval_seconds=1,
                count=5,
            )
            await self._on_connect()
            return True

    def run(self) -> None:
        """Starts the processing of incoming information from the server"""
        _LOGGER.debug("Starting listener task")
        self._stop = False
        self._main_loop_task = self._task_creator(self._main(), name="Main loop task")
        # This task typically has no awaiter but it's possible it completes
        # with an exception, so add a done callback that logs exceptions.
        assert self._main_loop_task is not None
        self._main_loop_task.add_done_callback(_log_completed_task_exception)

    async def stop(self) -> None:
        """Stops the processing of incoming information from the server"""
        self._stop = True
        if self._main_loop_task is not None:
            self._main_loop_task.cancel()
            try:
                await self._main_loop_task
            except asyncio.CancelledError:
                # Eat the expected exception
                pass

    async def send(self, message: Serializable) -> None:
        """Send the serializable 'message'"""
        if self._writer is None:
            raise RuntimeError("Client is not connected - call connect() first")
        else:
            bytes_to_write = message.to_bytes()
            _LOGGER.debug(f"Sending {message.__class__.__name__} with data: {bytes_to_write.hex(':')}")
            _LOGGER.debug(f"{repr(message)}")
            self._writer.write(bytes_to_write)
            drained: bool = False
            while not drained:
                try:
                    await self._writer.drain()
                    drained = True
                except (ConnectionResetError, asyncio.IncompleteReadError, TimeoutError) as e:
                    await self._try_reconnect()

    async def read_bytes(self, size: int) -> bytes | None:
        """
        Read exactly 'size' bytes, return None if could not read enough bytes or on disconnection and reconnection.
        This coroutine handles reconnection.
        """
        if self._reader is None:
            raise RuntimeError("Client is not connected - call connect() first")
        try:
            data = await self._reader.readexactly(size)
        except asyncio.IncompleteReadError as e:
            _LOGGER.debug(f"IncompleteReadError - partial bytes: {e.partial.hex(':')}")
            data = None
        except (ConnectionResetError, TimeoutError) as e:
            _LOGGER.debug("ConnectionResetError")
            data = None

        if data is None:
            _LOGGER.warning("Connection lost, reconnecting")
            await self._try_reconnect()
            return None
        _LOGGER.debug(f"Read payload of size {size}: {data.hex(':')}")
        return data

    async def _main(self) -> None:
        while not self._stop:
            if not (self._reader and self._writer):
                raise RuntimeError("Client is not connected - call connect() first")
            await self._handle_message()

    async def _try_reconnect(self) -> None:
        retries = 0
        while not await self.connect():
            await asyncio.sleep(0.001 * (10**retries) if retries < 4 else 10)
            retries += 1
            if not retries % 60 or retries == 4:
                _LOGGER.info("Server is not responding, will continue trying to reconnect every 10s")
        _LOGGER.info("Reconnected")