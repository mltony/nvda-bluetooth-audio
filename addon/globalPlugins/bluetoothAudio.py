# -*- coding: UTF-8 -*-
#A part of the BluetoothAudio addon for NVDA
#Copyright (C) 2018 Tony Malykh
#This file is covered by the GNU General Public License.
#See the file COPYING.txt for more details.

import addonHandler
import api
import atexit
import config
import core
from ctypes import create_string_buffer, byref
import globalPluginHandler
import gui
from gui import nvdaControls
from logHandler import log
from NVDAHelper import generateBeep
import nvwave
import os
import random
from scriptHandler import script
import speech
import struct
import sys
from threading import Condition, Lock, Thread
import time
import tones
import ui
import wave
import wx
from gui.settingsDialogs import SettingsPanel

debug = False
if debug:
    f = open("C:\\Users\\tony\\drp\\1.txt", "w", encoding='utf-8')
    debugLock = Lock()
    def mylog(s):
        with debugLock:
            print(str(s), file=f)
            f.flush()
else:
    def mylog(s):
        pass


def initConfiguration():
    confspec = {
        "keepAlive" : "integer( default=60, min=0)",
        "whiteNoiseVolume" : "integer( default=0, min=0, max=100)",
    }
    config.conf.spec["bluetoothaudio"] = confspec

addonHandler.initTranslation()
initConfiguration()

def getConfig(key):
    value = config.conf["bluetoothaudio"][key]
    return value



def resetCounter(reopen=False):
    global beepThread
    t = time.time()
    t += getConfig("keepAlive")
    beepThread.play(t, reopen)

def getSoundsPath():
    globalPluginPath = os.path.abspath(os.path.dirname(os.path.dirname(__file__)))
    #addonPath = os.path.split(globalPluginPath)[0]
    addonPath = globalPluginPath
    soundsPath = os.path.join(addonPath, "sounds")
    return soundsPath

def generateBeepBuf(whiteNoiseVolume):
    # sox -n -b 16 --rate 44100 output.wav synth 10 pinknoise
    fileName = os.path.join(
        getSoundsPath(),
        "white_noise_10s.wav"
    )

    f = wave.open(fileName,"r")
    if f is None: raise RuntimeError()
    buf =  f.readframes(f.getnframes())
    bufSize = len(buf)
    n = bufSize//2
    unpacked = struct.unpack(f"<{n}h", buf)
    unpacked = list(unpacked)
    for i in range(n):
        unpacked[i] = int(unpacked[i] * whiteNoiseVolume/1000)

    packed = struct.pack(f"<{n}h", *unpacked)
    return packed, f.getframerate()




class BeepThread(Thread):
    def __init__(self):
        super().__init__(
            name="Bluetooth Audio background beeper thread",
            daemon=True,
        )
        self.lock = Lock()
        self.sleepCondition = Condition(self.lock)
        self.playing = False
        self.pauseTime = time.time() + 1e10
        self.initRequested = True
        self.shutdownRequested = False
        self.player = None
        self.timer = wx.PyTimer(self.lockAndInterrupt)
        self.preCounter = 0
        self.postCounter = 0


    def doInit(self):
        if self.player is not None:
            try:
                self.player.stop()
            except:
                pass
        self.buf, framerate = generateBeepBuf(getConfig('whiteNoiseVolume'))
        self.player = nvwave.WavePlayer(channels=2, samplesPerSec=framerate, bitsPerSample=16, outputDevice=config.conf["speech"]["outputDevice"],wantDucking=False)

    def run(self):
        while True:
            with self.lock:
                self.preCounter += 1
                if self.shutdownRequested:
                    return
                if self.initRequested:
                    self.doInit()
                    self.initRequested = False
                if time.time() >= self.pauseTime:
                    self.playing = False
                    self.sleepCondition.wait()
                else:
                    self.playing = True
                self.postCounter += 1
            if self.playing:
                self.player.feed(self.buf)

    def lockAndInterrupt(self):
        with self.lock:
            self.interrupt()

    def interrupt(self):
        # This function is not 100% reliable.
        # For example, it might call player.stop() before the thread actually calls player.feed().
        # In this case interrupt won't work. This can  be fixed but this would make code much more complicated.
        # We rather decided to keep code simple. In the worst case white noise will be playing for extra 10 seconds.
        if self.playing:
            self.player.stop()
        else:
            self.sleepCondition.notifyAll()

    def play(self, untilWhen, reopen=False):
        with self.lock:
            self.pauseTime = untilWhen
            if reopen:
                self.initRequested = True
            self.timer.Stop()
            timerDuration = int(1 + 1000 * (untilWhen - time.time()))
            if timerDuration > 0:
                self.timer.Start(timerDuration, wx.TIMER_ONE_SHOT)
            if timerDuration <= 0 or not self.playing or reopen:
                mylog("timerDuration <= 0")
                self.interrupt()

    def terminate(self):
        with self.lock:
            self.shutdownRequested = True
            self.interrupt()

beepThread = BeepThread()
beepThread.start()

@atexit.register
def cleanup():
    beepThread.terminate()

def interceptSpeech():
    def makeInterceptFunc(targetFunc, hookFunc):
        def wrapperFunc(*args, **kwargs):
            hookFunc()
            return targetFunc(*args, **kwargs)
        return wrapperFunc
    speech.speak = makeInterceptFunc(speech.speak, resetCounter)
    speech.speech.speak = makeInterceptFunc(speech.speech.speak, resetCounter)
    tones.initialize = makeInterceptFunc(tones.initialize, lambda: resetCounter(reopen=True))

interceptSpeech()

class SettingsDialog(SettingsPanel):
    # Translators: Title for the settings dialog
    title = _("BluetoothAudio")

    def makeSettings(self, settingsSizer):
        sHelper = gui.guiHelper.BoxSizerHelper(self, sizer=settingsSizer)
      # Translators: Label for Stand by time edit box
        labelText = _("Stand by time in seconds")
        self.keepAliveEdit = sHelper.addLabeledControl(
            labelText, nvdaControls.SelectOnFocusSpinCtrl,
            min=1, max=100000,
            initial=getConfig("keepAlive"),
        )
      # White noise volume slider
        label = _("Volume of white noise")
        self.whiteNoiseVolumeSlider = sHelper.addLabeledControl(label, wx.Slider, minValue=0,maxValue=100)
        self.whiteNoiseVolumeSlider.SetValue(getConfig("whiteNoiseVolume"))

    def isValid(self):
        try:
            int(self.keepAliveEdit.Value)
            return True
        except:
            ui.message("Invalid number format")
            self.keepAliveEdit.SetFocus()
            return False

    def onSave(self):
        keepAlive = int(self.keepAliveEdit.Value)
        config.conf["bluetoothaudio"]["keepAlive"] = keepAlive
        config.conf["bluetoothaudio"]["whiteNoiseVolume"] = self.whiteNoiseVolumeSlider.Value
        resetCounter(reopen=True)

class GlobalPlugin(globalPluginHandler.GlobalPlugin):
    scriptCategory = _("BluetoothAudio")

    def __init__(self, *args, **kwargs):
        super(GlobalPlugin, self).__init__(*args, **kwargs)
        self.createMenu()

    def createMenu(self):
        gui.settingsDialogs.NVDASettingsDialog.categoryClasses.append(SettingsDialog)

    def terminate(self):
        gui.settingsDialogs.NVDASettingsDialog.categoryClasses.remove(SettingsDialog)
        cleanup()

