Here is the breakdown of the protocol structure, the operational logic, and the list of commands you can use.
These have all been obtained by packet sniffing the communication between the device and an iOS device using the app. If you know of any other commands that aren't on here, please feel free to add them in!
# Protocol Overview
* Format: Plain text JSON.
* Transport: UDP on Port 45
* Logic:
	* Querying: To read a value, you send the JSON structure with the target key set to null. The device responds with the same structure but with the current value filled in.
	* Setting: To set a value, send the JSON structure with the target key set to your desired value (integer, boolean, or string).
	* Transaction ID (xid): Most commands are wrapped in an "osc" object containing an "xid". This is an integer you should increment with every request to match responses to requests.
	* Some of the commands below are broken up with line breaks to make it easier to read, but ideally they should be sent with no line breaks in one chunk.

# Command Structure
## The Wrapper

All commands are typically wrapped in this root structure:
```JSON
{
  "osc": {
    "xid": 123  // Increment this number for each new command
  },
  // ... Command Payload goes here ...
}
```

## Device Identification & Network

Use these to identify the hardware and its network status.

### Get Identity (Product & Version):
```JSON
{"device":{"identity":{"product":null,"version":null}}}
```

Response Example: `{"product":"EWD1","version":"2.5.0"}`
### Get Network Config (IP & MAC):
```JSON
{"device":{"network":{"ipv4":{"ipaddr":null},"ether":{"macs":null}}}}
```
### Get/Set LCD Brightness:
```JSON
{"brightness":null}
// To set: {"brightness": 75} - Goes from 0-100
```
### Auto Key Lock
This locks the screen after ~10 seconds. To unlock it you have to hold the button down on the unit (or just turn off auto key lock)
```json
{"rx1":{"autolock":null}}    // Values True/False
```
### Identify
This will flash the LED on the front of the receiver as well as on the transmitter (if connected). Lasts for 10 seconds and then sets itself back to false.
```json
{"rx1":{"identify":null}}   // Values True/False
```
### Walktest
This will show a signal level in bigger writing on the LCD of the Receiver and transmitter of the signal level - Used to help you walk around and look for signal issues.
```json
{"rx1":{"walktest":null}}   // Values True/False
```
### Mute Switch
Enables/Disables the Mute Switch on the TX (stops the users from muting themselves!)
```json
{"rx1":{"mute_switch_active":null}}  // Values True/False  
```
### Pairing Mode
This is the same as holding down the Pair button on the Receiver. (Note: To pair, put the receiver in pairing mode, then hold the pair button down on the Transmitter)
```json
{"rx1":{"pair":null}}   // Values: True to enable pairing mode.
```
### Factory Reset
```json
"device":{"factory_reset":true}   // Will factory reset the device!
```
## Audio Configuration

These commands control the DSP on the receiver.
### Get/Set Automatic Gain Control (AGC):
```JSON
{"audio":{"agc":{"preset":null}}}
```
Values: 0 (Off), 1 (Hard), 2 (Soft)

### Get/Set De-Esser:
```JSON
{"audio":{"de_esser":{"preset":null}}}
```
Values: 0 (Off), 1 (Broad), 2 (Selective)

### Get/Set Equalizer:
```JSON
{"audio":{"equalizer":{"preset":null}}}
```
Values

| ID  | Name           | ID  | Name              |
| :-- | :------------- | :-- | :---------------- |
| 0   | Off            | 7   | Low Mid Cut       |
| 1   | Custom         | 8   | High Boost        |
| 2   | Vocals         | 9   | High Cut          |
| 3   | Presence Boost | 10  | Megaphone         |
| 4   | Mid Cut 1      | 11  | Telephone         |
| 5   | Mid Cut 2      | 12  | Acoustic Guitar 1 |
| 6   | High Mid Cut   | 13  | Acoustic Guitar 2 |
### Custom EQ
Set the equalizer preset to 1 - then you can adjust the values here
```json
{"audio":{"equalizer":{"custom":[6,7,6,8,5,-8,-8]}}}
```
Each value is one of the eq bands - Accepts a value from -12 to 12 (in dB)

| ID  | Band  |
| --- | ----- |
| 1   | 50Hz  |
| 2   | 125Hz |
| 3   | 315Hz |
| 4   | 800Hz |
| 5   | 2kHz  |
| 6   | 5kHz  |
| 7   | 10kHz |

### Get/Set Low Cut Filter:
```JSON
{"audio":{"low_cut":null}}    // Use true/false
```
### Get/Set Output Gain:
```JSON
{"audio":{"out1":{"gain_db":null}}}    // Integer from 1-30
```

## Receiver & Transmitter Status
Use these to monitor the connected microphone (Transmitter/TX) and the Receiver (RX).
The "mates" part I believe is where it has to query the Transmitter itself (So, battery levels and the switch value)
### Get Receiver Mute Switch Status:
```JSON
{"rx1":{"mute_switch_active":null}}
```
Note: This is different from the below switch1 value - If you have the mute switch disabled, this will always return false.
### Get Transmitter Battery & Switch:
```JSON
{
  "mates": {
    "tx1": {
      "bat_gauge": null,    // Returns % from 0 to 100
      "bat_state": null,    // Returns the bat_gauge response - likely unneeded!
      "switch1": { "state": null } // Mute switch on mic - Returns true or false.
    }
  }
}
```
Note: The Switch1 state is different from the receiver mute switch status. If you have the mute switch disabled, it will still report true or false.
### Get Transmitter RF Quality
```json
{
	"rx1": {
		"rf_quality": null, // Returns 1-100 as a % for the rf quality
		"warnings": null    // Responds with ["No Link"] if it can't see the mic, or [""] for all OK
	}
}
```

### Get Current Audio Level
```json
{
	"audio": {
		"out1": {
		  "level_db": null   // Returns db level from -80 to 0
		}
	}
}
```
### Get Input Type:
```JSON
{"mates":{"tx1":{"acoustic":null}}}    // Returns "Mic"
```
Response Example: "Mic"

## Subscriptions (Real-time Updates)

Instead of polling constantly, the protocol supports subscriptions. You send a subscribe list, and the device will push updates to you (e.g., audio levels or battery changes).

To start a subscription: Send a JSON with the keys you want to watch set to null inside a subscribe array.
```JSON
{
  "osc": {
    "state": {
      "subscribe": [
        {
          "rx1": {
            "rf_quality": null,
            "warnings": null
          },
          "mates": {
            "tx1": {
              "warnings": null,
              "bat_gauge": null
            }
          },
          "audio": {
            "out1": {
              "level_db": null
            }
          }
        }
      ]
    }
  }
}
```
Once subscribed, the device will spontaneously send packets like {"audio":{"out1":{"level_db":-42}}} when the values change.  You will need to send a new subscribe message every 10 seconds.
In my testing, I was getting approximately 18-20 updates per second.

## Capability Discovery

The device supports a "capabilities" discovery mechanism. If you query limits, it returns the allowed options for specific fields.

```JSON
{"osc":{"xid":29,"limits":[{"audio":{"agc":{"preset":null}}}]}} 
```
Response: Returns the options [0,1,2] and descriptions ["Off","Hard","Soft"].
```json
{"osc":{"xid":29,"limits":[{"audio":{"agc":{"preset":[{"type":"Number","desc":"AGC presets","option":[0,1,2],"option_desc":["Off","Hard","Soft"]}]}}}]}}
```
