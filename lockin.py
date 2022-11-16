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

import serial
import zhinst.utils
import zhinst.ziPython
 
import pandas as pd
import serial

import codecs




class LockIn():
    
    def __init__(self,device):
        
        self.zurich_device = device
        self.connected = False
    
    def connectToLockin(self):    
        """Function to establish connection to Lockin.
        
        Returns
        -------
        list
            Zurich Instruments localhost name and device details
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

        self.logger.info('Connection to Lock-In Established')
        
        self.connected = True       
        self.ui.imageConnect_lockin.setPixmap(QtGui.QPixmap("Button_on.png"))
        
        return self.daq, self.device