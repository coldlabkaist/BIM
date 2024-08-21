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
from PyQt5.QtWidgets import QApplication

# ## ===== ===== ===== ===== ===== ===== ===== =====
# ## Parse arguments
# ## ===== ===== ===== ===== ===== ===== ===== =====

parser = argparse.ArgumentParser(description = "Sleap feature extractor");

## Video and Excel data
parser.add_argument('--project_path',       type=str,   default="projects/project 0",   help='directory of video');
parser.add_argument('--video_path',       type=str,   default="projects/project 0/video",   help='directory of video');
parser.add_argument('--infer_path',       type=str,   default="projects/project 0/inference",   help='directory of sleap/dlc inference data');
parser.add_argument('--tracking_method',    type=str,   default="sleap",                help='tracking method of csv file');

## Graph controller
parser.add_argument('--show_norm',      type=int,   default=0,              help='Number of times to output a norm graph');
parser.add_argument('--show_smooth',    type=int,   default=0,              help='Number of times to output a smoothed graph');

## Inference smoothing
parser.add_argument('--window_length',  type=int,   default=19,             help='window length for smoothing');
parser.add_argument('--polyorder',      type=int,   default=3,              help='polynomial order for smoothing');
parser.add_argument('--smoothing_type', type=str,   default="savitzkygolay",         help='smoothing algorithm');
# none, savitzkygolay
parser.add_argument('--show_raw_data',  type=bool,  default=True,          help='show unsmoothed data if True');

## Detecting proofreading
parser.add_argument('--z_criteria',     type=int,   default=-2.3,           help='Z value below the criteria is recognized as a frame that requires proofreading');
parser.add_argument('--show_proofread_alert',     type=bool,   default=True,           help='Z value below the criteria is recognized as a frame that requires proofreading');

# trajetory controller # beta
# add code

args = parser.parse_args();

# ## ===== ===== ===== ===== ===== ===== ===== =====
# ## main
# ## ===== ===== ===== ===== ===== ===== ===== =====
#logger = getLogger(__name__)

def main():
    #test
    #print(args.int_test)

    list_file = {}
    list_file["inf"] = os.listdir(args.infer_path)
    list_file["vid"] = os.listdir(args.video_path)

    # call GUI
    print("calling BIM GUI...")
    callUI(args, list_file)

def callUI(args, list_file):
    #QApplication : a class that runs a program
    os.environ['QT_MULTIMEDIA_PREFERRED_PLUGINS'] = 'windowsmediafoundation'

    app = QApplication(sys.argv)  # type: ignore

    #Creating an Instance of WindowClass
    myWindow = UI.MainWindowClass(args, list_file) 

    #show GUI
    #myWindow.show()
    myWindow.showMaximized()
    
    #Enter the program into the event loop (operate the program)
    sys.exit(app.exec_())

if __name__ == '__main__':
    main()
