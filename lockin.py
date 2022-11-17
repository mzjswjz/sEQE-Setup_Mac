import io
import itertools
import math
import os
import re
import sys
import time
import logging
import warnings
import platform
import pathlib

import GUI_template
import serial
import zhinst.utils
import zhinst.ziPython
 
import pandas as pd
import serial

import codecs




class LockIn():
    
    def __init__(self,device):
        
        self.zurich_device = device
        
        self.channel = 1
        self.c = str(self.channel-1) 
        self.c6 = str(6)
        
        self.connected = False
    
    def connect(self):    
        """Function to establish connection to Lockin.
        
        Returns
        -------
        tuple
            Zurich Instruments localhost name, device details and True if device is connected
        """        
        # Find device via Device Discovery and open connection to ziServer 
        d = zhinst.ziPython.ziDiscovery()
        props = d.get(d.find(self.zurich_device))
        daq = zhinst.ziPython.ziDAQServer(props['serveraddress'],
                                          props['serverport'], 
                                          props['apilevel'])
        daq.connectDevice(self.zurich_device, 
                          props['interfaces'][0])
        
        self.daq = daq
        
        # Detect device
        self.device = zhinst.utils.autoDetect(daq)

        logging.info('Connection to Lock-In Established')
        
        self.connected = True       
        
        return self.daq, self.device, self.connected
    
    def setParameters(self,diff,imp50,imp50_2,ac,Range,lowpass,rate,tc,c_2,amplification):       
        """Function to set default Lockin parameters.
        
        Parameters
        ----------
        diff int, required
            Boolean representation to turn differentiale mode on and off: default: 1
            
        imp50 int, required
            Boolean representation to turn 50 Ohm impedance(?) on or off, default: 0
        
        imp50_2 int,required
            Boolean representation to turn on 50 Ohm on channel 2 to attenuate signal from chopper controller as reference signal, default: 1 
        
        ac int, required
            Boolean representation to turn AC voltage on or off, default: 0
            
        Range int, required
            Voltage range for measurement, default: 2V
        
        lowpass int, required
            low pass filter order
        
        rate int, required
            data transfer rate
        
        tc int, required
             time constant for measurement
        
        c_2 str, required
            Channel 2, with value 1, for the reference input
        
        amplification int, required
            Lock-in amplification of the signal
        
        
        Returns
        -------
        None
        
        Raises
        ------
        LoggingError
             Raises error for Exception handling
        
        """
        try:
            self.diff = diff
            self.imp50 = imp50
            self.imp50_2 = imp50_2
            self.ac = ac
            self.range = Range 
            self.lowpass = lowpass
            self.rate = rate 
            self.tc = tc
            self.c_2 = c_2
            self.amplification = amplification
            
            # Disable all outputs and all demods
            general_setting = [
                 [['/', self.device, '/demods/0/trigger'], 0],
                 [['/', self.device, '/demods/1/trigger'], 0],
                 [['/', self.device, '/demods/2/trigger'], 0],
                 [['/', self.device, '/demods/3/trigger'], 0],
                 [['/', self.device, '/demods/4/trigger'], 0],
                 [['/', self.device, '/demods/5/trigger'], 0],
                 [['/', self.device, '/sigouts/0/enables/*'], 0],
                 [['/', self.device, '/sigouts/1/enables/*'], 0]
            ]
            self.daq.set(general_setting)

            # Set test settings
            t1_sigOutIn_setting = [
                # Diff Button (Enable for differential mode to measure the difference between +In and -In.)
                [['/', self.device, '/sigins/',self.c,'/diff'], self.diff],  

                # 50 Ohm Button (Enable to switch input impedance between low (50 Ohm) and high (approx 1 MOhm). 
                [['/', self.device, '/sigins/',self.c,'/imp50'], self.imp50],   # Select for signal frequencies of > 10 MHz.)

                # AC Button (Enable for AC coupling to remove DC signal. Cutoff frequency = 1kHz) 
                [['/', self.device, '/sigins/',self.c,'/ac'], self.ac],  

                [['/', self.device, '/sigins/',self.c,'/range'], self.range],  # Input Range               
                [['/', self.device, '/demods/',self.c,'/order'], self.lowpass],  # Low-Pass Filter Order                        
                [['/', self.device, '/demods/',self.c,'/timeconstant'], self.tc],  # Time Constant
                [['/', self.device, '/demods/',self.c,'/rate'], self.rate],  # Data Transfer Rate 
                [['/', self.device, '/demods/',self.c,'/oscselect'], self.channel-1],  # Oscillators
                [['/', self.device, '/demods/',self.c,'/harmonic'], 1],  # Harmonicss
                [['/', self.device, '/demods/',self.c,'/phaseshift'], 0],  # Phase Shift       
                [['/', self.device, '/zctrls/',self.c,'/tamp/0/currentgain'], self.amplification],  #  Amplifier Setting
                [['/', self.device, '/demods/',self.c,'/adcselect'], self.channel-1], # ???

            # For locked reference signal
                # 50 Ohm Button (Enable to switch input impedance between low (50 Ohm) and high (approx 1 MOhm).
                # Select for signal frequencies of > 10 MHz.)
                [['/', self.device, '/sigins/', self.c_2,'/imp50'], self.imp50_2], 
                [['/', self.device, '/plls/',self.c,'/enable'], 1],  # Manual [0], External Reference [1]
                [['/', self.device, '/plls/',self.c,'/adcselect'], 1], # ???

            # For manual reference signal - The frequency tab is currently not implemented in the GUI
    #            [['/', self.device, '/plls/',self.c,'/enable'], 0],  # Manual [0], External Reference [1]
    #            [['/', self.device, '/oscs/',self.c,'/freq'], self.frequency],  # Demodulation Frequency

            # Additional settings ?                        
        #        [['/', self.device, '/sigouts/',self.c,'/add'], -179.8390],  # Output Add Button (Adds signal from "Add" connection)
        #        [['/', self.device, '/sigouts/',self.c,'/on'], 1],  # Turn on Output Channel
        #        [['/', self.device, '/sigouts/',self.c,'/enables/',c6], 1],  # Enable Output Channel
        #        [['/', self.device, '/sigouts/',self.c,'/range'], 1],  # Output Range
        #        [['/', self.device, '/sigouts/',self.c,'/amplitudes/',c6], amplitude],  # Output Amplitude
        #        [['/', self.device, '/sigouts/',self.c,'/offset'], 0],  # Output Offset

            ]
            self.daq.set(t1_sigOutIn_setting);       
            time.sleep(1)  # wait 1s to get a settled lowpass filter
            self.daq.flush()   # clean queue
        
        except Exception as err:
            logging.error(f"Unexpected {err=} during execution of setParameters function: {type(err)=}")
            raise