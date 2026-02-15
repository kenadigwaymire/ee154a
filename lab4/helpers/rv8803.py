import qwiic_rv8803
import sys
import time

class RV8803:
    """
    PURPOSE: Real time clock 
    ERROR HANDLING: wiener
    """
    
    def __init__(self, address=0x32)