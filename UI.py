#-*- coding: utf-8 -*-

import sys
import os 
import random
import cv2  # type: ignore
from inferenceloader import slp, dlc
import smoothing
import matplotlib.pyplot as plt
import time

from PyQt5.QtWidgets import QApplication, QDialog, QGraphicsScene, QMainWindow, QGraphicsEllipseItem, QGraphicsTextItem
from PyQt5.QtGui import QBrush, QPen, QColor, QFont
from PyQt5.QtCore import *
from PyQt5.QtMultimedia import QMediaPlayer, QMediaContent
from PyQt5.QtMultimediaWidgets import QGraphicsVideoItem
from PyQt5 import uic

# connect slexGUI.ui file to UI.py
form_class = uic.loadUiType("BIMGUI.ui")[0]

# main page of slex
# consists of video/graphic section, instance/skeleton manager, and additional things
class MainWindowClass(QDialog, form_class):

    # create a signal to generate frame change detector
    frameChangedsig = pyqtSignal(int) # type: ignore 

    def __init__(self, args_main, list_file):
        super().__init__()
        self.setupUi(self)
        self.setWindowFlags(Qt.WindowCloseButtonHint | Qt.WindowMaximizeButtonHint | Qt.WindowMinimizeButtonHint) # type: ignore

        # ---------------------------------------------------------------------------------
        # Load file directory into project, read information from video
        # ---------------------------------------------------------------------------------
        # Read parser arguments
        self.args_main = args_main
        self.video_path = args_main.video_path
        self.infer_path = args_main.infer_path

        # Road lists of files
        self.list_inf = list_file["inf"]
        self.list_vid = list_file["vid"]

        # Read fps and size of video (from one sample video)
        sample_vid = cv2.VideoCapture(self.video_path+'/'+self.list_vid[0])
        self.fps = sample_vid.get(cv2.CAP_PROP_FPS)
        isloaded, frame = sample_vid.read()
        if not isloaded:
            print("incorrect video!")
            return
        self.vid_h, self.vid_w, _ = frame.shape
        self.current_frame = 0
        
        # Define resolution or margin of video (to display without distortion)
        # refer update_scene_size()
        self.vid_h_adjust, self.vid_w_adjust = self.vid_h, self.vid_w
        self.vid_resol_const = 1
        self.vid_resol_var = 100 # in %
        self.vid_bias_x = 0.0
        self.vid_bias_y = 0.0

        # ---------------------------------------------------------------------------------
        # Load graphics and Videos
        # ---------------------------------------------------------------------------------

        # load graphics map
        self.size = 8 # default value
        self.trans = 120 # default value
        self.def_colormap() 

        # Create a list of graphics
        self.inf_graphic = []

        # Create a QGraphicsScene
        self.scene = QGraphicsScene()
        # Set the scene to the QGraphicsView
        self.qgraphicsvideo.setScene(self.scene)

        # Create a QGraphicsVideoItem
        self.video_item = QGraphicsVideoItem()
        self.scene.addItem(self.video_item)

        # Set up the QMediaPlayer
        self.media_player = QMediaPlayer(None, QMediaPlayer.VideoSurface)
        self.media_player.setVideoOutput(self.video_item)

        # Connect error signals to handle potential issues
        self.media_player.error.connect(self.handle_error)
        self.media_player.mediaStatusChanged.connect(self.handle_media_status)
        self.media_player.stateChanged.connect(self.handle_state_changed)

        # Adjust the video to screen size
        self.update_scene_size()

        # Load inference data
        if args_main.tracking_method == "sleap":
            self.inf_file = slp.load_file(self.infer_path, self.list_inf)
        elif args_main.tracking_method == "dlc":
            self.inf_file = dlc.load_file(self.infer_path, self.list_inf, args_main)
        else:
            raise Exception("Check CSV File Method")
        smoothing.smoothing(self.inf_file, args_main)
        
        self.is_video_played = False

        self.text_items = []
        # load proofreading detector
        for i in range(1,5):
            text_item = QGraphicsTextItem("Need ProofReading")
            text_item.setFont(QFont("Arial", 24))
            text_item.setDefaultTextColor(self.invisible)
            text_item.setPos(100, 100*i)
            self.scene.addItem(text_item) 
            self.text_items.append(text_item)

        # ---------------------------------------------------------------------------------
        # Timers (to move graphics)
        # ---------------------------------------------------------------------------------
        self.frame_check_timer = QTimer(self) # type: ignore 
        self.frame_check_timer.timeout.connect(self.check_frame_change)
        self.frame_check_timer.setInterval(10)
        self.frame_check_timer.start()  # Check every frame
        self.frameChangedsig.connect(self.framechanged)

        # ---------------------------------------------------------------------------------
        # Qt widgets
        # ---------------------------------------------------------------------------------
        # qt: buttons
        self.prevNfbt.clicked.connect(self.prevNfbt_clicked)
        self.prevfbt.clicked.connect(self.prevfbt_clicked)
        self.playbt.clicked.connect(self.playbt_clicked)
        self.nextfbt.clicked.connect(self.nextfbt_clicked)
        self.nextNfbt.clicked.connect(self.nextNfbt_clicked)
        
        self.colorbt.clicked.connect(self.colorbt_clicked)

        # qt: spinbox
        self.Nf = self.framespin.value()
        self.framespin.valueChanged.connect(self.framespin_valueChanged)
        self.speedspin.valueChanged.connect(self.speedspin_changed)

        # qt: combos (selection)
        self.filecomb_set()
        self.filecomb.currentIndexChanged.connect(self.filecomb_changed)
        # self.instcomb_set() #conduct it at loadselectedvideo
        # self.nodecomb_set()
        self.colorcomb_set()
        
        # qt: textbrowser, label, videoslider
        # self.videoframelabel_set() # conduct it at loadselectedvideo
        # self.videoslider_setrange()
        self.videoslider.sliderPressed.connect(self.videoslider_pressed)
        self.videoslider.sliderReleased.connect(self.videoslider_released)
        self.videoslider.sliderMoved.connect(self.videoslider_moved)

        # qt: slider (transparency, size)
        self.translider.setRange(1, 225)
        self.translider.setValue(120) # default value
        self.translider.sliderMoved.connect(self.translider_moved)
        self.sizeslider.setRange(1, 20)
        self.sizeslider.setValue(8) # default value
        self.sizeslider.sliderMoved.connect(self.sizeslider_moved)

        # qt: checkbox
        if self.args_main.show_proofread_alert:
            self.alertcheck.toggle()
        self.alertcheck.stateChanged.connect(self.alertcheck_changed)
        if self.args_main.show_raw_data:
            self.rawdatacheck.toggle()
        self.rawdatacheck.stateChanged.connect(self.rawdatacheck_changed)

        # load video
        self.load_selected_video(self.list_vid[0], self.list_inf[0])

        self.media_player.play()
        self.media_player.pause()

    # -------------------------------------------------------------------
    # METHODS_video
    # -------------------------------------------------------------------
    def load_selected_video(self, video_path, infer_path = None):
        time.sleep(0.1)
        file_path = self.video_path+'/'+video_path
        self.media_player.setMedia(QMediaContent(QUrl.fromLocalFile(file_path))) # type: ignore 
        self.media_player.setMuted(True)
        self.media_player.setPlaybackRate(self.speedspin.value())
        self.get_framecount(video_path)
        self.current_frame = 0
        self.videoframelabel_set()
        self.videoslider_reset()
        self.videoslider_setrange()

        # load graphics
        if infer_path == None:
            self.file_ind = self.filecomb.currentIndex()
            self.file_data = self.inf_file.file_data[self.file_ind]
        else:
            self.file_data = self.inf_file.file_data[0]
        self.node_list = self.inf_file.node_list
        self.instance_list = self.file_data.instance

        self.instcomb_set()
        self.nodecomb_set()
        self.instance_colormap = [[0 for i in self.node_list] for j in self.instance_list]
        #print(self.instance_colormap)

        self.videoloaded = True
        self.update_scene_size()
        self.add_graphical_elements(0)

    def get_framecount(self, video_path):
        file_path = self.video_path+'/'+video_path
        cap = cv2.VideoCapture(file_path)
        self.totalframe = cap.get(cv2.CAP_PROP_FRAME_COUNT)
        self.fps = cap.get(cv2.CAP_PROP_FPS)
        #print(self.totalframe, self.fps)
    
    def video_playorpause(self):
        #print(self.media_player.mediaStatus(), self.media_player.state())
        if (self.media_player.mediaStatus()==1): # no video loaded
            return
        state = self.media_player.state()
        if(state == 0 or state == 2): # just loaded or paused
            print('Playing video...')
            self.media_player.play()
            self.is_video_played = True
        elif(state == 1): # playing
            print('video Paused')
            self.media_player.pause()
            self.is_video_played = False
    
    def move_frame(self, direction, pos, Nframe):
        if(direction == "forward"):
            sgn = +1
        elif(direction == "backward"):
            sgn = -1
        else:
            print("error: wrong direction on move_frame")
            return
        
        #self.media_player.pause()
        current_position = pos
        ms_step = self.frame2ms(Nframe)
        new_position = current_position + sgn*ms_step
        self.media_player.setPosition(new_position)
        self.media_player.setPlaybackRate(self.speedspin.value())
        #if self.is_video_played:
        #    self.media_player.play()

    def check_frame_change(self):
        position = self.media_player.position()
        new_frame = self.ms2frame(position)
        if new_frame != self.current_frame:
            self.current_frame = new_frame
            self.frameChangedsig.emit(self.current_frame)

    def framechanged(self):
        currentpos = self.media_player.position()
        currentfr = self.ms2frame(currentpos)
        self.videoframelabel.setText(f"Frame: {currentfr}/{int(self.totalframe)}")
        self.videoslider.setValue(currentfr)
        self.add_graphical_elements(currentfr)

        # to solve lagging
        if self.media_player.mediaStatus() == 4:
            print("StalledMedia")
        if self.media_player.mediaStatus() == 5:
            print("BufferingMedia")                   

    def update_scene_size(self):
        # get size information of qgraphicsvideo
        screen_rect = self.qgraphicsvideo.rect()
        screen_w = screen_rect.width()
        screen_h = screen_rect.height()
        #screen_x = screen_rect.x()
        #screen_y = screen_rect.y()
        
        # compare the size ratio of screen and video
        # if screen_w/video_w > screen_h/video_h, then height of video is longer
        if (screen_w*self.vid_h > screen_h*self.vid_w):
            # video height is longer, adjust width based on height
            self.resol_const = screen_h/self.vid_h
            self.vid_w_adjust = self.vid_w*self.resol_const
            self.vid_h_adjust = screen_h
            self.bias_x = (screen_w-self.vid_w_adjust)/2
            self.bias_y = 0
        elif (screen_w*self.vid_h <= screen_h*self.vid_w):
            # video width is longer, adjust height based on width
            self.resol_const = screen_w/self.vid_w
            self.vid_w_adjust = screen_w
            self.vid_h_adjust = self.vid_h*self.resol_const
            self.bias_x = 0
            self.bias_y = (screen_h-self.vid_h_adjust)/2

        self.video_item.setSize(QSizeF(self.vid_w_adjust, self.vid_h_adjust)) # type: ignore 
        self.scene.setSceneRect(QRectF(0,0, self.vid_w_adjust, self.vid_h_adjust)) # type: ignore 

    def resizeEvent(self, e):
        if self.videoloaded:
            self.update_scene_size()
            self.add_graphical_elements(self.ms2frame(self.media_player.position()))

    def ms2frame(self, ms):
        frame = (ms/1000) * self.fps
        return int(frame)

    def frame2ms(self, frame):
        ms = (frame/self.fps) * 1000
        return int(ms)

    # -------------------------------------------------------------------
    # METHODS_graphics
    # -------------------------------------------------------------------
    def def_colormap(self):
        # set basic colormap
        trans, size = self.trans, self.size
        # basic
        red_b = QColor(225, 0, 0, trans)
        blue_b = QColor(0, 0, 225, trans)
        green_b = QColor(0, 225, 0, trans)
        magenta_b = QColor(225, 0, 225, trans)
        self.colormap_b = [red_b, blue_b, green_b, magenta_b]
        # lighter
        red_l = QColor(240, 140, 140, trans)
        blue_l = QColor(140, 140, 240, trans)
        green_l = QColor(140, 240, 140, trans)
        magenta_l = QColor(240, 140, 240, trans)
        self.colormap_l = [red_l, blue_l, green_l, magenta_l]
        # darker
        red_d = QColor(133, 3, 3, trans)
        blue_d = QColor(3, 3, 133, trans)
        green_d = QColor(3, 133, 3, trans)
        magenta_d = QColor(133, 3, 133, trans)
        self.colormap_d = [red_d, blue_d, green_d, magenta_d]
        
        self.colormap = [self.colormap_b, self.colormap_l, self.colormap_d]

        self.gray = QColor(150, 150, 150, trans)
        self.invisible = QColor(0, 0, 0, 0)

        self.colorsize = size
        self.graysize = size*2

        # add additional codes

    def add_graphical_elements(self, current_frame):
        # clear original widgets
        for items in self.inf_graphic:
            for item in items:
                self.scene.removeItem(item) # 이 코드를 대체하면 trajetory를 띄울 수 있을 것 같음
        self.inf_graphic = []

        #current_frame = 0 if current_frame==0 else min(current_frame+1, int(self.totalframe)-1) # should be modified

        # draw circle
        for i in range(len(self.instance_list)):
            instance = self.instance_list[i]
            list_of_graphic = []
            for n in range(len(self.node_list)):
                node = self.node_list[n]
                coord_data = self.file_data.find_instance_data(instance).find_node_data(node)
                # show original data
                if self.args_main.show_raw_data:
                    x = coord_data.x[current_frame]
                    y = coord_data.y[current_frame]
                    # if x or y is none
                    if (x==None or y==None):
                        circle = QGraphicsEllipseItem(0, 0, self.graysize, self.graysize)
                        circle.setBrush(QBrush(self.invisible))
                        circle.setPen(QPen(Qt.NoPen)) # type: ignore 
                    else:
                        #print(instance, node, "Start", x,y)
                        x = x*self.resol_const
                        y = y*self.resol_const
                        circle = QGraphicsEllipseItem(x-self.graysize/2, y-self.graysize/2, self.graysize, self.graysize)
                        # circle = QGraphicsEllipseItem(x+self.bias_x, y+self.bias_y, size, size)
                        circle.setBrush(QBrush(self.gray))
                        circle.setPen(QPen(Qt.NoPen)) # type: ignore 
                    self.scene.addItem(circle)
                    list_of_graphic.append(circle)
                if True:
                    x_s = coord_data.x_smoothing[current_frame]
                    y_s = coord_data.y_smoothing[current_frame]
                    # if x or y is none
                    if (x_s==None or y_s==None):
                        circle_s = QGraphicsEllipseItem(0, 0, self.colorsize, self.colorsize)
                        circle_s.setBrush(QBrush(self.invisible))
                        circle_s.setPen(QPen(Qt.NoPen)) # type: ignore 
                    else:
                        #print(instance, node, "Start", x,y)
                        x_s = x_s*self.resol_const
                        y_s = y_s*self.resol_const
                        circle_s = QGraphicsEllipseItem(x_s-self.colorsize/2, y_s-self.colorsize/2, self.colorsize, self.colorsize)
                        # circle = QGraphicsEllipseItem(x+self.bias_x, y+self.bias_y, size, size)
                        colormap_id = self.instance_colormap[i][n]
                        circle_s.setBrush(QBrush(self.colormap[colormap_id][i]))
                        circle_s.setPen(QPen(Qt.NoPen)) # type: ignore 

                    self.scene.addItem(circle_s)
                    list_of_graphic.append(circle_s)
            self.inf_graphic.append(list_of_graphic)

            if self.args_main.show_proofread_alert:
                # print "Need Proofreading" when z score is under criteria_range
                if self.file_data.instance_z[i][current_frame] == None:
                    self.text_items[i].setDefaultTextColor(self.invisible)
                elif self.file_data.instance_z[i][current_frame] < self.args_main.z_criteria:
                    self.text_items[i].setDefaultTextColor(self.colormap[0][i])
                else:
                    self.text_items[i].setDefaultTextColor(self.invisible)
        
    # -------------------------------------------------------------------
    # METHODS_qtWidgets
    # -------------------------------------------------------------------

    # define key press event
    def keyPressEvent(self, e):
        self.delay = 5
        if e.key() == Qt.Key_Space: # type: ignore # Space key play/pause video 
            self.video_playorpause()
        elif e.key() == Qt.Key_Escape: # type: ignore # ESC key quits
            self.close()
        elif e.key() == Qt.Key_Comma: # type: ignore # < key moves to prev frame
            self.prevfbt_clicked()
        elif e.key() == Qt.Key_Period:# type: ignore  # > key moves to next frame
            self.nextfbt_clicked()
        elif e.key() == Qt.Key_A: # type: ignore # Left key moves to Nf prev frame # here, A
            self.prevNfbt_clicked()
        elif e.key() == Qt.Key_D: # type: ignore # Right key moves to Nf next frame # here, D
            self.nextNfbt_clicked()
        else:
            return
        self.speedspin_changed()
        
    def wheelEvent(self, e):
        # scroll control
        if self.media_player.state() == 1:
            self.media_player.pause()
        frame = self.videoslider.value() - e.angleDelta().y()
        position = self.frame2ms(frame)
        self.videoslider.setValue(frame)
        self.media_player.setPosition(position)
        self.add_graphical_elements(frame) 
        if self.is_video_played:
            self.media_player.pause()
            #time.sleep(0.1)
            self.media_player.play()
        else:
            # to remove lagging 
            self.media_player.play()
            self.media_player.pause()
        self.speedspin_changed()

    # buttons
    def prevNfbt_clicked(self):
        self.move_frame("backward", self.media_player.position(), self.Nf)
        self.videoframelabel_set()
    def prevfbt_clicked(self):
        self.move_frame("backward", self.media_player.position(), 1)
        self.videoframelabel_set()
    def playbt_clicked(self):
        self.video_playorpause()
    def nextfbt_clicked(self):
        self.move_frame("forward", self.media_player.position(), 1)
        self.videoframelabel_set()
    def nextNfbt_clicked(self):
        self.move_frame("forward", self.media_player.position(), self.Nf)
        self.videoframelabel_set()

    def colorbt_clicked(self):
        colorset = self.colorcomb.currentText()
        n = self.nodecomb.currentIndex()
        i = self.instcomb.currentIndex()
        #print(n, i)
        if colorset == "Basic":
            self.instance_colormap[i][n] = 0
        elif colorset == "Lighter":
            self.instance_colormap[i][n] = 1
        elif colorset == "Darker":
            self.instance_colormap[i][n] = 2
        self.add_graphical_elements(self.ms2frame(self.media_player.position()))


    # filecomb_set: Set lists of comb
    # filecomb_changed: Defines the function when selection changes
    def filecomb_set(self):
        for i in range(len(self.list_vid)):
            self.filecomb.addItem(self.list_vid[i])
    def filecomb_changed(self):
        file_sel = self.filecomb.currentText()
        self.load_selected_video(file_sel)

    def instcomb_set(self):
        self.instcomb.clear()
        for i in self.instance_list:
            self.instcomb.addItem(i)
    def nodecomb_set(self):
        if self.nodecomb.count() == 0:
            for n in self.node_list:
                self.nodecomb.addItem(n)

    def colorcomb_set(self):
        self.colorcomb.addItems(["Basic", "Lighter", "Darker"])
        
    # spinbox
    def framespin_valueChanged(self):
        self.Nf = self.framespin.value()

    def speedspin_changed(self):
        speed = self.speedspin.value()
        self.media_player.setPlaybackRate(speed)

    # textbrowser, label 
    def videoframelabel_set(self):
        currentpos = self.media_player.position()
        currentfr = self.ms2frame(currentpos)
        self.videoframelabel.setText(f"Frame: {currentfr}/{int(self.totalframe)}")

    # videoslider
    def videoslider_setrange(self):
        self.videoslider.setRange(0, self.totalframe-1)
    def videoslider_pressed(self):
        self.media_player.pause()
    def videoslider_moved(self): #, frame
        frame = self.videoslider.value()
        position = self.frame2ms(frame)
        self.media_player.setPosition(position)
        self.videoframelabel_set()
    def videoslider_released(self):
        if(self.is_video_played):
            #time.sleep(0.1)
            self.media_player.play()
    def videoslider_reset(self):
        self.videoslider.setValue(0)

    def sizeslider_moved(self):
        self.size = self.sizeslider.value()
        self.def_colormap()
        self.add_graphical_elements(self.ms2frame(self.media_player.position()))
    def translider_moved(self):
        self.trans = self.translider.value()
        self.def_colormap()
        self.add_graphical_elements(self.ms2frame(self.media_player.position()))

    # checkbox
    def rawdatacheck_changed(self):
        self.args_main.show_raw_data = self.rawdatacheck.isChecked()
        self.add_graphical_elements(self.ms2frame(self.media_player.position()))
    def alertcheck_changed(self):
        self.args_main.show_proofread_alert = self.alertcheck.isChecked()
        self.add_graphical_elements(self.ms2frame(self.media_player.position()))
        

    # -------------------------------------------------------------------
    # Error handling
    # -------------------------------------------------------------------

    def handle_error(self, error):
        pass
        #print("Error occurred: ", error, self.media_player.errorString())

    def handle_media_status(self, status):
        pass
        # print("Media status changed: ", status)

    def handle_state_changed(self, state):
        pass
        # print("State changed: ", state)

    # -----------------------------------------------

