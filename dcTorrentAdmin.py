import logging
import dcTorrentLogging

import pstats

from BitTornado.BT1.track import TrackerServer
from BitTornado.BT1.makemetafile import make_meta_file, defaults
from BitTornado.parseargs import parseargs
from dcTorrentDownload import HeadlessDownloader
from dcTorrentDefaults import defaultDirs, defaultSettings
from twisted.web.resource import Resource
from twisted.internet import reactor, threads
from twisted.internet import protocol
from twisted.web.server import Site
from twisted.web.static import File

from urlparse import urlparse
import os
from time import time, gmtime, strftime
import shutil
import sys
from multiprocessing import Lock

def getDownloaderId(action, target):
    return action + ':' + target

class MyPP(protocol.ProcessProtocol):
    def __init__(self, name):
        self.data = ""
        self.name = name
        self.logger = logging.getLogger('{0}'.format(self.__class__.__name__))

    def connectionMade(self):
        self.transport.closeStdin()
    def outReceived(self, data):
        self.data = self.data + data
    def errReceived(self, data):
        self.logger.error( 'Error: {0}'.format(data))
    def inConnectionLost(self):
        pass
    def outConnectionLost(self):
        self.logger.debug(  'stdout lost: {0}'.format(self.data))
    def errConnectionLost(self):
        self.logger.debug(  'stderr lost.')
    def processExited(self, reason):
        import sys
        global processes
        processes.remove(self.name)
        #action = self.name.split(':')[0]
        #profile = defaultDirs['profile']+'{0}.profile'.format(action)
        #stats = defaultDirs['profile']+'{0}.stats'.format(action)
        #if os.path.exists(profile):
        #    p = pstats.Stats(profile)
        #    statslog = open(stats,'a')
        #    normalstdout = sys.stdout
        #    sys.stdout = statslog
        #    p.strip_dirs().sort_stats('time').print_stats()
        #    sys.stdout = normalstdout

        if reason.value.exitCode != 0:
            self.logger.error(  "Process {0} exited with status {1}".format(self.name, reason.value.exitCode))
        else :
            self.logger.info(  "Process {0} exited.".format(self.name))
    def processEnded(self, reason):
        if reason.value.exitCode != 0:
            self.logger.error(  "Process {0} ended with status {1}".format(self.name, reason.value.exitCode))
        else :
            self.logger.info(  "Process {0} ended.".format(self.name))

def removeDownloader(result):
    global downloaders
    if downloaders.has_key(result):
        del downloaders[result]

# this runs in tracker's thread
def trackerAnnouceCallback(infohash, ip):
    statfile = open(defaultDirs['log'] + 'stat.log', 'a')
    timestr = strftime('%Y-%m-%d %H:%M:%S UTC', gmtime(time()))
    readableInfohash = ''.join( [ "%02X" % ord( x ) for x in infohash ] )
    statfile.writelines('{0} finish downloading {1} at {2}\n'.format(ip, readableInfohash, timestr))
    statfile.flush()

class ProcessManager():
    def __init__(self):
        self.lock = Lock()
        self.processes = dict()
    def has(self, name):
        self.lock.acquire()
        isExists = True if self.processes.has_key(name) else False
        self.lock.release()
        return isExists
    def add(self, name, process):
        self.lock.acquire()
        self.processes[name] = process
        self.lock.release()
    def remove(self, name):
        self.lock.acquire()
        if self.processes.has_key(name):
            del self.processes[name]
        self.lock.release()
    def kill(self, name):
        self.lock.acquire()
        if self.processes.has_key(name):
            self.processes[name].signalProcess('KILL')
            del self.processes[name]
        self.lock.release()

class DcTorrentAdmin(Resource):
    
    def render_GET(self, request):
        global trackerPort, downloaders, processes, logger
        
        logger.info(request.uri)

        verb = request.args['action'][0]
        if verb=='track':
            if processes.has('track'):
                return 'Tracker is already up on {0}'.format(trackerPort)

            port = request.args['port'][0]
            params = ['--port', port, '--dfile', 'dstate']
            pp = MyPP('track')
            program = [defaultDirs['python'] + "python.exe", "dcTorrent.py", "start", "track"]
            args = program + params
            trackerProcess = reactor.spawnProcess(pp, args[0], args, env = os.environ)
            processes.add('track', trackerProcess)
            trackerPort = port
            #d = threads.deferToThread(tracker.track, params)
            # clear the "done" event for the next start
            #d.addCallback(lambda x: tracker.init())
            return 'Tracker is listening on {0}.'.format(port)
        elif verb=='seed' or verb=='download':
            torrent = request.args['torrent'][0]
            downloaderId = getDownloaderId(verb, torrent)
            # disallow multiple downloaders on one machine
            #if processes.has(downloaderId):
            #    return 'Downloader is already up'.format(downloaderId)

            parts = urlparse(torrent)
            components = os.path.normpath(parts.path).split(os.sep)
            torrentName = components[len(components)-1]
            filename = torrentName[:torrentName.find('.torrent')]
            #params = [verb, '--url', torrent, '--saveas', defaultDirs[verb] + filename, '--ip', request.host.host, '--logfile', '{0}{1}.log'.format(defaultDirs['log'], verb)]
            params = [verb, '--url', torrent, '--saveas', defaultDirs[verb] + filename, '--ip', request.host.host]
            #if verb == 'seed':
            #    params += ['--super_seeder', '1']
            program = [defaultDirs['python'] + "python.exe", "dcTorrent.py", "start"]
            args = program + params
            pp = MyPP(downloaderId)
            downloadProcess = reactor.spawnProcess(pp, args[0], args, env = os.environ)
            processes.add(downloaderId, downloadProcess)
            #h = HeadlessDownloader(removeDownloader)
            #downloaders[torrent] = h
            #d = threads.deferToThread(h.download, params)
            #d.addCallback(h.downloadCallback)
            return '{0} is up.'.format(downloaderId)
        elif verb=='maketorrent':
            if trackerPort==0:
                return 'Tracker is not started yet.'

            source = request.args['source'][0]
            filename = defaultDirs['seed'] + source
            target = defaultDirs['torrent'] + source + '.torrent'
            trackerUri = 'http://{0}:{1}/announce'.format(request.host.host, str(trackerPort))
            params = [trackerUri, filename, '--target', target]
            
            try:
                config, args = parseargs(params, defaults, 2, None)
                for file in args[1:]:
                    make_meta_file(file, args[0], config)
            except ValueError, e:
                return 'error: ' + str(e)
            return 'Make torrent for {0}'.format(source)
        elif verb=='stop':
            role = request.args['role'][0]
            # set the "done" event, but the role thread will stop sometime later
            if role=='track':
                #tracker.stop()
                processes.kill('track')
            elif role=='seed' or role=='download':
                torrent = request.args['torrent'][0]
                downloaderId = role + ':' + torrent
                processes.kill(downloaderId)
                #if downloaders.has_key(torrent):
                #    h = downloaders[torrent]
                #    h.shutdown()
            return '{0} is stopped.'.format(role)
        elif verb=='clean':
            try:
                if os.path.exists(defaultDirs['download']):
                    shutil.rmtree(defaultDirs['download'])
            except:
                logger.exception(str(sys.exc_info()[0]))
            return 'downloads are cleaned.'
        else:
            return 'Invalid parameter.'

class NotFound(Resource):
    def render_GET(self, request):
        return "Not Found";

class Dispatcher(Resource):
    def getChild(self, verb, request):
        if(verb=='admin'):
            return DcTorrentAdmin()
        elif(verb=='files'):
            return File(defaultDirs['torrent'])
        else:
            return NotFound()

tracker = TrackerServer(trackerAnnouceCallback)

if not os.path.exists(defaultDirs['log']):
    os.makedirs(defaultDirs['log'])

#adminlog = open(defaultDirs['log'] + 'admin.log', 'a')

downloaders = dict()

#logging.config.fileConfig('logging.conf')

dcTorrentLogging.setRootLogger(defaultDirs['log'] + 'admin.log', logging.DEBUG)
logger = logging.getLogger('admin')

processes = ProcessManager()
trackerPort = 0

root = Dispatcher()
factory = Site(root)
reactor.listenTCP(5678, factory)
reactor.run()

#start(int(sys.argv[1]))