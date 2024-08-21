#-*- coding: utf-8 -*-

import argparse
import sys
#from logging import getLogger

import time
import os 
import datetime
import logging
import numpy as np

# python files
import UI
from PyQt5 import uic
from PyQt5.QtWidgets import QApplication, QDialog, QMainWindow, QFileDialog, QListView

# ## ===== ===== ===== ===== ===== ===== ===== =====
# ## Parse arguments
# ## ===== ===== ===== ===== ===== ===== ===== =====

class Args():
    def __init__(self):
        self.video_path = "projects/project 0/video" #default
        self.infer_path = "projects/project 0/inference" #default
        self.tracking_method = "sleap" #default

        self.show_norm = 0
        self.show_smooth = 0

        self.window_length = 19
        self.polyorder = 3
        self.smoothing_type = "savitzkygolay" #default

        self.show_raw_data = True

        self.z_criteria = -2.3
        self.show_proofread_alert = True

# ## ===== ===== ===== ===== ===== ===== ===== =====
# ## main
# ## ===== ===== ===== ===== ===== ===== ===== =====
#logger = getLogger(__name__)

form_class = uic.loadUiType("BIMmainGUI.ui")[0]

class MainWindowClass(QDialog, form_class):
    def __init__(self):
        super().__init__()
        self.setupUi(self)
        self.args = Args()

        # load files
        self.loadvideobt.clicked.connect(self.loadvideo)
        self.loadinferbt.clicked.connect(self.loadinfer)

        # match files
        self.listvideo.setMovement(QListView.Free)
        self.listvideo.setDragEnabled(True)
        self.listvideo.setAcceptDrops(True)
        self.listvideo.setDragDropMode(QListView.InternalMove)
        self.listinfer.setMovement(QListView.Free)
        self.listinfer.setDragEnabled(True)
        self.listinfer.setAcceptDrops(True)
        self.listinfer.setDragDropMode(QListView.InternalMove)
        # implement delete
        self.viddelbt.clicked.connect(self.deleteselvideo)
        self.infdelbt.clicked.connect(self.deleteselinfer)
        # add more files
        # Todo

        self.datasmoothingmethod.addItems(["none", "savitzkygolay"])
        self.trackingmethod.addItems(["sleap", "dlc"])

        self.runbt.clicked.connect(self.runUI)

    def loadvideo(self):
        self.listvideo.clear()
        self.videofolderdir=QFileDialog.getExistingDirectory(self)
        if self.videofolderdir == '':
            print("directory not selected")
            return
        self.videofiledir = os.listdir(self.videofolderdir)
        self.listvideo.addItems(self.videofiledir)

    def loadinfer(self):
        self.listinfer.clear()
        self.inferfolderdir=QFileDialog.getExistingDirectory(self)
        if self.inferfolderdir == '':
            print("directory not selected")
            return
        self.inferfiledir = os.listdir(self.inferfolderdir)
        self.listinfer.addItems(self.inferfiledir)
    
    def deleteselvideo(self):
        row = self.listvideo.currentRow()
        self.listvideo.takeItem(row)
        
    def deleteselinfer(self):
        row = self.listinfer.currentRow()
        self.listinfer.takeItem(row)

    def runUI(self):
        # call GUI
        print("calling BIM GUI...")

        lenvid = self.listvideo.count()
        leninf = self.listinfer.count()
        if lenvid != leninf:
            print("number of video and inference should be same!")
            return

        self.list_file = {}
        self.list_file["inf"] = []
        self.list_file["vid"] = []

        for index in range(lenvid):
            vidtext = self.listvideo.item(index).text()
            if not vidtext.split('.')[-1] in ['mp4', 'avi']: # modify list
                print("incorrect video!")
                return
            self.list_file["vid"].append(self.listvideo.item(index).text())
        for index in range(leninf):
            inftext = self.listinfer.item(index).text()
            if not inftext.split('.')[-1] in ['csv', 'txt']: # modify list
                print("incorrect inference file!")
                return
            self.list_file["inf"].append(self.listinfer.item(index).text())      

        self.args.smoothing_type = self.datasmoothingmethod.currentText()
        self.args.tracking_method = self.trackingmethod.currentText()
        self.args.video_path = self.videofolderdir
        self.args.infer_path = self.inferfolderdir
        self.callUI()

    def callUI(self):
        #Creating an Instance of WindowClass
        myWindow_ui = UI.MainWindowClass(self.args, self.list_file) 

        #show GUI
        self.close()
        myWindow_ui.showMaximized()
        myWindow_ui.exec_()

def main():
    os.environ['QT_MULTIMEDIA_PREFERRED_PLUGINS'] = 'windowsmediafoundation'
    
    app = QApplication(sys.argv)  # type: ignore
    #Creating an Instance of WindowClass
    myWindow = MainWindowClass() 
    #show GUI
    myWindow.show()
    #Enter the program into the event loop (operate the program)
    sys.exit(app.exec_())

if __name__ == '__main__':
    main()
