import unittest

from airtouch2.protocol.at2plus.control_status_common import ControlStatusSubHeader, ControlStatusSubType
from airtouch2.protocol.at2plus.messages.SensorStatus import SENSOR_STATUS_LENGTH, SensorStatus, SensorStatusMessage

# Real 0x2B control/status data (subheader + subdata) captured from AirTouch 2+ consoles.
# Six 4-byte records: sensor id, second byte, 16-bit temperature (0x07ff = no reading).
# aramshaw's system (one console): only 0x90 has a reading.
CAPTURE_ARAMSHAW = bytes.fromhex("2b00000000040006808007ff818107ff828207ff838307ff90ff02c591ff07ff")
# kieranlee1970's system, from issue #21.
CAPTURE_KIERANLEE = bytes.fromhex("2b00000000040006808007ff818107ff828207ff838307ff90ff02d591ff07ff")


def _parse(data: bytes) -> SensorStatusMessage:
    subheader = ControlStatusSubHeader.from_bytes(data[:8])
    return SensorStatusMessage.from_bytes(data[8:8 + subheader.subdata_length.total()])


class TestSensorStatus(unittest.TestCase):
    def test_deserialize_reading(self):
        status = SensorStatus.from_bytes(bytes.fromhex("90ff02d5"))
        self.assertEqual(status.id, 0x90)
        self.assertEqual(status.temperature, 22.5)

    def test_deserialize_no_reading(self):
        status = SensorStatus.from_bytes(bytes.fromhex("91ff07ff"))
        self.assertEqual(status.id, 0x91)
        self.assertIsNone(status.temperature)

    def test_wrong_length_raises(self):
        with self.assertRaises(ValueError):
            SensorStatus.from_bytes(bytes(SENSOR_STATUS_LENGTH - 1))


class TestSensorStatusMessage(unittest.TestCase):
    def test_subheader_recognises_0x2b(self):
        subheader = ControlStatusSubHeader.from_bytes(CAPTURE_ARAMSHAW[:8])
        self.assertEqual(subheader.sub_type, ControlStatusSubType.SENSOR_STATUS)
        self.assertEqual(subheader.subdata_length.repeat_count, 6)
        self.assertEqual(subheader.subdata_length.repeat_length, SENSOR_STATUS_LENGTH)

    def test_deserialize_all_records(self):
        msg = _parse(CAPTURE_ARAMSHAW)
        self.assertEqual([s.id for s in msg.statuses], [0x80, 0x81, 0x82, 0x83, 0x90, 0x91])

    def test_only_present_sensor_has_temperature(self):
        temps = {s.id: s.temperature for s in _parse(CAPTURE_ARAMSHAW).statuses}
        self.assertEqual(temps[0x90], 20.9)
        for absent in (0x80, 0x81, 0x82, 0x83, 0x91):
            self.assertIsNone(temps[absent])

    def test_second_capture_matches_reported_value(self):
        # Reported in issue #21 as 22.5 C while the AC showed 22 C.
        temps = {s.id: s.temperature for s in _parse(CAPTURE_KIERANLEE).statuses}
        self.assertEqual(temps[0x90], 22.5)
