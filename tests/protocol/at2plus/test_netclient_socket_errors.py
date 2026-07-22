import unittest
from unittest.mock import AsyncMock, MagicMock

from airtouch2.common.NetClient import NetClient


class _StubMessage:
    def to_bytes(self) -> bytes:
        return b"\x00"


class TestNetClientSocketErrors(unittest.IsolatedAsyncioTestCase):
    """Regression tests for the zombie-client bug.

    When the controller drops off WiFi mid-connection, reads/writes fail with
    OSError [Errno 113] Host is unreachable - NOT ConnectionResetError. The
    old code only caught reset/timeout, so the read loop died un-handled and
    the client never reconnected (dead until restart). Any socket-level
    OSError must be treated as connection loss.
    """

    def _client(self) -> NetClient:
        return NetClient("localhost", 9200, AsyncMock(), AsyncMock())

    async def test_read_bytes_treats_host_unreachable_as_connection_loss(self):
        client = self._client()
        client._reader = MagicMock()
        client._reader.readexactly = AsyncMock(
            side_effect=OSError(113, "Host is unreachable"))
        client._try_reconnect = AsyncMock()

        result = await client.read_bytes(1)

        self.assertIsNone(result)          # signalled as a failed read...
        client._try_reconnect.assert_awaited()  # ...and reconnect kicked off

    async def test_send_reconnects_on_host_unreachable(self):
        client = self._client()
        dead_writer = MagicMock()
        dead_writer.drain = AsyncMock(
            side_effect=OSError(113, "Host is unreachable"))
        good_writer = MagicMock()
        good_writer.drain = AsyncMock()

        async def fake_reconnect():
            client._writer = good_writer

        client._writer = dead_writer
        client._try_reconnect = AsyncMock(side_effect=fake_reconnect)

        await client.send(_StubMessage())  # must not raise

        client._try_reconnect.assert_awaited()
        good_writer.drain.assert_awaited()
