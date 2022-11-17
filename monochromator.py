import time
import logging
import warnings
import codecs

import serial 

class Monochromator():
    """Implements Monochromator for Princeton Instruments HRS-300.
    
    Note: HRS-300 has manual filter wheel controls on the device. Users
    should periodically query the current monochromator filter wheel position.
    
    """ 
    
    def __init__(self,com):
        
        self.mono_usb = com
        self.connected = False        
    
    def connect(self):
        """Function to establish connection to monochromator. 
        
        Returns
        -------
        bool
            True if connection successful, False otherwise
            
        Raises
        ------
        LoggingError
            Raises Loggingerror for Exception handling
        
        """
        try:
            with serial.Serial(self.mono_usb, 9600, timeout=0) as self.p:

                self.p.write('HELLO\r'.encode())   # "Hello" initializes the Monochromator
                time.sleep(25)   # During initialization we want to avoid that the user sends signals
                self.connected = self.waitForOK()   # Checks for OK response of Monochromator

                return self.connected
            
        except Exception as err:
            logging.error(f"Unexpected {err=} during connect function, {type(err)=}")
            raise 
       
    
    # Check Monochromator response
    
    def waitForOK(self):
        """Function to wait for acceptance signal from monochromator.
        
        Returns
        -------
        bool 
            True if connection successful, False otherwise
        
        Raises
        ------
        LoggingError
            Raises error if monochromator connection failed or Exception handling
        
        """
        ret = False
        self.p.timeout = 40
        shouldbEOk = 'filler'
        
        try:
            while shouldbEOk != 'ok\r\n':
                shouldbEOk = self.p.readline()
                shouldbEOk = codecs.decode(shouldbEOk)
                print(shouldbEOk)
                #print ( shouldbEOk.endswith('ok\r\n') == True )
                if shouldbEOk.endswith('ok\r\n'):
                    ret = True
                    return ret
                else:
                    logging.info('Waiting for "ok" signal')
                    #print('Connection to Monochromator Could Not Be Established')
           
            self.p.timeout = 0
            return ret

            
        except Exception as error:
            logging.error(f"Unexpected {err=} during execution of waitForOk function, is ok still detected ? , {type(err)=}")
            print(error)
            

    def chooseWavelength(self, wavelength):   # Function to send GOTO command to monochromator
        """Function to send wavelength command to monochromator.
        
        Parameters
        ----------
        wavelength: float, required
            target wavelength
        
        Returns
        -------
        None
        
        Raises
        ------
        LoggerError
            Raises error if monochromator not connected or Exception handling

        """
        try:
            if self.connected:
                with serial.Serial(self.mono_usb, 9600, timeout=0) as self.p:
                    print('%d nm' % wavelength)
                    self.p.write('{:.2f} GOTO\r'.format(wavelength).encode())
                    self.waitForOK()

            else:
                logging.error('Monochromator Not Connected')
                
        except Exception as err:
            logging.error(f"Unexpected {err=} during execution of chooseWavelength function: {type(err)=}")
            raise
        
    def chooseScanSpeed(self, speed):
        """Function to send scan speed command to monochromator.
        
        Parameters
        ----------
        speed: float, required
            monochromator grating scan speed
            
        Returns
        -------
        None 
        
        Raises
        ------
        LoggerError
            Raises error if monochromator not connected or Exception handling

        """
        try:
            if self.connected:
                with serial.Serial(self.mono_usb, 9600, timeout=0) as self.p:
    #               logger.info('Updating Scan Speed to %d nm/min.' % speed)
                    self.p.write('{:.2f} NM/MIN\r'.format(speed).encode())
                    self.waitForOK()
            else:
                logging.error('Monochromator Not Connected')
                
        except Exception as err:
            logging.error(f"Unexpected {err=} during execution of chooseScanSpeed function: {type(err)=}")
            raise

    def chooseGrating(self, gratingNo):
        """Function to send grating command to monochromator.
        
        Parameters
        ----------
        gratingNo: float, required
            Monochromator grating number
            
        Returns
        -------
        None
        
        Raises
        -------
        LoggerError
            Raises error if monochromator not connected or Exception handling

        """
        try:
            if self.connected:
                if self.p.is_open:
                    logging.info('Moving to Grating %d' % gratingNo)
                    self.p.write('{:d} grating\r'.format(gratingNo).encode())
                    #print(self.p.readline())
                    self.waitForOK()
                else:
                    with serial.Serial(self.mono_usb, 9600, timeout=0) as self.p:
                        logging.info('Moving to Grating %d' % gratingNo)
                        self.p.write('{:d} grating\r'.format(gratingNo).encode())
                        #print(self.p.readline())
                        self.waitForOK()
            else:
                logging.error('Monochromator Not Connected')
                
        except Exception as err:
            logging.error(f"Unexpected {err=} during execution of chooseGrating function: {type(err)=}")
            raise

    def chooseFilter(self, filterNo):
        """Function to send filter selection command to filter wheel.
        
        Parameters
        ----------
        filterNo: float, required
            Filter position
            
        Returns
        -------
        None
        
        Raises
        ------
        LoggerError
            Raises error if monochromator not connected or Exception handling

        """
        try:
            if self.connected:

                if self.p.is_open:
                    logging.info('Moving to Monochromator Filter %d' % filterNo)
                    self.p.write('{:d} FILTER\r'.format(filterNo).encode())
                    #print(self.p.readline())
                    self.waitForOK()

                else: 
                    with serial.Serial(self.mono_usb, 9600, timeout=0) as self.p:
                            logging.info('Moving to Monochromator Filter %d' % filterNo)
                            self.p.write('{:d} FILTER\r'.format(filterNo).encode())
                            #print(self.p.readline())
                            self.waitForOK()

            else:
                logging.error('Monochromator Not Connected')
                
        except Exception as err:
            logging.error(f"Unexpected {err=} during execution of chooseFilter function: {type(err)=}")
            raise
            
    def initializeFilter(self, filterDiff):
        """Function to initialize filter wheel.
        
        Parameters
        ----------
        filterDiff: int, required
            Difference between filter position and initialization position

        Returns
        -------
        None
        
        Raises
        ------
        LoggerError:
            Raises error if monochromator not connected or Exception handling

        """
        try:
            if self.connected:
                with serial.Serial(self.mono_usb, 9600, timeout=0) as self.p:
                    logging.info('Initializing Monochromator Filter Wheel')
                    self.p.write('{:d} FILTER\r'.format(filterDiff).encode())
                    self.p.write('FHOME\r'.encode())
                    self.waitForOK()
            else:
                logging.error('Monochromator Not Connected')
        
        except Exception as err:
            logging.error(f"Unexpected {err=} during execution of initializeFilter function: {type(err)=}")
            raise

    def checkFilter(self,):   # Filter switching points from GUI
            """Function to read position of monochromators filter wheel.

            Returns
            -------
            int
                current monochromator's filter position

            Raises
            ------
            LoggerError
                Raises error if monochromator is not connected or Exception handling

            """
            try:
                if self.connected:
                    with serial.Serial(self.mono_usb, 9600, timeout=0) as self.p:
                        self.p.write('?filter\r'.encode())
                        self.p.timeout = 30000
                        response = self.p.readline() 
                        print(response)

                        if response.endswith('1  ok\r\n'.encode(errors='ignore')):
                            filterNo = 1
                        elif response.endswith('2  ok\r\n'.encode(errors='ignore')):
                            filterNo = 2 
                        elif response.endswith('3  ok\r\n'.encode(errors='ignore')):
                            filterNo = 3
                        elif response.endswith('4  ok\r\n'.encode(errors='ignore')):
                            filterNo = 4 
                        elif response.endswith('5  ok\r\n'.encode(errors='ignore')):
                            filterNo = 5
                        elif response.endswith('6  ok\r\n'.encode(errors='ignore')):
                            filterNo = 6
                        elif response.endswith('ok\r\n'.encode(errors='ignore')):
                            filterNo = 0
                        else:   # Do I need this?
                            logging.error('Error: Monchromator Filter Response')

                        return filterNo
                else:
                    logging.error('Monochromator Not Connected')
                    
            except Exception as err:
                logging.error(f"Unexpected {err=} during execution of checkFilter function: {type(err)=}")
                
    
    def checkGrating(self,):   # Grating switching points from GUI
        """Function to update monochromator grating position from GUI defaults.
        
        Parameters
        ----------
        wavelength: float, required
            Current wavelength position of monochromator

        Returns
        --------
        int
            Current grating position
        
        Raises
        ------
        LoggerError
            Raises error if  monochromator not connected or Exception handling

        """
        try:
            if self.connected:
                with serial.Serial(self.mono_usb, 9600, timeout=0) as self.p:
                    self.p.write('?grating\r'.encode())
                    self.p.timeout = 30000
                    response = self.p.readline()
                    print(response)

                    if response.endswith('1  ok\r\n'.encode()):
                        gratingNo = 1
                    elif response.endswith('2  ok\r\n'.encode()):
                        gratingNo = 2 
                    elif response.endswith('3  ok\r\n'.encode()):
                        gratingNo = 3
                    else:   # Do I need this?
                        logging.error('Error: Grating Response')
                        
                    return gratingNo
            else:
                logging.error('Monochromator Not Connected')
                
                
        except Exception as err:
            logging.error(f"Unexpected {err=} during execution of checkGrating function: {type(err)=}")
            raise