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

debug = True
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



SAMPLE_RATE = 44100
try:
    player = nvwave.WavePlayer(channels=2, samplesPerSec=int(SAMPLE_RATE), bitsPerSample=16, outputDevice=config.conf["speech"]["outputDevice"],wantDucking=False)
except:
    log.warning("Failed to initialize player for BluetoothAudio")

counter = 0
counterThreshold = 5
lock = Lock()

def resetCounter(reopen=False):
    global beepThread
    t = time.time()
    t += getConfig("keepAlive")
    beepThread.play(t, reopen)

def generateBeepBuf(whiteNoiseVolume):
    hz = 400
    length = 60000
    left = right = 0
    bufSize=generateBeep(None,hz,length,left,right)
    buf=create_string_buffer(bufSize)
    generateBeep(buf,hz,length,left,right)
    bytes = bytearray(buf)
    n = bufSize//2
    unpacked = struct.unpack(f"<{n}h", bytes)
    unpacked = list(unpacked)
    for i in range(n):
        #unpacked[i] = random.randint(-whiteNoiseVolume, whiteNoiseVolume)
        unpacked[i] = int(whiteNoiseVolume * random.gauss(0, 1))

    api.q = unpacked
    packed = struct.pack(f"<{n}h", *unpacked)
    return packed

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
        unpacked[i] = int(unpacked[i] * whiteNoiseVolume/100)

    api.q = unpacked
    packed = struct.pack(f"<{n}h", *unpacked)
    return packed, f.getframerate()




ttBase = time.time()
def tt(t=None):
    if t is not None:
        t = time.time()
    t -= ttBase
    return "%.3f" % t
    


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
        mylog(".doInit")
        if self.player is not None:
            try:
                self.player.stop()
            except:
                pass
        self.buf, framerate = generateBeepBuf(1)
        self.player = nvwave.WavePlayer(channels=2, samplesPerSec=framerate, bitsPerSample=16, outputDevice=config.conf["speech"]["outputDevice"],wantDucking=False)

    def run(self):
        mylog(".run start")
        while True:
            with self.lock:
                self.preCounter += 1
                mylog(f"self.preCounter={self.preCounter}")
                mylog(f"now={tt(time.time())} pauseTime={tt(self.pauseTime)}")
                if self.shutdownRequested:
                    mylog("shutdown requested, quitting!")
                    return
                if self.initRequested:
                    mylog("init requested!")
                    self.doInit()
                    self.initRequested = False
                if time.time() >= self.pauseTime:
                    mylog("Pause Time reached, pausing; self.playing: {self.playing}>False")
                    self.playing = False
                    self.sleepCondition.wait()
                else:
                    mylog("self.playing: {self.playing} > True")
                    self.playing = True
                self.postCounter += 1
                mylog(f"self.postCounter={self.postCounter}")
            if self.playing:
                mylog("Feeding")
                self.player.feed(self.buf)
            mylog("while True")
            
    def lockAndInterrupt(self):
        mylog(".lockAndInterrupt")
        with self.lock:
            self.interrupt()

    def interrupt(self):
        timeLeft = self.pauseTime - time.time()
        mylog(f".interrupt self.playing={self.playing} timeLeft={timeLeft}")
        mylog(f"now={tt(time.time())} pauseTime={tt(self.pauseTime)}")
        # This function is not 100% reliable.
        # For example, it might call player.stop() before the thread actually calls player.feed().
        # In this case interrupt won't work. This can  be fixed but this would make code much more complicated.
        # We rather decided to keep code simple. In the worst case white noise will be playing for extra 10 seconds.
        if self.playing:
            self.player.stop()
            if self.preCounter == self.postCounter:
                mylog(f"asdf pre == post {self.preCounter} == {self.postCounter}")
                def postCheck():
                    mylog(f"postCheck: {self.preCounter} {self.postCounter}")
                core.callLater(1000, postCheck)
            else:
                mylog(f"asdf pre != post {self.preCounter} != {self.postCounter}")
        else:
            self.sleepCondition.notifyAll()

    def play(self, untilWhen, reopen=False):
        mylog(".play")
        with self.lock:
            self.pauseTime = untilWhen
            self.initRequested = reopen
            self.timer.Stop()
            timerDuration = int(1 + 1000 * (untilWhen - time.time()))
            if timerDuration > 0:
                mylog(f"setting timer for {timerDuration} seconds")
                self.timer.Start(timerDuration, wx.TIMER_ONE_SHOT)
            if timerDuration <= 0 or not self.playing or reopen:
                mylog("timerDuration <= 0")
                self.interrupt()

    def terminate(self):
        with self.lock:
            self.shutdownRequested = True
            self.interrupt()


    def runOld(self):
        global player, counter, lock
        buf = generateBeepBuf(1)
        while True:
            playerLocal = player
            if not playerLocal:
                break
            with lock:
                counter += 1
                counterLocal = counter
            if counterLocal <= counterThreshold:
                playerLocal.feed(buf)
            else:
                time.sleep(1)


beepThread = BeepThread()
beepThread.start()

@atexit.register
def cleanup():
    beepThread.terminate()

#tones.initialize
def interceptSpeech():
    def makeInterceptFunc(targetFunc, hookFunc):
        def wrapperFunc(*args, **kwargs):
            hookFunc()
            return targetFunc(*args, **kwargs)
        return wrapperFunc
    speech.speak = makeInterceptFunc(speech.speak, resetCounter)
    speech.speech.speak = makeInterceptFunc(speech.speech.speak, resetCounter)
    tones.initialize = makeInterceptFunc(tones.initialize, lambda: resetCounter(reopen=True))

def initConfiguration():
    confspec = {
        "keepAlive" : "integer( default=60, min=0)",
    }
    config.conf.spec["bluetoothaudio"] = confspec

def getConfig(key):
    value = config.conf["bluetoothaudio"][key]
    return value

def handleConfigProfileSwitch():
    tones.beep(500, 500)

config.post_configProfileSwitch.register(handleConfigProfileSwitch)

addonHandler.initTranslation()
initConfiguration()
interceptSpeech()
counterThreshold = getConfig("keepAlive")

class SettingsDialog(SettingsPanel):

    # Translators: Title for the settings dialog
    title = _("BluetoothAudio")

    def makeSettings(self, settingsSizer):
        sHelper = gui.guiHelper.BoxSizerHelper(self, sizer=settingsSizer)
        # Translators: Label for Stand by time edit box
        self.keepAliveEdit = sHelper.addLabeledControl(_("Stand by time in seconds"), wx.TextCtrl)
        self.keepAliveEdit.Value = str(getConfig("keepAlive"))

    def isValid(self):
        try:
            int(self.keepAliveEdit.Value)
            return True
        except:
            ui.message("Invalid number format")
            self.keepAliveEdit.SetFocus()
            return False

    def onSave(self):
        global counterThreshold
        keepAlive = int(self.keepAliveEdit.Value)
        config.conf["bluetoothaudio"]["keepAlive"] = keepAlive
        counterThreshold = keepAlive

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

    @script(description=_("Debug log"), gestures=['kb:NVDA+Control+F12'])
    def script_debugLog(self, gesture):
        tones.beep(500, 50)
        mylog("qqq")
