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
    statfile = open(os.path.join(defaultDirs['log'], 'stat.log'), 'a')
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
    def getDownloadId(self, action, target):
        return action + '$' + target

    def extractDownloadId(self, downloadId):
        separator = downloadId.find('$')
        return (downloadId[:separator], downloadId[separator+1:])

    def track(self, port):
        if processes.has('track'):
            return 'Tracker is already up on {0}'.format(trackerPort)

        params = ['--port', port, '--dfile', 'dstate']
        pp = MyPP('track')
        #program = [defaultDirs['python'] + "python.exe", "dcTorrent.py", "start", "track"]
        program = ["dcTorrent.exe", "start", "track"]
        args = program + params
        trackerProcess = reactor.spawnProcess(pp, args[0], args, env = os.environ)
        processes.add('track', trackerProcess)
        
        #d = threads.deferToThread(tracker.track, params)
        # clear the "done" event for the next start
        #d.addCallback(lambda x: tracker.init())

    def download(self, downloadId, host):
        
        # disallow multiple downloaders on one machine
        #if processes.has(downloadId):
        #    return 'Downloader is already up'.format(downloadId)
        (action, torrent) = self.extractDownloadId(downloadId)
        parts = urlparse(torrent)
        components = os.path.normpath(parts.path).split(os.sep)
        torrentName = components[len(components)-1]
        filename = torrentName[:torrentName.find('.torrent')]
        params = [action, '--url', torrent, '--saveas', os.path.join(defaultDirs[action], filename), '--ip', host]
        #if action == 'seed':
        #    params += ['--super_seeder', '1']
        #program = [defaultDirs['python'] + "python.exe", "dcTorrent.py", "start"]
        program = ["dcTorrent.exe", "start"]
        args = program + params
        pp = MyPP(downloadId)
        downloadProcess = reactor.spawnProcess(pp, args[0], args, env = os.environ)
        processes.add(downloadId, downloadProcess)
        #h = HeadlessDownloader(removeDownloader)
        #downloaders[torrent] = h
        #d = threads.deferToThread(h.download, params)
        #d.addCallback(h.downloadCallback)
    def download_many(self, downloadId, host):
        (action, torrent_dir) = self.extractDownloadId(downloadId)
        params = [action, torrent_dir, '--saveas', defaultDirs[action], '--ip', host]
        program = ["dcTorrent.exe", "start"]
        args = program + params
        pp = MyPP(downloadId)
        downloadProcess = reactor.spawnProcess(pp, args[0], args, env = os.environ)
        processes.add(downloadId, downloadProcess)
    def make_torrent(self, source, trackers):
        filename = os.path.join(defaultDirs['seed'], source)
        target = os.path.join(defaultDirs['torrent'], source + '.torrent')
        trackerUris = ['http://{0}:{1}/announce'.format(tracker, defaultSettings['trackerPort']) for tracker in trackers]
        params = [trackerUris[0], filename, '--target', target]
        if len(trackerUris) > 1:
            params += ['--announce_list', ','.join(trackerUris[1:])]
        
        config, args = parseargs(params, defaults, 2, None)
        for file in args[1:]:
            make_meta_file(file, args[0], config)
    def make_torrents(self, trackers, torrent_dir):
        for f in os.listdir(defaultDirs[torrent_dir]):
            if not f.endswith('.torrent'):
                self.make_torrent(f, trackers)

    def render_GET(self, request):
        global trackerPort, downloaders, processes, logger
        
        logger.info(request.uri)

        action = request.args['action'][0]
        if action=='track':
            port = request.args['port'][0]
            self.track(port)
            return 'Tracker is listening on {0}.'.format(port)
        elif action=='seed' or action=='download':
            torrent = request.args['torrent'][0]
            downloadId = self.getDownloadId(action, torrent)
            self.download(downloadId, request.host.host)
            return '{0} is up.'.format(downloadId)
        elif action=='seedmany' or action=='downloadmany':
            param = 'dir'
            if not request.args.has_key(param):
                return 'wrong parameters {0}'.format(param)

            dir = request.args[param][0]
            downloadId = self.getDownloadId(action, os.path.abspath(defaultDirs[dir]))
            self.download_many(downloadId, request.host.host)
            return '{0} is up.'.format(downloadId)
        elif action=='maketorrent':
            source = request.args['source'][0]
            trackers = request.args['trackers'][0].split(',')
            try:
                self.make_torrent(source, trackers)
                return 'Make torrent for {0}'.format(source)
            except ValueError, e:
                return 'error: ' + str(e)
        elif action=='maketorrents':
            trackers = request.args['trackers'][0].split(',')
            # dir name, not path
            torrent_dir = request.args['torrentdir'][0]
            try:
                self.make_torrents(trackers, torrent_dir)
                return 'Make torrents for {0}'.format(torrent_dir)
            except ValueError, e:
                return 'error: ' + str(e)
        elif action=='stop':
            role = request.args['role'][0]
            # set the "done" event, but the role thread will stop sometime later
            if role=='track':
                #tracker.stop()
                processes.kill('track')
                return 'Track is stopped.'
            elif role=='seed' or role=='download':
                torrent = request.args['torrent'][0]
                downloadId = self.getDownloadId(role, torrent)
                processes.kill(downloadId)
                #if downloaders.has_key(torrent):
                #    h = downloaders[torrent]
                #    h.shutdown()
                return '{0} is stopped.'.format(downloadId)
            elif role=='seedmany' or role=='downloadmany':
                param = 'dir'
                if not request.args.has_key(param):
                    return 'wrong parameters {0}'.format(param)
                
                dir = request.args[param][0]
                downloadId = self.getDownloadId(role, os.path.abspath(defaultDirs[dir]))
                processes.kill(downloadId)
                return '{0} is stopped.'.format(downloadId)
        elif action=='clean':
            role = request.args['role'][0]
            if role=='track':
                return 'track log is cleaned.'
            elif role=='seed':
                return 'seed log is cleaned.'
            elif role == 'download':
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
    def getChild(self, action, request):
        if(action=='admin'):
            return DcTorrentAdmin()
        elif(action=='files'):
            return File(defaultDirs['torrent'])
        else:
            return NotFound()

tracker = TrackerServer(trackerAnnouceCallback)

if not os.path.exists(defaultDirs['log']):
    os.makedirs(defaultDirs['log'])

#adminlog = open(defaultDirs['log'] + 'admin.log', 'a')

downloaders = dict()

#logging.config.fileConfig('logging.conf')

dcTorrentLogging.setRootLogger(os.path.join(defaultDirs['log'], 'admin.log'), logging.DEBUG)
logger = logging.getLogger('admin')

processes = ProcessManager()
trackerPort = 0

root = Dispatcher()
factory = Site(root)
reactor.listenTCP(5678, factory)
reactor.run()

#start(int(sys.argv[1]))