import unittest

from airtouch2.at2plus.At2PlusClient import At2PlusClient
from airtouch2.protocol.at2plus.messages.AcStatus import AcStatusMessage


class TestKeepAlivePoll(unittest.IsolatedAsyncioTestCase):
    """The controller drops the session after ~16 min of silence; a periodic
    lightweight status request keeps it alive."""

    async def test_poll_sends_status_request(self):
        client = At2PlusClient("localhost")
        sent = []

        async def fake_send(msg):
            sent.append(msg)

        client._client.send = fake_send

        await client._send_keepalive_poll()

        self.assertEqual(len(sent), 1)
        self.assertIsInstance(sent[0], AcStatusMessage)
