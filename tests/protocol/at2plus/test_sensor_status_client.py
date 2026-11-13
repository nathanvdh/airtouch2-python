import unittest

from airtouch2.at2plus.At2PlusClient import At2PlusClient
from airtouch2.protocol.at2plus.messages.SensorStatus import SensorStatus, SensorStatusMessage


class TestClientSensorStatus(unittest.IsolatedAsyncioTestCase):
    def _client(self) -> At2PlusClient:
        return At2PlusClient("localhost")

    async def test_sensor_readings_are_stored(self):
        client = self._client()
        await client._handle_sensor_status_message(
            SensorStatusMessage([SensorStatus(0x90, 22.5), SensorStatus(0x91, None)]))
        self.assertEqual(client.sensors_by_id[0x90].temperature, 22.5)
        self.assertIsNone(client.sensors_by_id[0x91].temperature)

    async def test_later_message_updates_reading(self):
        client = self._client()
        await client._handle_sensor_status_message(SensorStatusMessage([SensorStatus(0x90, 22.5)]))
        await client._handle_sensor_status_message(SensorStatusMessage([SensorStatus(0x90, 22.4)]))
        self.assertEqual(client.sensors_by_id[0x90].temperature, 22.4)

    async def test_callback_fires_on_update_and_can_be_removed(self):
        client = self._client()
        calls = []
        remove = client.add_sensor_callback(lambda: calls.append(1))
        await client._handle_sensor_status_message(SensorStatusMessage([SensorStatus(0x90, 22.5)]))
        self.assertEqual(len(calls), 1)
        remove()
        await client._handle_sensor_status_message(SensorStatusMessage([SensorStatus(0x90, 22.4)]))
        self.assertEqual(len(calls), 1)
