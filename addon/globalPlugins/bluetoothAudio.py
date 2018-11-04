# -*- coding: UTF-8 -*-
#A part of the BluetoothAudio addon for NVDA
#Copyright (C) 2018 Tony Malykh
#This file is covered by the GNU General Public License.
#See the file COPYING.txt for more details.

import atexit
import config
from ctypes import create_string_buffer, byref
import globalPluginHandler
from logHandler import log
from NVDAHelper import generateBeep
import nvwave
from threading import Lock, Thread
import time
import tones

SAMPLE_RATE = 44100
playerLock = Lock()
shutdownInProgress = False
player = None

class BeepThread(Thread):
    def run(self):
        global player, shutdownInProgress
        buf = self.generateBeepBuf()
        while True:
            try:
                with playerLock:
                    if shutdownInProgress:
                        return
                    player = None
                    player = nvwave.WavePlayer(channels=2, samplesPerSec=int(SAMPLE_RATE), bitsPerSample=16, outputDevice=config.conf["speech"]["outputDevice"],wantDucking=False)
            except:
                log.warning("Failed to initialize player for BluetoothAudio")
                time.sleep(60)
                continue
            for second in range(60):
                if shutdownInProgress:
                    return
                playerLocal = player
                if not playerLocal:
                    break
                playerLocal.stop()
                playerLocal.feed(buf.raw)
                time.sleep(1)
    def generateBeepBuf(self):
        hz = 10
        length = 1
        left = right = 1
        bufSize=generateBeep(None,hz,length,left,right)
        buf=create_string_buffer(bufSize)
        generateBeep(buf,hz,length,left,right)
        return buf

        
beepThread = BeepThread()
beepThread.setName("Bluetooth Audio background beeper thread")
beepThread.daemon = True
beepThread.start()

@atexit.register
def _cleanup():
    global player, shutdownInProgress
    with playerLock:
        shutdownInProgress = True
        player = None

class GlobalPlugin(globalPluginHandler.GlobalPlugin):
    scriptCategory = _("BluetoothAudio")
    