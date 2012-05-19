import win32service
import win32serviceutil
import win32api
import win32con
import win32event
import win32evtlogutil
import os, sys, string, time
from BitTornado.BT1.track import TrackerServer

class aservice(win32serviceutil.ServiceFramework):
    _svc_name_ = "MyServiceShortName"
    _svc_display_name_ = "My Serivce Long Fancy Name!"
    _svc_description_ = "THis is what my crazy little service does - aka a DESCRIPTION! WHoa!"
         
    def __init__(self, args):
        win32serviceutil.ServiceFramework.__init__(self, args)
        self.hWaitStop = win32event.CreateEvent(None, 0, 0, None)
        self.server = TrackerServer()           
        
    def SvcStop(self):
        self.ReportServiceStatus(win32service.SERVICE_STOP_PENDING)
        win32event.SetEvent(self.hWaitStop)
        self.server.stop()                    
         
    def SvcDoRun(self):
       import servicemanager      
       servicemanager.LogMsg(servicemanager.EVENTLOG_INFORMATION_TYPE,servicemanager.PYS_SERVICE_STARTED,(self._svc_name_, '')) 
      
       try:
           argv = ['--port', '6969', '--dfile', 'e:\\temp\\dstate', '--logfile', 'e:\\temp\\tracker.log'];
           self.server.track(argv)
       except:
           print "Unexpected error:", sys.exc_info()[0] 

def ctrlHandler(ctrlType):
    return True
                  
if __name__ == '__main__':   
    win32api.SetConsoleCtrlHandler(ctrlHandler, True)   
    win32serviceutil.HandleCommandLine(aservice)
