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
        self.logger = logging.getLogger('{0}.{1}'.format(__name__, self.__class__.__name__))
    def has(self, name):
        self.lock.acquire()
        isExists = True if self.processes.has_key(name) else False
        self.lock.release()
        return isExists
    def add(self, name, process):
        self.lock.acquire()
        self.processes[name] = process
        self.logger.debug('Add process ' + name)
        self.lock.release()
    def remove(self, name):
        self.lock.acquire()
        if self.processes.has_key(name):
            del self.processes[name]
            self.logger.debug('Remove process ' + name)
        self.lock.release()
    def kill(self, name):
        self.lock.acquire()
        if self.processes.has_key(name):
            self.processes[name].signalProcess('KILL')
            del self.processes[name]
            self.logger.debug('Killed and removed process ' + name)
        self.lock.release()

class DcTorrentAdmin(Resource):
    def __init__(self):
        dcTorrentLogging.setRootLogger(os.path.join(defaultDirs['log'], 'admin.log'), logging.DEBUG)
        self.logger = logging.getLogger('admin')

    def getDownloadId(self, action, target):
        if target.find('http') == -1 :
            return action + '$' + os.path.normcase(os.path.abspath(target))
        else:
            return action + '$' + target

    def extractDownloadId(self, downloadId):
        separator = downloadId.find('$')
        return (downloadId[:separator], downloadId[separator+1:])

    def getDcTorrentPath(self):
        application_path = ''
        if getattr(sys, 'frozen', False):
            application_path = os.path.dirname(sys.executable)
            return [os.path.join(application_path, "dcTorrent.exe")]
        elif __file__:
            application_path = os.path.dirname(__file__)
            return [os.path.join(defaultDirs['python'], 'python.exe'), os.path.join(application_path, 'dcTorrent.py')]
        
    def track(self, port):
        program = self.getDcTorrentPath()
        params = ["start", "track", '--port', port, '--dfile', 'dstate']
        args = program + params
        pp = MyPP('track')
        trackerProcess = reactor.spawnProcess(pp, args[0], args, env = os.environ)
        processes.add('track', trackerProcess)
        
        #d = threads.deferToThread(tracker.track, params)
        # clear the "done" event for the next start
        #d.addCallback(lambda x: tracker.init())

    def download(self, downloadId, host, trackers=[]):
        
        # disallow multiple downloaders on one machine
        #if processes.has(downloadId):
        #    return 'Downloader is already up'.format(downloadId)
        (action, torrent) = self.extractDownloadId(downloadId)
        parts = urlparse(torrent)
        components = os.path.normpath(parts.path).split(os.sep)
        torrentName = components[len(components)-1]
        filename = torrentName[:torrentName.find('.torrent')]
        trackerUris = ['http://{0}:{1}/announce'.format(tracker, defaultSettings['trackerPort']) for tracker in trackers]
        params = ['start', action, '--url', torrent, '--saveas', os.path.join(defaultDirs[action], filename), '--ip', host]
        if len(trackers) > 0:
            params += [ '--announce_list', ','.join(trackerUris)]
        #if action == 'seed':
        #    params += ['--super_seeder', '1']
        program = self.getDcTorrentPath()
        args = program + params
        pp = MyPP(downloadId)
        downloadProcess = reactor.spawnProcess(pp, args[0], args, env = os.environ)
        processes.add(downloadId, downloadProcess)
        #h = HeadlessDownloader(removeDownloader)
        #downloaders[torrent] = h
        #d = threads.deferToThread(h.download, params)
        #d.addCallback(h.downloadCallback)
    def download_many(self, downloadId, host, trackers=[]):
        # now only used for seed many
        (action, dir) = self.extractDownloadId(downloadId)
        trackerUris = ['http://{0}:{1}/announce'.format(tracker, defaultSettings['trackerPort']) for tracker in trackers]
        params = ["start", action, dir, '--saveas', dir, '--ip', host]
        if len(trackers) > 0:
            params += [ '--announce_list', ','.join(trackerUris)]
        program = self.getDcTorrentPath()
        args = program + params
        pp = MyPP(downloadId)
        downloadProcess = reactor.spawnProcess(pp, args[0], args, env = os.environ)
        processes.add(downloadId, downloadProcess)
    def make_torrent(self, filename, dir, trackers):
        source = os.path.join(dir, filename)
        target = os.path.join(dir, filename + '.torrent')
        trackerUris = ['http://{0}:{1}/announce'.format(tracker, defaultSettings['trackerPort']) for tracker in trackers]
        params = [trackerUris[0], source, '--target', target]
        if len(trackerUris) > 1:
            params += ['--announce_list', ','.join(trackerUris[1:])]
        
        config, args = parseargs(params, defaults, 2, None)
        for file in args[1:]:
            make_meta_file(file, args[0], config)
    def make_torrents(self, trackers, dir):
        # recursively
        for item in os.listdir(dir):
            if os.path.isfile(os.path.join(dir, item)):
                if not item.endswith('.torrent'):
                    self.make_torrent(item, dir, trackers)
            else:
                self.make_torrents(trackers, os.path.join(dir, item))
    def render_GET(self, request):
        global downloaders, processes, root, VIEWS
        
        self.logger.info(request.uri)

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

            abs_dir = request.args[param][0]
            VIEWS['files'] = File(abs_dir)
            root.putChild('files', File(abs_dir))
            downloadId = self.getDownloadId(action, abs_dir)

            if request.args.has_key('trackers'):
                trackers = request.args['trackers'][0]
            self.download_many(downloadId, request.host.host, trackers)
            return '{0} is up.'.format(downloadId)
        elif action=='maketorrent':
            source = request.args['source'][0]
            trackers = request.args['trackers'][0].split(',')
            try:
                filename = os.path.basename(source)
                dir = os.path.dirname(source)
                self.make_torrent(filename, dir, trackers)
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
                downloadId = self.getDownloadId(role, dir)
                processes.kill(downloadId)
                return '{0} is stopped.'.format(downloadId)
        elif action=='clean':
            role = request.args['role'][0]
            log = os.path.join(defaultDirs['log'], '{0}.log'.format(role))
            if os.path.exists(log):
                os.remove(log)
            if role == 'download':
                try:
                    if os.path.exists(defaultDirs['download']):
                        shutil.rmtree(defaultDirs['download'])
                except:
                    logger.exception(str(sys.exc_info()[0]))
            
            return 'Cleaned {0}.'.format(role)
        else:
            return 'Invalid parameter.'

class NotFound(Resource):
    def render_GET(self, request):
        return "Not Found";

class Dispatcher(Resource):
    def render_GET(self, request):
        return 'try these actions: admin, files, etc'
    def getChild(self, action, request):
        if action == '':
            return self
        else:
            if action in VIEWS.keys():
                return Resource.getChild(self, action, request)
            else:
                return NotFound()


#tracker = TrackerServer(trackerAnnouceCallback)



downloaders = dict()
processes = ProcessManager()

if not os.path.exists(defaultDirs['log']):
    os.makedirs(defaultDirs['log'])

VIEWS = {
         'admin': DcTorrentAdmin()
}

root = Dispatcher()
for viewName, className in VIEWS.items():
    root.putChild(viewName, className)

server = Site(root)
reactor.listenTCP(5678, server)
reactor.run()