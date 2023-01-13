#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Fri Sep 28 11:59:40 2018

@author: jungbluth
"""

# AFMD standard python packages
import io
import itertools
import math
import os
import re
import sys
import time

#logging packages
import logging
import warnings

import platform
import pathlib




import serial

# for zurich instruments lock in amplifier:
import zhinst.utils
import zhinst.ziPython

# for the gui
from PyQt5 import QtCore, QtGui, QtWidgets
from tkinter import Tk
from tkinter import filedialog 

# AFMD standard scientific python packages
import matplotlib
import matplotlib.pyplot as plt
from matplotlib import style
import pandas as pd
from numpy import *
from scipy.interpolate import interp1d

# bit to unicode translator
import codecs 

# AFMD modules
import GUI_template
from monochromator import Monochromator 
from microscope.filterwheels.thorlabs import ThorlabsFilterWheel
from lockin import LockIn



class MainWindow(QtWidgets.QMainWindow):
    """sEQE control software main window. 
    
    Parameters
    ----------
    QtWidgets.QMainWindow: 
        The Qt5 GUI Interface
    """
    def __init__(self):
        
         # Initialising ports, device names and save path
        file = pathlib.Path('pathsNdevices_config.txt')
        if file.exists():
            pNpdata = file.read_text().split(',')
            
            self.zurich_device = pNpdata[0]
            self.filter_port = pNpdata[1]
            self.mono_port =  pNpdata[2]
            self.save_path = pNpdata[3]
            
            print(f'Found the following details for setup in pathsNdevices.txt: \n zurich instrument device name: {self.zurich_device} \n second filter wheel port: {self.filter_port} \n monochromator port: {self.mono_port} \n default path where data are saved: {self.save_path}')
            
            for i in range(len(pNpdata)):
                if pNpdata[i] == '':
                    print('Empty string in pathsNdevices.txt found. The current file will be deleted, please recreate the file')
                    file.unlink()  # to delete file
                
        else:
            file.touch(exist_ok = False)
            if platform.system() == 'Linux':
                port_prefix = '/dev/ttyUSB'
            elif platform.system() == 'Windows':
                port_prefix = 'COM'
            else:
                self.logger.error('Operating System is not known - defaulting to Linux system')
                port_prefix = '/dev/tty'
            
            self.zurich_device = str(input('Which zurich instrument device is used  ? - type device address string e.g. UHF-DEV2000.  ')) #'hf2-dev838'
            self.filter_port = port_prefix+str(input('Which port number is used by the second filter wheel ? - type a number  '))# AFMD default 'COM4'
            self.mono_port =  port_prefix+str(input('Which port number is used by the monochromator ? - type a number  '))# AFMD default 'COM1'
            self.save_path = pathlib.Path(input('Where do you want to save your data ? - copy absolute path of folder  '))# AFMD default 'C:\\Users\\Public\\Documents\\sEQE'
            
            file.write_text(f'{self.zurich_device},{self.filter_port},{self.mono_port},{self.save_path}')

        QtWidgets.QMainWindow.__init__(self)
        
        warnings.filterwarnings("ignore")
        
        self.logger = self.get_logger()
        
        # Set up the user interface from Designer
        
        self.ui = GUI_template.Ui_MainWindow()
        self.ui.setupUi(self)         
        
        # Connections
        
        self.mono_connected = False   # Set the monochromator connection to False
        self.lockin_connected = False   # Set the Lock-in connection to False
        self.filter_connected = False  # Set the filterwheel connection to False
        
        # Initialize Monochromator and Lock-In Amplifier
        self.mono = Monochromator(self.mono_port)
        self.lockin = LockIn(self.zurich_device)
        
        # General Setup
        self.channel = 1
        self.c = str(self.channel-1) 
        self.c6 = str(6)

        self.do_plot = True

        self.complete_scan = False
        
        # these can not be defined here, due to empty text boxes at start up 
        # self.userName = self.ui.user.text()
        # self.experimentName = self.ui.experiment.text()
        # self.path =f'{self.save_path}/{self.userName}/{self.experimentName}'

        self.filter_addition = 'None' ####################################################################################
        
        
        # Handle Monochromator Buttons
        
        self.ui.connectButton_Mono.clicked.connect(self.connectToMono)  # Connect only to Monochromator        
        self.ui.monoGotoButton.clicked.connect(self.MonoHandleWavelengthButton)   # Go to specific wavelength
        self.ui.monoSpeedButton.clicked.connect(self.MonoHandleSpeedButton)   # Set scan speed
        self.ui.monoGratingButton.clicked.connect(self.MonoHandleGratingButtons)   # Change grating    
        self.ui.monoFilterButton.clicked.connect(self.MonoHandleFilterButton)   # Change filter
        
        self.ui.monoFilterInitButton.clicked.connect(self.MonoHandleFilterInitButton)   # Initialize filter
            
        # Handle Lock-in Buttons
        
        self.ui.connectButton_Lockin.clicked.connect(self.connectToLockin)   # Connect only to Lock-in         
        self.ui.lockinParameterButton.clicked.connect(self.LockinHandleParameterButton)   # Set Lock-in parameters

        # Handle Filterwheel Buttons
        
        self.ui.connectButton_Filter.clicked.connect(self.connectToFilter) # Connect only to Filterwheel
         
        # Handle Combined Buttons
        
        self.ui.connectButton.clicked.connect(self.connectToEquipment)
        self.ui.completeScanButton_start.clicked.connect(self.MonoHandleCompleteScanButton)  #########################################################################################
        self.ui.completeScanButton_stop.clicked.connect(self.HandleStopCompleteScanButton)   #########################################################################################
        
        # Save and Import data from files or naming from path
        
        self.ui.save_to_file.clicked.connect(self.save_mono_parameter) # Save measurement parameter to file
        self.ui.import_from_file.clicked.connect(self.load_mono_parameter)
        self.ui.importNamingButton.clicked.connect(self.load_naming)
        
        
        # Import photodiode calibration files

        Si_file = pd.ExcelFile("FDS100-CAL.xlsx") # The files are in the sEQE Analysis folder
#        print(Si_file.sheet_names)
        self.Si_cal = Si_file.parse('Sheet1')
#        print(self.Si_cal)
        
        InGaAs_file = pd.ExcelFile("FGA21-CAL.xlsx")
        self.InGaAs_cal = InGaAs_file.parse('Sheet1')     
        
    # Close connection to Monochromator and Thorlabs filter wheel when window is closed
    
    def __del__(self):
        try:
            self.thorfilterwheel.close()
            with serial.Serial(self.mono_port, 9600, timeout=0) as self.p:
                self.p.close()
        except:
            pass 
        
        
# -----------------------------------------------------------------------------------------------------------

    #### Functions to import data into GUI
    
# -----------------------------------------------------------------------------------------------------------





# -----------------------------------------------------------------------------------------------------------        

    #### Functions to connect to Monochromator and Lock-in

# -----------------------------------------------------------------------------------------------------------
        
    # Establish serial connection to Monochromator
    
    def connectToMono(self):
        """Function to establish connection to monochromator. 
        
        Returns
        -------
        None
        
        """
        try:
            self.mono_connected = self.mono.connect()
            
            if self.mono_connected:
                self.logger.info('Connection to Monochromator Established')
                self.ui.imageConnect_mono.setPixmap(QtGui.QPixmap("Button_on.png"))
                
        except Exception as err:
            self.logger.exception("Unexpected error during execution of connectToMono function:")
            
    # Establish connection to LOCKIN
    
    def connectToLockin(self):    
        """Function to establish connection to Lockin.
        
        Returns
        -------
        list
            Zurich Instruments localhost name and device details
        """
        try: 
            self.daq, self.device, self.lockin_connected = self.lockin.connect()

            self.ui.imageConnect_lockin.setPixmap(QtGui.QPixmap("Button_on.png"))

            return self.daq, self.device
        
        except Exception as err:
            self.logger.exception("Unexpected error during execution of connectToLockin function:")
            
    # Establish connection to Filterwheel

    def connectToFilter(self):
        """Function to establish connection to filter wheel.
        
        Returns
        -------
        None
        
        """
        try:
            self.thorfilterwheel = ThorlabsFilterWheel(com=self.filter_port) # Initialize here = GUI openable without equipment physically connected
            if self.thorfilterwheel.position == 0:
                self.filter_connected = True
                self.logger.info("Connection to Thorlabs filter wheel established")
                self.ui.imageConnect_filter.setPixmap(QtGui.QPixmap("Button_on.png"))
            else:
                self.logger.exception('Could not find the Thorlabs filter wheel in position 1, i.e. in open position. Please check current filter wheel position manually.')
                self.filter_connected = False
        except Exception as err:
            self.logger.exception("Unexpected error during execution of connectToFilter function:")
# -----------------------------------------------------------------------------------------------------------        
        
    # Establish connection to all equipment
        
    def connectToEquipment(self):
        """Function to establish connection to monochromator, Lockin & filter wheel.
        
        Returns
        -------
        None
        
        """
        try:
            self.connectToLockin()
            self.connectToMono()
            self.connectToFilter()

            self.ui.imageConnect.setPixmap(QtGui.QPixmap("Button_on.png"))
            
        except Exception as err:
             self.logger.exception("Unexpected error during execution of connectToEquipment function:")
    
# -----------------------------------------------------------------------------------------------------------        
    
    #### Functions to handle parameter buttons for Monochromator and Lock-in
    
# -----------------------------------------------------------------------------------------------------------            
       
    ## Monochromator Functions
    
    # Set and GOTO wavelength
    
    def MonoHandleWavelengthButton(self):   # Function sets desired wavelength and calls chooseWavelength function
        """Function to read wavelength value from GUI.
        
        Returns
        -------
        None
        
        """
        wavelength = self.ui.pickNM.value()
        self.mono.chooseWavelength(wavelength)
      
    # Update the scan speed
            
    def MonoHandleSpeedButton(self):   # Function sets desired scan speed and calls chooseScanSpeed function
        """Function to read monochromator speed from GUI.
        
        Returns
        -------
        None
        
        """
        speed = self.ui.pickScanSpeed.value()
        self.mono.chooseScanSpeed(speed)

    # Set and move to grating 
    
    def MonoHandleGratingButtons(self):   # Function sets desired grating number and calls chooseGrating function
        """Function to read grating number from monochromator.
        
        Returns
        -------
        None
        
        """
        if self.ui.Blaze_300.isChecked():
            gratingNo = 1
        elif self.ui.Blaze_750.isChecked():
            gratingNo = 2
        elif self.ui.Blaze_1600.isChecked():
            gratingNo = 3
            
        self.mono.chooseGrating(gratingNo)
       
    # Update filter number
            
    def MonoHandleFilterButton(self):
        """Function to read filter position from GUI.
        
        Returns
        -------
        None
        
        """
        filterNo = int(self.ui.pickFilter.value())
        self.mono.chooseFilter(filterNo)

    # Initialize filter 

    def MonoHandleFilterInitButton(self):
        """Function to read filter initialization position from GUI.
        
        Returns
        -------
        None
        
        """
        filterStart = self.ui.pickFilterInitStart.value()
        filterDiff = int(8-filterStart)
        self.mono.initializeFilter(filterDiff)
        self.ui.imageInit_filterwheel.setPixmap(QtGui.QPixmap("Button_on.png"))
        self.logger.info('Monochromator Filter Wheel initialized') 
    
# -----------------------------------------------------------------------------------------------------------        
    
    ## Lock-in Functions
    
    # Define and set Lock-in parameters
    
    def LockinHandleParameterButton(self):
        """Function to read Lockin amplification value from GUI.
        
        Returns
        -------
        None
        
        """
        try:
            if self.lockin_connected:
                self.amplification = self.ui.pickAmp.value()
                self.LockinUpdateParameters(self.amplification)
            else: 
                self.logger.info('Lock-In not connected')
                
        except Exception as err:
            self.logger.exception("Unexpected error during execution of LockinHandleParametersButton function:")
        
    def LockinUpdateParameters(self,amplification):   # Function sets desired Lock-in parameters and calls setParameter function 
        """Function to update Lockin parameters.
        
        Parameters
        ----------
        amplification int, required
            amplification value of the LockIn signal
        
        Returns
        -------
        None
        
        Raises
        ------
        LoggerError
            Raises error if Lockin not connected or Exception handling

        """
        try:
            if self.lockin_connected:  
                self.c_2 = str(self.channel) # Channel 2, with value 1, for the reference input
                self.tc = self.ui.pickTC.value() # Import value for time constant
                self.rate = self.ui.pickDTR.value() # Import value for data transfer rate
                self.lowpass = self.ui.pickLPFO.value() # Import value for low pass filter order
                self.range = 2 # This sets the default voltage range to 2
                self.ac = 0 # AC off
                self.imp50 = 0 # 50 Ohm off
                self.imp50_2 = 1 # Turn on 50 Ohm on channel 2 to attenuate signal from chopper controller as reference signal
                self.diff = 1 # Diff off
                self.diff_2 = 0 #diff for channel 2 off
    #            if self.ui.acButton.isChecked(): # AC on if button is checked
    #                self.ac = 1
    #            if self.ui.imp50Button.isChecked(): # 50 Ohm on if button is checked
    #                self.imp50 = 1
    #            if self.ui.diffButton.isChecked(): # Diff on if button is checked
    #                self.diff = 1                
    #            self.frequency = self.ui.pickFreq.value() # For manual frequency control. The frequency tab is currently not implemented in the GUI

                self.lockin.setParameters(self.diff_2, self.diff, self.imp50, self.imp50_2, self.ac, self.range, self.lowpass, self.rate, self.tc, self.c_2, amplification)
                self.logger.info('Updating Lock-In Settings')

            else:
                self.logger.error("Lock-In not connected")
                
        except Exception as err:
            self.logger.exception("Unexpected error during execution of LockinUpdateParameters function:")
             
        
# -----------------------------------------------------------------------------------------------------------        
    
    #### Functions to handle filter and grating changes

# -----------------------------------------------------------------------------------------------------------  
  
        
    def monoCheckFilter(self, wavelength):   # Filter switching points from GUI
        """
        Function to update position of first filter wheel from GUI defaults.
            
        Parameters
        ----------
        wavelength: float, required
            Current wavelength position of monochromator

        Returns
        -------
        None
        
        Raises
        ------
        LoggerError
            Raises error if filter wheel commands are invalid or monochromator not connected

        """
        filterNo = self.mono.checkFilter()
        data_average_factor = self.ui.data_average_factor.value() # TODO: Add GUI window with corresponding name

        startNM_F2 = int(self.ui.startNM_F2.value())
        stopNM_F2 = int(self.ui.stopNM_F2.value())                
        startNM_F3 = int(self.ui.startNM_F3.value())
        stopNM_F3 = int(self.ui.stopNM_F3.value())
        startNM_F4 = int(self.ui.startNM_F4.value())
        stopNM_F4 = int(self.ui.stopNM_F4.value())
        startNM_F5 = int(self.ui.startNM_F5.value())
        stopNM_F5 = int(self.ui.stopNM_F5.value())            

        if startNM_F2 <= wavelength < stopNM_F2: # Filter 3 [FESH0700]: from 350 - 649  -- including start, excluing end
            shouldbeFilterNo = 2                  
        elif startNM_F3 <= wavelength < stopNM_F3: # Filter 3 [FESH0700]: from 350 - 649  -- including start, excluing end
            shouldbeFilterNo = 3  
        elif startNM_F4 <= wavelength < stopNM_F4: # Filter 4 [FESH1000]: from 650 - 984  -- including start, excluding end
            shouldbeFilterNo = 4 
        elif startNM_F5 <= wavelength <= stopNM_F5: # Filter 5 [FELH0950]: from 985 - 1800  -- including start, including end
            shouldbeFilterNo = 5
        else:   
            self.logger.error('Error: Filter Out Of Range')

        if shouldbeFilterNo != filterNo:
            self.mono.chooseFilter(shouldbeFilterNo)    


            # Take data and discard it, this is required to avoid kinks
            # Poll data for 5 time constants, second parameter is poll timeout in [ms] (recomended value is 500ms) 
            dataDict = self.daq.poll(data_average_factor*self.tc,500)  
            # Dictionary with ['timestamp']['x']['y']['frequency']['phase']['dio']['trigger']['auxin0']['auxin1']['time']

        else:
            pass
    
    def monoCheckGrating(self, wavelength):   # Grating switching points from GUI
        """Function to update monochromator grating position from GUI defaults.
        
        Parameters
        ----------
        wavelength: float, required
            Current wavelength position of monochromator

        Returns
        --------
        None
        
        Raises
        ------
        LoggerError
            Raises error if grating commands are invalid or monochromator not connected

        """
        gratingNo = self.mono.checkGrating()
        
        startNM_G1 = int(self.ui.startNM_G1.value())
        stopNM_G1 = int(self.ui.stopNM_G1.value())
        startNM_G2 = int(self.ui.startNM_G2.value())
        stopNM_G2 = int(self.ui.stopNM_G2.value())
        startNM_G3 = int(self.ui.startNM_G3.value())
        stopNM_G3 = int(self.ui.stopNM_G3.value()) 

        if startNM_G1 <= wavelength < stopNM_G1: # Grating 1: from 350 - 549  -- including start, excluding end
            shouldbeGratingNo = 1  
        elif startNM_G2 <= wavelength < stopNM_G2: # Grating 2: from 550 - 1299  -- including start, excluding end
            shouldbeGratingNo = 2  
        elif startNM_G3 <= wavelength <= stopNM_G3: # Grating 3: from 1300 - 1800  -- including start, including end
            shouldbeGratingNo = 3
        else:   # Do I need this?
            self.logger.error('Error: Grating Out Of Range')
        if shouldbeGratingNo != gratingNo:
            self.mono.chooseGrating(shouldbeGratingNo)

            # Take data and discard it, this is required to avoid kinks                
            # Poll data for 5 time constants, second parameter is poll timeout in [ms] (recomended value is 500ms) 
            dataDict = self.daq.poll(5*self.tc,500)  
            # Dictionary with ['timestamp']['x']['y']['frequency']['phase']['dio']['trigger']['auxin0']['auxin1']['time']

        else:
            pass

# -----------------------------------------------------------------------------------------------------------

    #### Function to handle filter changes of Thorlabs filter wheel

# -----------------------------------------------------------------------------------------------------------

    def thorChangeFilter(self, pos):
        """Function to update position of second filter wheel.
        
        Parameters
        ----------
        pos: int, required
            Target filter position, between 1-6
            
        Returns
        -------
        bool
            True if connection to second filter wheel is successful, False otherwise
            
        Raises
        ------
        LoggerError
            Raises error if second filter wheel not connected
       
        """
        try:
            if not self.filter_connected:
                self.logger.exception("External Filter Wheel Not Connected")
                return False

            self.thorfilterwheel._do_set_position(pos-1) # -1 due to microscope.thorfilterwheel code accepting only 0-5
            self.logger.info(f'Thorlabs filterwheel moved to {pos}. position')
            return True
        
        except Exception as err: 
            self.logger.exception("Unexpected error during execution of thorChangeFilter function:")
        
# -----------------------------------------------------------------------------------------------------------        
    
    #### Functions to handle measurement parameter and measurment itself
    
# -----------------------------------------------------------------------------------------------------------  

    def MonoHandleCompleteScanButton(self):
        """Function to measure samples with different filters.
        
        Returns
        -------
        None
        
        """
        try: 
            self.complete_scan = True
            self.ui.imageCompleteScan_start.setPixmap(QtGui.QPixmap("Button_on.png"))
            measurement_values = {}
            if self.ui.scan_noFilter.isChecked():

                self.thorChangeFilter(1)

                if self.thorChangeFilter(1):

                    self.filter_addition = 'no'

                    self.logger.info('Moving to Open Filter Position')

                    start_f1 = self.ui.scan_startNM_1.value()
                    stop_f1 = self.ui.scan_stopNM_1.value()
                    step_f1 = self.ui.scan_stepNM_1.value()
                    amp_f1 = self.ui.scan_pickAmp_1.value()

                    measurement_values['f1']=[start_f1,stop_f1,step_f1,amp_f1]

                    self.amplification = amp_f1
                    self.LockinUpdateParameters(self.amplification)
                    self.MonoHandleSpeedButton() 

                    scan_list = self.createScanJob(start_f1, stop_f1, step_f1)
                    self.HandleMeasurement(scan_list, start_f1, stop_f1, step_f1, amp_f1, 3)

            if self.ui.scan_Filter2.isChecked():

                self.thorChangeFilter(2)

                if self.thorChangeFilter(2):

                    self.filter_addition = str(int(self.ui.cuton_filter_2.value()))

                    self.logger.info('Moving to %s nm Filter' % self.filter_addition)

                    start_f2 = self.ui.scan_startNM_2.value()
                    stop_f2 = self.ui.scan_stopNM_2.value()
                    step_f2 = self.ui.scan_stepNM_2.value()
                    amp_f2 = self.ui.scan_pickAmp_2.value()

                    measurement_values['f2']=[start_f2,stop_f2,step_f2,amp_f2]

                    self.amplification = amp_f2
                    self.LockinUpdateParameters(self.amplification)
                    self.MonoHandleSpeedButton()

                    scan_list = self.createScanJob(start_f2, stop_f2, step_f2)
                    self.HandleMeasurement(scan_list, start_f2, stop_f2, step_f2, amp_f2, 3)

            if self.ui.scan_Filter3.isChecked():

                self.thorChangeFilter(3)

                if self.thorChangeFilter(3):

                    self.filter_addition = str(int(self.ui.cuton_filter_3.value()))

                    self.logger.info('Moving to %s nm Filter' % self.filter_addition)

                    start_f3 = self.ui.scan_startNM_3.value()
                    stop_f3 = self.ui.scan_stopNM_3.value()
                    step_f3 = self.ui.scan_stepNM_3.value()
                    amp_f3 = self.ui.scan_pickAmp_3.value()

                    measurement_values['f3']=[start_f3,stop_f3,step_f3,amp_f3]

                    self.amplification = amp_f3
                    self.LockinUpdateParameters(self.amplification)
                    self.MonoHandleSpeedButton()

                    scan_list = self.createScanJob(start_f3, stop_f3, step_f3)
                    self.HandleMeasurement(scan_list, start_f3, stop_f3, step_f3, amp_f3, 3)

            if self.ui.scan_Filter4.isChecked():

                self.thorChangeFilter(4)

                if self.thorChangeFilter(4):

                    self.filter_addition = str(int(self.ui.cuton_filter_4.value()))

                    self.logger.info('Moving to %s nm Filter' % self.filter_addition)

                    start_f4 = self.ui.scan_startNM_4.value()
                    stop_f4 = self.ui.scan_stopNM_4.value()
                    step_f4 = self.ui.scan_stepNM_4.value()
                    amp_f4 = self.ui.scan_pickAmp_4.value()

                    measurement_values['f4']=[start_f4,stop_f4,step_f4,amp_f4]

                    self.amplification = amp_f4
                    self.LockinUpdateParameters(self.amplification)
                    self.MonoHandleSpeedButton()

                    scan_list = self.createScanJob(start_f4, stop_f4, step_f4)
                    self.HandleMeasurement(scan_list, start_f4, stop_f4, step_f4, amp_f4, 3)

            if self.ui.scan_Filter5.isChecked():

                self.thorChangeFilter(5)

                if self.thorChangeFilter(5):

                    self.filter_addition = str(int(self.ui.cuton_filter_5.value()))

                    self.logger.info('Moving to %s nm Filter' % self.filter_addition)

                    start_f5 = self.ui.scan_startNM_5.value()
                    stop_f5 = self.ui.scan_stopNM_5.value()
                    step_f5 = self.ui.scan_stepNM_5.value()
                    amp_f5 = self.ui.scan_pickAmp_5.value()

                    measurement_values['f5']=[start_f5,stop_f5,step_f5,amp_f5]

                    self.amplification = amp_f5
                    self.LockinUpdateParameters(self.amplification)
                    self.MonoHandleSpeedButton()

                    scan_list = self.createScanJob(start_f5, stop_f5, step_f5)
                    self.HandleMeasurement(scan_list, start_f5, stop_f5, step_f5, amp_f5, 3)

            if self.ui.scan_Filter6.isChecked():

                self.thorChangeFilter(6)

                if self.thorChangeFilter(6):

                    self.filter_addition = str(int(self.ui.cuton_filter_6.value()))

                    self.logger.info('Moving to %s nm Filter' % self.filter_addition)

                    start_f6 = self.ui.scan_startNM_6.value()
                    stop_f6 = self.ui.scan_stopNM_6.value()
                    step_f6 = self.ui.scan_stepNM_6.value()
                    amp_f6 = self.ui.scan_pickAmp_6.value()

                    measurement_values['f6']=[start_f6,stop_f6,step_f6,amp_f6]

                    self.amplification = amp_f6
                    self.LockinUpdateParameters(self.amplification)
                    self.MonoHandleSpeedButton()

                    scan_list = self.createScanJob(start_f6, stop_f6, step_f6)
                    self.HandleMeasurement(scan_list, start_f6, stop_f6, step_f6, amp_f6, 3)

            self.thorChangeFilter(1) 
            self.logger.info('Moving to open filter')               
            self.mono.chooseFilter(1)
            self.complete_scan = False   
            self.ui.imageCompleteScan_start.setPixmap(QtGui.QPixmap("Button_off.png"))
            self.ui.imageCompleteScan_stop.setPixmap(QtGui.QPixmap("Button_off.png"))

            self.logger.info('Finished Measurement') 

            measurement_parameter = pd.DataFrame.from_dict(measurement_values)
                    #self.save(measurement_values)
                
        except Exception as err:
            self.logger.exception("Unexpected error during execution of MonoHandleCompleteScanButton function:")
            
            
    def load_naming(self):
        """Function to load naming from directory path

        Parameters
        ----------
        None
            
        Returns
        -------
        None 
        
        """
        
        try:
            
            root = Tk() # Creates master window for tkinters filedialog window
            root.withdraw() # Hides master window
            filepath = filedialog.askdirectory() # Creates pop-up window to ask for file save
            
            names = filepath.split("/")
            self.ui.user.setText(names[5])
            self.ui.experiment.setText(names[6])
            
        except Exception as err:
            self.logger.exception("Unexpected error during execution of load_naming function:")
    
    def save_mono_parameter(self):
        """Function to save monochromator measurement parameters to file
        
        Parameters
        ----------
        None
            
        Returns
        -------
        None
        
        Raises
        ------
        LoggerWarning
            Raises warning if tkinter saving dialog was closed without entering filename
        
        Notes
        -----
        Reads the spinbox values and saves them into a file selected via tkinter dialog
        
        """
        
        try:

            measurement_values = {}

            if self.ui.scan_noFilter.isChecked():

                start_f1 = self.ui.scan_startNM_1.value()
                stop_f1 = self.ui.scan_stopNM_1.value()
                step_f1 = self.ui.scan_stepNM_1.value()
                amp_f1 = self.ui.scan_pickAmp_1.value()

                measurement_values['f1']=[start_f1,stop_f1,step_f1,amp_f1]

            if self.ui.scan_Filter2.isChecked():

                start_f2 = self.ui.scan_startNM_2.value()
                stop_f2 = self.ui.scan_stopNM_2.value()
                step_f2 = self.ui.scan_stepNM_2.value()
                amp_f2 = self.ui.scan_pickAmp_2.value()

                measurement_values['f2']=[start_f2,stop_f2,step_f2,amp_f2]


            if self.ui.scan_Filter3.isChecked():

                start_f3 = self.ui.scan_startNM_3.value()
                stop_f3 = self.ui.scan_stopNM_3.value()
                step_f3 = self.ui.scan_stepNM_3.value()
                amp_f3 = self.ui.scan_pickAmp_3.value()

                measurement_values['f3']=[start_f3,stop_f3,step_f3,amp_f3]

            if self.ui.scan_Filter4.isChecked():

                start_f4 = self.ui.scan_startNM_4.value()
                stop_f4 = self.ui.scan_stopNM_4.value()
                step_f4 = self.ui.scan_stepNM_4.value()
                amp_f4 = self.ui.scan_pickAmp_4.value()

                measurement_values['f4']=[start_f4,stop_f4,step_f4,amp_f4]

            if self.ui.scan_Filter5.isChecked():

                start_f5 = self.ui.scan_startNM_5.value()
                stop_f5 = self.ui.scan_stopNM_5.value()
                step_f5 = self.ui.scan_stepNM_5.value()
                amp_f5 = self.ui.scan_pickAmp_5.value()

                measurement_values['f5']=[start_f5,stop_f5,step_f5,amp_f5]

            if self.ui.scan_Filter6.isChecked():

                start_f6 = self.ui.scan_startNM_6.value()
                stop_f6 = self.ui.scan_stopNM_6.value()
                step_f6 = self.ui.scan_stepNM_6.value()
                amp_f6 = self.ui.scan_pickAmp_6.value()

                measurement_values['f6']=[start_f6,stop_f6,step_f6,amp_f6]

            measurement_parameter = pd.DataFrame.from_dict(measurement_values)

            root = Tk() # Creates master window for tkinters filedialog window
            root.withdraw() # Hides master window
            filepath = filedialog.asksaveasfilename() # Creates pop-up window to ask for file save

            # This somehow destroys the Qt event manager, error message: 
            # "QCoreApplication::exec: The event loop is already running"
            # self.filename = str(input('What is the name of this measurement routine ?:  '))
            # if self.path.exists() not:
            #     os. 

            measurement_parameter.to_csv(filepath, index= False)
            self.logger.info('Saved measurement parameter into: '+ filepath) 
        
        except FileNotFoundError:
            self.logger.warning('No parameters were safed due to missing filename')
            
        except Exception as err:
            self.logger.exception("Unexpected error during execution of save_mono_parameter function:")
    
    
    def load_mono_parameter(self):
        """Function to load monochromator measurement parameters from file.
        
        Parameters
        ----------
        None
            
        Returns
        -------
        None
        
        Notes
        -----
        Selects a file via tkinter dialog, reads the values and sets measurement parameters
        
        """
        
        try:
            root = Tk() # Creates master window for tkinters filedialog window
            root.withdraw() # Hides master window
            filepath = filedialog.askopenfilename() # Creates pop-up window to ask for file save

            measurement_parameters = pd.read_csv(filepath)

            if self.ui.scan_noFilter.isChecked():

                self.ui.scan_startNM_1.setValue(measurement_parameters['f1'][0])
                self.ui.scan_stopNM_1.setValue(measurement_parameters['f1'][1])
                self.ui.scan_stepNM_1.setValue(measurement_parameters['f1'][2])
                self.ui.scan_pickAmp_1.setValue(measurement_parameters['f1'][3])

            if self.ui.scan_Filter2.isChecked():

                self.ui.scan_startNM_2.setValue(measurement_parameters['f2'][0])
                self.ui.scan_stopNM_2.setValue(measurement_parameters['f2'][1])
                self.ui.scan_stepNM_2.setValue(measurement_parameters['f2'][2])
                self.ui.scan_pickAmp_2.setValue(measurement_parameters['f2'][3])                

            if self.ui.scan_Filter3.isChecked():

                self.ui.scan_startNM_3.setValue(measurement_parameters['f3'][0])
                self.ui.scan_stopNM_3.setValue(measurement_parameters['f3'][1])
                self.ui.scan_stepNM_3.setValue(measurement_parameters['f3'][2])
                self.ui.scan_pickAmp_3.setValue(measurement_parameters['f3'][3])

            if self.ui.scan_Filter4.isChecked():

                self.ui.scan_startNM_4.setValue(measurement_parameters['f4'][0])
                self.ui.scan_stopNM_4.setValue(measurement_parameters['f4'][1])
                self.ui.scan_stepNM_4.setValue(measurement_parameters['f4'][2])
                self.ui.scan_pickAmp_4.setValue(measurement_parameters['f4'][3])

            if self.ui.scan_Filter5.isChecked():

                self.ui.scan_startNM_5.setValue(measurement_parameters['f5'][0])
                self.ui.scan_stopNM_5.setValue(measurement_parameters['f5'][1])
                self.ui.scan_stepNM_5.setValue(measurement_parameters['f5'][2])
                self.ui.scan_pickAmp_5.setValue(measurement_parameters['f5'][3])

            if self.ui.scan_Filter6.isChecked():

                self.ui.scan_startNM_6.setValue(measurement_parameters['f6'][0])
                self.ui.scan_stopNM_6.setValue(measurement_parameters['f6'][1])
                self.ui.scan_stepNM_6.setValue(measurement_parameters['f6'][2])
                self.ui.scan_pickAmp_6.setValue(measurement_parameters['f6'][3])
                
        except Exception as err:
            self.logger.exception("Unexpected error during execution of load_mono_parameter function:")
        
        
    # General function to create scanning list
        
    def createScanJob(self, start, stop, step):
        """Function to compile scan parameters.
        
        Parameters
        ----------
        start: float, required
            Wavelength start value
        stop: float, required
            Wavelength stop value
        step: float, required
            Wavelength step value
            
        Returns
        -------
        List
            List of integer wavelength values

        """
        scan_list = []       
        number = int((stop-start)/step)
        
        for n in range(-1, number + 1): 
        # -1 to start from before the beginning, +1 to include the last iteration of 'number', [and +2 to go above stop (this can
        # be changed later])
            wavelength = start + n*step
            scan_list.append(wavelength)
            
        return scan_list
           
# -----------------------------------------------------------------------------------------------------------        
    
    #### Functions to handle measurement

# -----------------------------------------------------------------------------------------------------------       
        
    # Measure LOCKIN response    
     
    def HandleMeasurement(self, scan_list, start, stop, step, amp, number):  
        """Function to prepare sample measurement.
        
        Parameters
        ----------
        scan_list: list of ints, required
            List of wavelength values to scan
        start: float, required
            Wavelength start value
        stop: float, required
            Wavelength stop value
        step: float, required
            Wavelength step value
        amp: float, required
            Pre-amplifier amplification value
        number: int, required
            Specifier to decide if power value is calculated (1) or not (0)

        Returns
        -------
        None
        
        """      
        if self.mono_connected and self.lockin_connected and self.filter_connected:   
            # Assign user, expriment and file name for current measurement
            userName = self.ui.user.text()
            experimentName = self.ui.experiment.text()
            
            start_no = str(int(start))
            stop_no = str(int(stop))
            step_no = str(int(step))
            amp_no = str(int(amp))
            if number == 1:
#                name = 'Si_ref_diode'
                name = self.ui.file.text()  
            if number == 2:
#                name = 'InGaAs_ref_diode'
                name = self.ui.file.text()  
            if number == 3:
                name = self.ui.file.text()

            if not self.complete_scan: # If not a complete scan is taken
                fileName = name + '_(' + start_no + '-' + stop_no + 'nm_' + step_no + 'nm_' + amp_no + 'x)'
            elif self.complete_scan:
                fileName = name + '_' + self.filter_addition + 'Filter' + '_(' + start_no + '-' + stop_no + 'nm_' + step_no + 'nm_' + amp_no + 'x)' 
        
            #Set up path to save data
            self.path =f'{self.save_path}/{userName}/{experimentName}'
            self.logger.info(f'Saving data to: {self.path}')
            if not os.path.exists(self.path):
                os.makedirs(self.path)
            else:
                pass       
            self.naming(fileName, self.path, 2)  # This function defines a variable called self.file_name
            
            self.measure(scan_list, number)
            
            
         
         
    def measure(self, scan_list, number):     
        """Function to perform sample measurement.
        
        Parameters
        ----------
        scan_list: list of ints, required
            List of wavelength values to scan
        number: int, required
            Specifier to decide if power value is calculated (1) or not (0)

        Returns
        -------
        None

        """
#        columns = ['Wavelength', 'Mean Current', 'Amplification', 'Mean R', 'Log Mean R', 'Mean RMS', 'Mean X', 'Mean Y', 'Mean Frequency', 'Mean Phase']
        columns = ['Wavelength', 'Mean Current', 'Amplification', 'Mean R', 'Mean Frequency', 'Mean Phase']    
        
        self.measuring = True 
        self.ui.imageCompleteScan_stop.setPixmap(QtGui.QPixmap("Button_off.png"))
        
        # Set up plot style                
        if self.do_plot:
#            plt.close()
            self.set_up_plot()
            
        time.sleep(1)

    # Set up empty lists for measurements
        plot_list_x = []
        plot_list_y = []
        plot_log_list_y = []
        plot_list_phase = []
        data_list = []
        data_df = pd.DataFrame(data_list, columns = columns) 
                    
        # Subscribe to scope
        self.path0 = '/' + self.device + '/demods/', self.c,'/sample'
        self.daq.subscribe(self.path0) 
        
        count = 0
        
#        self.chooseFilter(2)


        while len(scan_list)>0:            
            if self.measuring:                
                wavelength = scan_list[0]

                self.monoCheckFilter(wavelength)
                self.monoCheckGrating(wavelength)
                
                self.mono.chooseWavelength(wavelength)
                
                # Poll data for 5 time constants, second parameter is poll timeout in [ms] (recomended value is 500ms) 
                dataDict = self.daq.poll(5*self.tc,500)  # Dictionary with ['timestamp']['x']['y']['frequency']['phase']['dio']['trigger']['auxin0']['auxin1']['time']
#                print(dataDict[self.device]['demods'][self.c]['sample']['timestamp'])
                
            
                # Recreate data
                if self.device in dataDict:
                    if dataDict[self.device]['demods'][self.c]['sample']['time']['dataloss']:
                        self.logger.info('Sample Loss Detected')
                    else:
                        if count>0: # Cut off the first measurement before the start to cut off the initial spike in the spectrum                         
#                           if self.imp50==0:     #### FIX THIS TO HANDLE IMP 50
#                                e = amp_coeff*amplitude/sqrt(2)
#                           elif self.imp50==1:  # If 50 Ohm impedance is enabled, the signal is cut in half
#                                e = 0.5*amp_coeff*amplitude/sqrt(2) 
                            
                            data = dataDict[self.device]['demods'][self.c]['sample']
                            rdata = sqrt(data['x']**2+data['y']**2)
                            rms = sqrt(0.5*(data['x']**2+data['y']**2))
                            current = rdata/self.amplification
                            
                            mean_curr = mean(current)
                            mean_r = mean(rdata)
                            log_mean_r = log(mean_r)
                            mean_rms = mean(rms)
                            mean_x = mean(data['x'])
                            mean_y = mean(data['y'])
                            mean_freq = mean(data['frequency'])
                            mean_phase = mean(data['phase'])
                                                                                         
                            
#                            scanValues = [wavelength, mean_curr, self.amplification, mean_r, log_mean_r, mean_rms, mean_x, mean_y, mean_freq, mean_phase]
                            scanValues = [wavelength, mean_curr, self.amplification, mean_r, mean_freq, mean_phase]
                           
                            plot_list_x.append(wavelength)
                            plot_list_y.append(mean_r)
                            plot_log_list_y.append(log_mean_r)
                            plot_list_phase.append(mean_phase)
        
                            data_list.append(scanValues)
                            
                            data_df = pd.DataFrame(data_list, columns = columns)
                            
                            if number == 1:
                                self.calculatePower(data_df, self.Si_cal)
                            elif number == 2:
                                self.calculatePower(data_df, self.InGaAs_cal)
                            else: #### CHECK THAT THIS WORKS!!!
                                pass
                            
                            data_file = data_df.to_csv(os.path.join(self.path, self.file_name))
                            
                            
                            if self.do_plot:
                                self.ax1.plot(plot_list_x, plot_list_y, color = '#000000')
                                self.ax2.plot(plot_list_x, plot_log_list_y, color = '#000000')
                                self.ax3.plot(plot_list_x, plot_list_phase, color = '#000000')
                                self.pause(0.1)
                                
                del scan_list[0]
                count+=1  
                
            else:
                self.ui.imageCompleteScan_stop.setPixmap(QtGui.QPixmap("Button_on.png"))
                break
        

        # Unsubscribe to scope 
        self.daq.unsubscribe(self.path0)
# -----------------------------------------------------------------------------------------------------------   

    # Function to calculate the reference power

    def calculatePower(self, ref_df, cal_df):
        """Function to calculate power.
        
        Parameters
        ----------
        ref_df: DataFrame, required
            DataFrame of reference measurements
        cal_df: DataFrame, required
            DataFrame of reference calibration measurements
        
        Returns
        -------
        DataFrame
            DataFrame of reference diode measurements incl. power

        """        
        cal_wave_dict = {} # Create an empty dictionary
        power = [] # Create an empty list
            
        for x in range(len(cal_df['Wavelength [nm]'])): # Iterate through columns of calibration file
            cal_wave_dict[cal_df['Wavelength [nm]'][x]] = cal_df['Responsivity [A/W]'][x] # Add wavelength and corresponding responsivity to dictionary


        for y in range(len(ref_df['Wavelength'])): # Iterate through columns of reference file
#            print(ref_df['Wavelength'][y])
            if ref_df['Wavelength'][y] in cal_wave_dict.keys(): # Check if reference wavelength is in calibraton file
                power.append(float(ref_df['Mean Current'][y]) / float(cal_wave_dict[ref_df['Wavelength'][y]])) # Add power to the list
            else: # If reference wavelength is not in calibration file
                resp_int = self.interpolate(ref_df['Wavelength'][y], cal_df['Wavelength [nm]'], cal_df['Responsivity [A/W]']) # Interpolate responsivity
                power.append(float(ref_df['Mean Current'][y]) / float(resp_int)) # Add power to the list                
                
        ref_df['Power'] = power # Create new column in reference file
        
        return ref_df['Power']        
    
    # Function to interpolate values    
        
    def interpolate(self, num, x, y):     
        f = interp1d(x, y)
        return f(num)
        
# -----------------------------------------------------------------------------------------------------------   
            
    def set_up_plot(self): 
        """Function to set up plot.
        
        Returns
        -------
        None

        """
        style.use('ggplot')
        fig1 = plt.figure()
                    
        self.ax1 = fig1.add_subplot(3,1,1)
#        plt.xlabel('Time (s)', fontsize=17, fontweight='medium')
        plt.ylabel('R component (V)', fontsize=17, fontweight='medium')              
        plt.grid(True)
#        plt.box()
        plt.title('Demodulator data', fontsize=17, fontweight='medium')
        plt.tick_params(labelsize=14)
        plt.minorticks_on()
        plt.rcParams['figure.facecolor']='white'
        plt.rcParams['figure.edgecolor']='white'
        plt.tick_params(labelsize=15, direction='in', axis='both', which='major', length=8, width=2)
        plt.tick_params(labelsize=15, direction='in', axis='both', which='minor', length=4, width=2)

        self.ax2 = fig1.add_subplot(3,1,2)
#        plt.xlabel('Time (s)', fontsize=17, fontweight='medium')
        plt.ylabel('Log(R)', fontsize=17, fontweight='medium')              
        plt.grid(True)
#        plt.box()
        plt.tick_params(labelsize=14)
        plt.minorticks_on()
        plt.rcParams['figure.facecolor']='white'
        plt.rcParams['figure.edgecolor']='white'
        plt.tick_params(labelsize=15, direction='in', axis='both', which='major', length=8, width=2)
        plt.tick_params(labelsize=15, direction='in', axis='both', which='minor', length=4, width=2)
        
        self.ax3 = fig1.add_subplot(3,1,3)
        plt.xlabel('Wavelength [nm]', fontsize=17, fontweight='medium')
        plt.ylabel('Phase', fontsize=17, fontweight='medium') 
        plt.grid(True)
#        plt.box()
#        plt.title('Demodulator data', fontsize=17, fontweight='medium')
        plt.tick_params(labelsize=14)
        plt.minorticks_on()
        plt.rcParams['figure.facecolor']='white'
        plt.rcParams['figure.edgecolor']='white'
        plt.tick_params(labelsize=15, direction='in', axis='both', which='major', length=8, width=2)
        plt.tick_params(labelsize=15, direction='in', axis='both', which='minor', length=4, width=2)
        
        plt.show()
        
        return fig1

    def pause(self,interval):
        """Function to pause matplotlib without plt.show()
        
        Parameters
        ----------
        interval: int, required
            Pause time
            
        Returns
        -------
        None
        
        Notes
        -----
        This is a reimplementation of the matplotlib pause function, removing the final show() call.
        It prevents the matplotlib plot window to pop up after each measurement.
        
        The matplotlib 3.6 docstring says: 
        
        "Run the GUI event loop for *interval* seconds.
        If there is an active figure, it will be updated and displayed before the
        pause, and the GUI event loop (if any) will run during the pause.
        This can be used for crude animation.  For more complex animation use
        :mod:`matplotlib.animation`.
        If there is no active figure, sleep for *interval* seconds instead.
        
        See Also
        --------
        matplotlib.animation : Proper animations
        show : Show all figures and optional block until all figures are closed."
        
        """
        manager = matplotlib._pylab_helpers.Gcf.get_active()
        if manager is not None:
            canvas = manager.canvas
            if canvas.figure.stale:
                canvas.draw_idle()
            #show(block=False)
            canvas.start_event_loop(interval)
        else:
            time.sleep(interval)

# -----------------------------------------------------------------------------------------------------------   
        
    def naming(self, file_name, path_name, num):
        """Function to compile filename.
        
        Parameters
        ----------
        file_name: str, required
            File name
        path_name: str, required
            Path name
        num: str, required
            Filter number
        
        Returns
        -------
        None

        """        
        name = os.path.join(path_name, file_name)
        exists = os.path.exists(name)
        
        if exists:
            if num ==2:
                filename = file_name + '_%d' % num
            else:
                filename = file_name[:-1] + str(num)
            num += 1
            self.naming(filename, path_name, num)
        else:
            self.file_name = file_name

# -----------------------------------------------------------------------------------------------------------   

    def HandleStopCompleteScanButton(self):
        """Function to stop multi-filter measurement.
        
        Returns
        -------
        None

        """
        self.measuring = False
        self.ui.imageCompleteScan_stop.setPixmap(QtGui.QPixmap("Button_on.png"))
        return self.measuring

# -----------------------------------------------------------------------------------------------------------

    def get_logger(self):
        """Function to set up logger.
        
        Returns
        -------
        logger
        
        """
        logger = logging.getLogger()
        logger.setLevel(logging.DEBUG)
        formatter = logging.Formatter(fmt="%(asctime)s %(levelname)s %(name)s: %(message)s",
                                      datefmt="%Y-%m-%d - %H:%M:%S")
        console = logging.StreamHandler(sys.stdout)
        console.setLevel(logging.DEBUG)
        console.setFormatter(formatter)
    
#        logfile = logging.FileHandler('run.log', 'w')
#        logfile.setLevel(logging.DEBUG)
#        logfile.setFormatter(formatter)
    
        logger.addHandler(console)
#        logger.addHandler(logfile)
    
        return logger

# -----------------------------------------------------------------------------------------------------------
        
def main():

    try:
        app = QtWidgets.QApplication(sys.argv)
        monoUI = MainWindow()
        monoUI.show()
        sys.exit(app.exec_())
        
    except Exception as error:
        logging.exception("Unexpected error during main function: ")

if __name__ == "__main__": 
    main()
  

