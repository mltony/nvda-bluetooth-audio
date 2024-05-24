# Notice

Bluetooth Audio add-on is abandoned. Silence playing functionality has been merged to NVDA core as of version 2024.2 and is turned on by default, so no further action is required.

If you would like to hear white noise, you would need to set a hidden option:
1. Open `NVDA.ini`. If you have installed copy of NVDA, it is located at `%APPDATA%\NVDA\nvda.ini`.
2. Quit NVDA and open Narrator.
3. Find `[audio]` section.
4. Within that section, add the following line:
    ```
    whiteNoiseVolume = 50
    ```
5. Save and close the file. Restart NVDA.

# nvda-bluetooth-audio
Bluetooth Audio is  an NVDA add-on that improves sound quality when working with bluetooth or RF headphones or speakers.

Most bluetooth devices enter standby mode after a few seconds of inactivity. That means that when NVDA starts speaking again, the first split second of sound will be lost. Bluetooth Audio add-on prevents bluetooth devices from entering standby mode by constantly playing a silent sound, that is inaudible to a human ear.

Bluetooth Audio can optionally play white noise sound instead of silence. This can be good for testing or to ascertain that Bluetooth Audio works as expected. However, same level of audio quality improvement can be achieved by playing silence.

Warning: using Bluetooth Audio add-on might reduce battery life of your bluetooth device.
## Download
* Current stable version (Python 3 only, requires NVDA 2019.3 or later): [BluetoothAudio](https://github.com/mltony/nvda-bluetooth-audio/releases/latest/download/bluetoothaudio.nvda-addon)
* Last Python 2 version (compatible with NVDA 2019.2 and prior): [v1.0](https://github.com/mltony/nvda-bluetooth-audio/releases/download/v1.0/bluetoothaudio-1.0.nvda-addon)

## Keystrokes
Bluetooth Audio add-on doesn't have any keystrokes. It works as long as it is installed.
## Source code
Source code is available at <http://github.com/mltony/nvda-bluetooth-audio>.

