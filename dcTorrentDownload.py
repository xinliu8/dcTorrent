# Written by Bram Cohen
# see LICENSE.txt for license information

from BitTornado import PSYCO
if PSYCO.psyco:
    try:
        import psyco
        assert psyco.__version__ >= 0x010100f0
        psyco.full()
    except:
        pass
    
from BitTornado.download_bt1 import BT1Download, defaults, parse_params, get_usage, get_response
from BitTornado.RawServer import RawServer, UPnP_ERROR
from random import seed
from socket import error as socketerror
from BitTornado.bencode import bencode
from BitTornado.natpunch import UPnP_test
from threading import Event, Timer
from os.path import abspath
import sys
from sha import sha
from time import strftime, gmtime, time
from BitTornado.clock import clock
from BitTornado import createPeerID, version
from BitTornado.ConfigDir import ConfigDir
from dcTorrentDefaults import adjustDownloader

assert sys.version >= '2', "Install Python 2.0 or greater"
try:
    True
except:
    True = 1
    False = 0

PROFILER = False

def hours(n):
    if n == 0:
        return 'complete!'
    try:
        n = int(n)
        assert n >= 0 and n < 5184000  # 60 days
    except:
        return '<unknown>'
    m, s = divmod(n, 60)
    h, m = divmod(m, 60)
    if h > 0:
        return '%d hour %02d min %02d sec' % (h, m, s)
    else:
        return '%d min %02d sec' % (m, s)

def isotime(secs = None):
    if secs == None:
        secs = time()
    return strftime('%Y-%m-%d %H:%M UTC', gmtime(secs))

class HeadlessDownloader:
    def __init__(self):
        self.done = False
        self.file = ''
        self.percentDone = ''
        self.timeEst = ''
        self.downloadTo = ''
        self.downRate = ''
        self.upRate = ''
        self.shareRating = ''
        self.seedStatus = ''
        self.peerStatus = ''
        self.errors = []
        self.last_update_time = -1
        self.doneflag = Event()
        self.isDownloader = False
        self.torrent = ''
        self.logfile = None
        
    def log(self, stuff):
        if self.logfile == None:
            print stuff
        else:
            self.logfile.write(stuff + '\n')
            self.logfile.flush()

    def shutdown(self):
        self.doneflag.set()

    def finished(self):
        self.done = True
        self.percentDone = '100'
        self.timeEst = 'Download Succeeded!'
        self.downRate = ''
        self.display()
        if self.isDownloader == True:
            t = Timer(30.0, self.shutdown)
            t.start()

    def failed(self):
        self.done = True
        self.percentDone = '0'
        self.timeEst = 'Download Failed!'
        self.downRate = ''
        self.display()
        self.doneflag.set()

    def error(self, errormsg):
        self.errors.append(errormsg)
        self.display()
        self.doneflag.set()

    def displaySlim(self, dpflag = Event(), fractionDone = None, timeEst = None, 
            downRate = None, upRate = None, activity = None,
            statistics = None,  **kws):

        dpflag.set()

    def display(self, dpflag = Event(), fractionDone = None, timeEst = None, 
            downRate = None, upRate = None, activity = None,
            statistics = None,  **kws):
        if self.last_update_time + 0.1 > clock() and fractionDone not in (0.0, 1.0) and activity is not None:
            return
        self.last_update_time = clock()        
        if fractionDone is not None:
            self.percentDone = str(float(int(fractionDone * 1000)) / 10)
        if timeEst is not None:
            self.timeEst = hours(timeEst)
        if activity is not None and not self.done:
            self.timeEst = activity
        if downRate is not None:
            self.downRate = '%.1f kB/s' % (float(downRate) / (1 << 10))
        if upRate is not None:
            self.upRate = '%.1f kB/s' % (float(upRate) / (1 << 10))
        if statistics is not None:
           if (statistics.shareRating < 0) or (statistics.shareRating > 100):
               self.shareRating = 'oo  (%.1f MB up / %.1f MB down)' % (float(statistics.upTotal) / (1<<20), float(statistics.downTotal) / (1<<20))
           else:
               self.shareRating = '%.3f  (%.1f MB up / %.1f MB down)' % (statistics.shareRating, float(statistics.upTotal) / (1<<20), float(statistics.downTotal) / (1<<20))
           if not self.done:
              self.seedStatus = '%d seen now, plus %.3f distributed copies' % (statistics.numSeeds,0.001*int(1000*statistics.numCopies))
           else:
              self.seedStatus = '%d seen recently, plus %.3f distributed copies' % (statistics.numOldSeeds,0.001*int(1000*statistics.numCopies))
           self.peerStatus = '%d seen now, %.1f%% done at %.1f kB/s' % (statistics.numPeers,statistics.percentDone,float(statistics.torrentRate) / (1 << 10))
        self.log( '\n\n\n\n')
        for err in self.errors:
            self.log( 'ERROR:\n' + err + '\n')
        self.log( 'saving:        '+ self.file)
        self.log( 'percent done:  '+ self.percentDone)
        self.log( 'time left:     '+ self.timeEst)
        self.log( 'download to:   '+ self.downloadTo)
        self.log( 'download rate: '+ self.downRate)
        self.log( 'upload rate:   '+ self.upRate)
        self.log( 'share rating:  '+ self.shareRating)
        self.log( 'seed status:   '+ self.seedStatus)
        self.log( 'peer status:   '+ self.peerStatus)
        
        dpflag.set()        

    def chooseFile(self, default, size, saveas, dir):
        self.file = '%s (%.1f MB)' % (default, float(size) / (1 << 20))
        if saveas != '':
            default = saveas
        self.downloadTo = abspath(default)
        return default

    def newpath(self, path):
        self.downloadTo = path

    def download(self, params):
        role = params[0]
        if role == 'download':
            self.isDownloader = True

        #try:
        #    logname = 'download' if self.isDownloader else 'seed'
        #    self.log = open('C:\\Logs\\{0}.log'.format(logname),'a')
        #    self.log.write( "# Log Started: " + isotime())
        #except:
        #    print "warning: could not open log file: "

        params.remove(role)

        while True:
            configdir = ConfigDir('downloadheadless')
            defaultsToIgnore = ['responsefile', 'url', 'priority']
            configdir.setDefaults(defaults,defaultsToIgnore)
            configdefaults = configdir.loadConfig()
            defaults.append(('save_options',0,
             "whether to save the current options as the new default configuration " +
             "(only for btdownloadheadless.py)"))
            try:
                config = parse_params(params, configdefaults)
            except ValueError, e:
                print 'error: ' + str(e) + '\nrun with no args for parameter explanations'
                break
            if not config:
                print get_usage(defaults, 80, configdefaults)
                break
            if config['save_options']:
                configdir.saveConfig(config)
            configdir.deleteOldCacheData(config['expire_cache_data'])
            
            if config['url']:
                self.torrent = config['url']
            elif config['responsefile']:
                self.torrent = config['responsefile']

            if (config['logfile']) and (config['logfile'] != '-'):
                try:
                    self.logfile = open(config['logfile'],'a')
                    self.log( "# Log Started: " + isotime())
                except:
                    print "warning: could not open log file."

            for k in adjustDownloader:
                config[k] = adjustDownloader[k]

            myid = createPeerID()
            seed(myid)
        
            def disp_exception(text):
                self.log( text)
            rawserver = RawServer(self.doneflag, config['timeout_check_interval'],
                                  config['timeout'], ipv6_enable = config['ipv6_enabled'],
                                  failfunc = self.failed, errorfunc = disp_exception)
            upnp_type = UPnP_test(config['upnp_nat_access'])

            while True:
                try:
                    listen_port = rawserver.find_and_bind(config['minport'], config['maxport'],
                                    config['bind'], ipv6_socket_style = config['ipv6_binds_v4'],
                                    upnp = upnp_type, randomizer = config['random_port'])
                    break
                except socketerror, e:
                    if upnp_type and e == UPnP_ERROR:
                        self.log( 'WARNING: COULD NOT FORWARD VIA UPnP')
                        upnp_type = 0
                        continue
                    self.log( "error: Couldn't listen - " + str(e))
                    self.failed()
                    return "error: Couldn't listen - " + str(e)

            response = get_response(config['responsefile'], config['url'], self.error)
            if not response:
                break

            infohash = sha(bencode(response['info'])).digest()
            # seeder log doesn't need to be detailed
            statusfunc = self.display if self.isDownloader else self.displaySlim
            dow = BT1Download(statusfunc, self.finished, self.error, disp_exception, self.doneflag,
                            config, response, infohash, myid, rawserver, listen_port,
                            configdir)
        
            if not dow.saveAs(self.chooseFile, self.newpath):
                break

            if not dow.initFiles(old_style = True):
                break
            if not dow.startEngine():
                dow.shutdown()
                break
            dow.startRerequester()
            dow.autoStats()

            if not dow.am_I_finished():
                self.display(activity = 'connecting to peers')
            rawserver.listen_forever(dow.getPortHandler())
            self.display(activity = 'shutting down')
            dow.shutdown()
            break
        try:
            rawserver.shutdown()
        except:
            pass
        if not self.done:
            self.failed()

        return

if __name__ == '__main__':
    
    h = HeadlessDownloader()
    h.download(sys.argv[1:])
