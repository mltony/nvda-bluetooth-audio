# nvda-蓝牙-音频
蓝牙音频是 NVDA 的插件，可在使用蓝牙耳机或蓝牙音箱时改进 NVDA 的语音效果。


大多数蓝牙设备在不工作几秒后会进入待机模式。这意味着当 NVDA 再次朗读时，语音的前几个字将会丢失。蓝牙音频插件通过不间断播放人耳听不见的无声音频防止蓝牙设备进入待机模式。

蓝牙音频插件可以选择播放白噪声而不是静音音频。这有助于测试或确定蓝牙音频插件是否按预期工作。但是，播放无声音频可以达到同样的改进效果。

注意：使用蓝牙音频插件可能会缩短蓝牙设备的电池续航时间。

## 下载
* 当前稳定版（仅限 Python 3，需要 NVDA 2019.3 或更高版本）：[BluetoothAudio](https://github.com/mltony/nvda-bluetooth-audio/releases/latest/download/bluetoothaudio.nvda-addon)
* 最后一个 Python 2 版本（兼容 NVDA 2019.2 及之前版本）：[v1.0](https://github.com/mltony/nvda-bluetooth-audio/releases/download/v1.0/bluetoothaudio-1.0.nvda-addon)

## 按键
蓝牙音频插件没有任何快捷键。只要安装它就可以使用。

## 源代码
源代码可在 <http://github.com/mltony/nvda-bluetooth-audio> 获取。
