# nvda-bluetooth-audio
Bluetooth Audio это дополнение NVDA, улучшающее качество звука при работе с ВЧ или Bluetooth-наушниками или колонками.

Большинство устройств Bluetooth уходит в режим ожидания через несколько секунд неактивности. Это означает, что когда NVDA начинает снова говорить, первая часть секунды звука будет потеряна. Дополнение Bluetooth Audio предотвращает от входа в режим ожидания Bluetooth -устройств, постоянно играя беззвучный звук, неслышимый для человеческого уха.

Bluetooth Audio can optionally play white noise sound instead of silence. This can be good for testing or to ascertain that Bluetooth Audio works as expected. However, same level of audio quality improvement can be achieved by playing silence.

Bluetooth Audio может опционально воспроизводить звук белого шума вместо тишины. Это может быть полезно для проверки или, чтобы выяснить, что Bluetooth Audio работает, как и ожидалось. Тем не менее, тот же уровень улучшения качества звука может быть достигнут, играя тишину.

Предупреждение: дополнение Bluetooth Audio может уменьшить срок службы батареи вашего устройства Bluetooth.
## Загрузить
* Текущую стабильную версию (Только Python 3, требуется NVDA 2019.3 или более поздней версии): [BluetoothAudio](https://github.com/mltony/nvda-bluetooth-audio/releases/latest/download/bluetoothaudio.nvda-addon)
* Последнюю версию Python 2 (совместимую с NVDA 2019.2 и более ранние): [v1.0](https://github.com/mltony/nvda-bluetooth-audio/releases/download/v1.0/bluetoothaudio-1.0.nvda-addon)

## Горячие клавиши
Дополнение Bluetooth Audio не имеет никаких горячих клавиш. Оно работает до тех пор, пока установлено.
## Исходники
Исходный код доступен на <http://github.com/mltony/nvda-bluetooth-audio>.