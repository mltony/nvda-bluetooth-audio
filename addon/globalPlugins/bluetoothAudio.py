# -*- coding: UTF-8 -*-
#A part of the BluetoothAudio addon for NVDA
#Copyright (C) 2018 Tony Malykh
#This file is covered by the GNU General Public License.
#See the file COPYING.txt for more details.

import addonHandler
import atexit
import config
from ctypes import create_string_buffer, byref
import globalPluginHandler
import gui
from logHandler import log
from NVDAHelper import generateBeep
import nvwave
import speech
from threading import Lock, Thread
import time
import tones
import ui
import wx
from gui.settingsDialogs import SettingsPanel

SAMPLE_RATE = 44100
try:
    player = nvwave.WavePlayer(channels=2, samplesPerSec=int(SAMPLE_RATE), bitsPerSample=16, outputDevice=config.conf["speech"]["outputDevice"],wantDucking=False)
except:
    log.warning("Failed to initialize player for BluetoothAudio")
    
counter = 0
counterThreshold = 5
lock = Lock()

def resetCounter():
    global counter, lock
    with lock:
        counter = 0

class BeepThread(Thread):

    def run(self):
        global player, counter, lock
        buf = self.generateBeepBuf()
        while True:
            playerLocal = player
            if not playerLocal:
                break
            with lock:
                counter += 1
                counterLocal = counter
            if counterLocal <= counterThreshold:
                playerLocal.feed(buf.raw)
                time.sleep(60)

    def generateBeepBuf(self):
        hz = 400
        length = 60000
        left = right = 0
        bufSize=generateBeep(None,hz,length,left,right)
        buf=create_string_buffer(bufSize)
        generateBeep(buf,hz,length,left,right)
        return buf

beepThread = BeepThread()
beepThread.setName("Bluetooth Audio background beeper thread")
beepThread.daemon = True
beepThread.start()

@atexit.register
def cleanup():
    global player
    player = None
    
def interceptSpeech():
    def makeInterceptFunc(targetFunc):
        def wrapperFunc(*args, **kwargs):
            resetCounter()
            targetFunc(*args, **kwargs)
        return wrapperFunc
    speech.speak = makeInterceptFunc(speech.speak)

def initConfiguration():
    confspec = {
        "keepAlive" : "integer( default=60, min=0)",
    }
    config.conf.spec["bluetoothaudio"] = confspec
    
def getConfig(key):
    value = config.conf["bluetoothaudio"][key]
    return value

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
