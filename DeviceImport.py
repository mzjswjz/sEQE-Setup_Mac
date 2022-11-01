#!/usr/bin/env python
# coding: utf-8

# In[11]:


import platform

import os 
import pathlib


# In[61]:


class DummyClass():
    def __init__(self):
        file = pathlib.Path('pathsNports.txt')
        if file.exists():
            pNpdata = file.read_text().split(',')
            print(pNpdata)
            self.filter_usb = pNpdata[0]
            self.mono_usb =  pNpdata[1]
            self.save_path = pNpdata[2]
            print(f'{self.filter_usb},{self.mono_usb},{self.save_path}')
            #file.unlink()            
        else:
            file.touch(exist_ok = False)
            
             # Path to USB connections NOTE: Change these if necessary - this will be improved à la Grey
            if platform.system() == 'Linux':
                port_prefix = '/dev/ttyUSB'
            elif platform.system() == 'Windows':
                port_prefix = 'COM'
            else:
                self.logger.error('Operating System is not known - defaulting to Linux system')
                port_prefix = '/dev/tty'
            
            self.filter_usb = port_prefix+str(input('Which port number is used by the second filter wheel ? - type a number'))#'COM4'
            self.mono_usb =  port_prefix+str(input('Which port number is used by the monochromator ? - type a number'))#'COM1'
            self.save_path = pathlib.Path(input('Where do you want to save your data ? - copy absolute path of folder'))#'C:\\Users\\Public\\Documents\\sEQE'                
                
#                 self.filter_usb = '/dev/ttyUSB0'
#                 self.mono_usb = '/dev/ttyUSB1' 
#                 self.save_path = '/home/jungbluthl/Desktop/sEQE Data'
           
                # self.filter_usb = str(input('Which port is used by the second filter wheel ? - type COMx with x being a number'))#'COM4'
                # self.mono_usb =  str(input('Which port is used by the monochromator ? - type COMx with x being a number'))#'COM1'
                # #self.save_path = 'C:\\Users\\hanauske\\Desktop\\sEQE-Data'
                # self.save_path = pathlib.Path(input('Where do you want to save your data ? - copy absolute path of folder'))#'C:\\Users\\Public\\Documents\\sEQE'
                
            file.write_text(f'{self.filter_usb},{self.mono_usb},{self.save_path}')
            print(file.read_text())


# In[60]:


x = DummyClass()


# In[22]:


path = os.getcwd()
p = pathlib.Path(path)
print(p)
for child in p.iterdir():
    print(child)

c = pathlib.Path('sEQE-Data').exists()
print(c)


# In[ ]:


windwospath = pathlib.Path('C:\\Users\\Public\\Documents\\sEQE')

