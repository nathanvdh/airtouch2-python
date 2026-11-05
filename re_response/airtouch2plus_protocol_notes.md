# AirTouch2+ Extended Protocol Documentation

## Overview

This document describes additional protocol messages discovered in AirTouch2+ controllers that extend beyond the standard documented protocol. These messages were reverse-engineered from live controller communications and cross-referenced with available AirTouch2 protocol documentation.

## Background

The AirTouch2+ controller sends several undocumented message types that must be properly acknowledged to maintain stable communication. Without proper handling of these messages, the controller may refuse new connections from both Home Assistant integrations and mobile applications.

## Message Types Identified

### Control Status Messages (0xC0)

#### 0x10 - AC Status Extended

**Purpose**: Provides extended AC status information beyond the standard 0x23 AC Status message.

**Structure**:
```
Byte 0: 0x10 (Message subtype)
Byte 1: 0x00 (Reserved)
Bytes 2-7: Standard control status subheader
Byte 8: AC ID
Byte 9: Status byte (bit 7 = power on/off)
Byte 10: Mode and fan speed (lower 4 bits = mode, upper 4 bits = fan)
Byte 11: Additional flags
Byte 12: Temperature value (divide by 10 for actual temperature)
```

**Correlation**: Maps to offsets 0x162-0x163 in AirTouch2 documentation (AC1/AC2 status)

**Required Acknowledgment**:
```
2B 00 00 02 00 00 00 00 00 00
```

#### 0x2B - Extended Status

**Purpose**: System status including available favorites, timers, and system counters.

**Structure**:
```
Byte 0: 0x2B (Message subtype)
Byte 1: 0x00 (Reserved)
Bytes 2-7: Standard control status subheader
Byte 8: Number of entries
Byte 9: Number of sections
Bytes 10+: Repeating 4-byte sections:
  - Byte 0: ID (0x80-0x83 = favorites, 0x90-0x91 = system counters)
  - Byte 1: Value
  - Bytes 2-3: Flags/counter data
```

**Favorites Section (0x80-0x83)**:
- ID byte matches value byte when favorite is available
- Flags provide additional status information
- Favorite 0 = 0x80, Favorite 1 = 0x81, etc.

**System Counters (0x90-0x91)**:
- System status and operational counters
- Flags contain 16-bit counter values

**Correlation**: Relates to timer offsets 0x15A-0x161 in AirTouch2 documentation

**Required Acknowledgment**:
A simple 1-byte payload is required.
```
2B 00 00 01 00 00 00 00 00
```
**Note**: The acknowledgment for this message must be sent as a `CONTROL_STATUS` message (type `0xC0`).

#### 0x21 - Group Status

**Purpose**: Provides the current status of all zone groups, including power state and damper percentage. This message is sent frequently and immediately after a favorite scene is changed to reflect the new settings.

**Structure**:
```
Byte 0: 0x21 (Message subtype)
Byte 1: 0x00 (Reserved)
Bytes 2-7: Standard control status subheader (typically 00 00 00 08 00 08, indicating 0 bytes of normal data, and 8 repeats of 8-byte blocks)
Bytes 8+: Repeating 8-byte group status blocks
```

**Group Status Block Format (8 bytes per group)**:
```
Byte 0:    Power and ID. Bit 6 (0x40) is power state (1=ON). Lower 4 bits are the group ID.
Byte 1:    Target Damper Percentage (0-100).
Byte 2:    Unknown flags.
Byte 3:    Current Damper Percentage (0-100).
Bytes 4-7: Additional flags (spill, turbo, etc).
```

**Example Parsing from Live Log**:
```
Data: 21:00:00:00:00:08:00:08:40:64:96:64:02:f8:00:00:41:50:96:50:02:f8:00:00...
      │ │                    │ │
      │ │                    └─ 8 repeats of 8-byte blocks
      │ └─ Subtype (0x21)
      │
      └─ Group 0 Block (40:64:96:64...):
         - Power/ID: 0x40 -> Power ON, ID 0
         - Target Damper: 0x64 -> 100%
         - Current Damper: 0x64 -> 100%
      └─ Group 1 Block (41:50:96:50...):
         - Power/ID: 0x41 -> Power ON, ID 1
         - Target Damper: 0x50 -> 80%
         - Current Damper: 0x50 -> 80%
```

**Required Acknowledgment**:
This is a status message and does not require an acknowledgment.


#### 0x31 - Favorite Status

**Purpose**: Provides the names of all configured favorite scenes and indicates which one is currently active. This message is sent when the active favorite changes.

**Structure**:
```
Byte 0: 0x31 (Message subtype)
Byte 1: 0x00 (Reserved)
Bytes 2-7: Standard control status subheader (typically 00 02 00 0B 00 04, indicating 2 bytes of normal data, and 4 repeats of 11-byte blocks)
Bytes 8-9: Normal Data - Active favorite selector
Bytes 10+: Repeating 11-byte favorite entry blocks
```

**Active Selector (Normal Data)**:
The first byte of the normal data is a bitmap indicating which favorite is active. The second byte is currently unknown (observed as `0x08`).
- `0x01`: Favorite 0 active 
- `0x02`: Favorite 1 active 
- `0x04`: Favorite 2 active 
- `0x08`: Favorite 3 active 

**Favorite Entry Format (11 bytes per favorite)**:
```
Byte 0:    Favorite ID (0-indexed)
Bytes 1-8: Name (8-byte ASCII string, null-padded)
Bytes 9-10: Unknown/Status bytes
```

**Example Parsing from Live Log**:
Message received when "gym" (Favorite ID 1) was activated.
```
Data: 31:00:00:02:00:0b:00:04:02:08:00:6d:61:69:6e:00:00:00:00:1b:00:01:67:79:6d:00:00:00:00:00:9b:00...
      │ │                    │ │   │ │
      │ │                    │ │   │ └─ Repeat Count (4 favorites)
      │ │                    │ │   └─ Repeat Length (11 bytes)
      │ │                    │ └─ Normal Data Length (2 bytes)
      │ │                    └─ Active Selector (0x02 -> Favorite 1 is active)
      │ └─ Subtype (0x31)
      │
      └─ Favorite 1 Block:
         - ID: 0x01
         - Name: 0x67796d... (in this case "gym")
         - Unknown: 0x9b00
```

**Required Acknowledgment**:
This is a status message and does not require an acknowledgment.

#### 0x40 - Zone Status

**Purpose**: Provides zone control percentages and status.

**Structure**:
```
Byte 0: 0x40 (Message subtype)
Byte 1: 0x00 (Reserved)
Bytes 2-7: Standard control status subheader
Bytes 8+: Repeating 8-byte zone blocks:
  - Byte 0: Zone ID
  - Byte 1: Percentage value
  - Bytes 2-7: Additional zone flags/status
```

**Correlation**: Maps to zone percentage offsets 0x114-0x123 in AirTouch2 documentation

**Required Acknowledgment**:
```
40 00 00 01 00 00 00 00 00
```
#### 0x45 - System Identity Broadcast

**Purpose**: Broadcasts system identity information. The payload contains the string "Polyaire Atch2PM", likely identifying the manufacturer and "AirTouch 2 Plus Module". This message appears to be sent periodically (e.g., every 13 hours).

**Required Acknowledgment - still testing**:
A simple 1-byte payload is required.
```
45 00 00 01 00 00 00 00 00
```
**Note**: The acknowledgment for this message must be sent as a `CONTROL_STATUS` message (type `0xC0`).

### Unknown Message Types

#### 0x27 - Unknown Message Type

**Purpose**: Unknown function, appears to be short status messages.

**Observed Data**: Simple payloads (typically single bytes like 0x00, 0x01)

**Required Handling**: Log and ignore - no acknowledgment appears necessary.

## Protocol Requirements

### Acknowledgment Format

All control status acknowledgments follow this structure:

```
Header (8 bytes):
  Byte 0: Message subtype (matches incoming message)
  Byte 1: 0x00 (Reserved)
  Bytes 2-3: Normal data length (big-endian)
  Bytes 4-5: Repeat data length (big-endian, typically 0x00 0x00)
  Bytes 6-7: Repeat count (big-endian, typically 0x00 0x00)
  
Data (variable length):
  Minimal response data as specified per message type
```

### Message Header Requirements

- **Address Source**: Your client should always identify itself with address `0x80`.
- **Message Type**: Use `MessageType.CONTROL_STATUS` (`0xC0`) for sending control commands and for acknowledging messages like `0x2B` and `0x45`. Use other types like `MessageType.EXTENDED` (`0xCB`) for other specific requests.
- **CRC16**: Proper MODBUS CRC16 checksum required

### Critical Implementation Notes

1. **Connection Stability**: The controller will refuse new connections if these messages are not properly acknowledged.

2. **Timing**: Acknowledgments should be sent immediately upon receiving these message types.

3. **Error Handling**: Unknown message types should be logged but not cause processing failures.

4. **Enum Handling**: Add these message types to your protocol enums to prevent ValueError exceptions:

```python
class ControlStatusSubType(IntEnum):
    # ... existing values ...
    AC_STATUS_EXTENDED = 0x10
    EXTENDED_STATUS = 0x2B  
    FAVORITE_STATUS = 0x31
    ZONE_STATUS = 0x40

class MessageType(IntEnum):
    # ... existing values ...
    UNKNOWN_27 = 0x27
```

## Implementation Example

```python
async def _send_ack_response(self, msg_type: int):
    """Send protocol-compliant acknowledgment."""
    ack_data: bytes
    if msg_type == 0x2B:  # Extended Status
        ack_data = bytes([0x2B, 0x00, 0x00, 0x01, 0x00, 0x00, 0x00, 0x00, 0x00])
    elif msg_type == 0x45:  # System Identity
        ack_data = bytes([0x45, 0x00, 0x00, 0x01, 0x00, 0x00, 0x00, 0x00, 0x00])
    else:
        # Generic ACK for other subtypes if needed
        ack_data = bytes([msg_type, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00])

    # Create header with correct address
    if msg_type == 0x2B or msg_type == 0x45:
        header = Header(0xC0, MessageType.CONTROL_STATUS, len(ack_data))
    else:
        header = Header(0x80, MessageType.CONTROL_STATUS, len(ack_data))
    
    # Create and send message with proper headers and checksum
    # ... implementation details ...```

## Future Enhancement Opportunities

### Favorite Scene Control
The 0x31 message provides complete favorite scene information that could be used to:
- Display available scenes in Home Assistant
- Show which scene is currently active
- Potentially trigger scene changes (requires further reverse engineering)

### Enhanced Zone Management  
The 0x40 message provides detailed zone status that could enable:
- Individual zone percentage display
- Zone-specific status indicators
- Advanced zone control features

### System Monitoring
The 0x2B message contains system counters and status that could provide:
- System health monitoring
- Usage statistics
- Advanced diagnostics

## References

- AirTouch2 Protocol Documentation (offsets 0x158-0x18A)
- Live protocol captures from AirTouch2+ controller communications
- Reverse engineering analysis of controller behavior

## Changelog

- **Initial Version**: Documented 0x2B, 0x10, 0x31, 0x40, and 0x27 message types
- **Protocol Requirements**: Added acknowledgment format specifications
- **Implementation Guide**: Added code examples and enum definitions