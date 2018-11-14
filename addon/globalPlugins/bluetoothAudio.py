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
def createMenu():
    def _popupMenu(evt):
        gui.mainFrame._popupSettingsDialog(SettingsDialog)
    prefsMenuItem  = gui.mainFrame.sysTrayIcon.preferencesMenu.Append(wx.ID_ANY, _("BluetoothAudio..."))
    gui.mainFrame.sysTrayIcon.Bind(wx.EVT_MENU, _popupMenu, prefsMenuItem)

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
createMenu()
interceptSpeech()
counterThreshold = getConfig("keepAlive")

class SettingsDialog(gui.SettingsDialog):
    # Translators: Title for the settings dialog
    title = _("BluetoothAudio settings")

    def __init__(self, *args, **kwargs):
        super(SettingsDialog, self).__init__(*args, **kwargs)

    def makeSettings(self, settingsSizer):
        sHelper = gui.guiHelper.BoxSizerHelper(self, sizer=settingsSizer)
        # Translators: Label for Stand by time edit box
        self.keepAliveEdit = gui.guiHelper.LabeledControlHelper(self, _("Stand by time in seconds"), wx.TextCtrl).control
        self.keepAliveEdit.Value = str(getConfig("keepAlive"))

    def onOk(self, evt):
        global counterThreshold
        try:
            keepAlive = int(self.keepAliveEdit.Value)
            config.conf["bluetoothaudio"]["keepAlive"] = keepAlive
            counterThreshold = keepAlive
            super(SettingsDialog, self).onOk(evt)
        except ValueError:
            ui.message("Invalid number format")
            self.keepAliveEdit.SetFocus()

class GlobalPlugin(globalPluginHandler.GlobalPlugin):
    scriptCategory = _("BluetoothAudio")
    
    def terminate(self):
        cleanup()
    