from BitTornado.BT1.track import TrackerServer
from BitTornado.BT1.makemetafile import make_meta_file, defaults
from BitTornado.parseargs import parseargs
from dcTorrentDownload import HeadlessDownloader

from twisted.web.resource import Resource
from twisted.internet import reactor, threads
from twisted.web.server import Site
from twisted.web.static import File

from urlparse import urlparse
import os
from time import time, gmtime, strftime
import shutil
import sys

defaultDirs = { 'seed':'..\\data\\', 'download':'..\\downloaded\\', 'torrent':'..\\data\\', 'log':'..\\logs\\'}

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

class DcTorrentAdmin(Resource):
    
    def log(self, stuff):
        global adminlog
        adminlog.write(stuff + '\n')
        adminlog.flush()

    def render_GET(self, request):
        global tracker
        global downloaders
        
        self.log(request.uri)

        verb = request.args['action'][0]
        if verb=='track':
            port = request.args['port'][0]
            params = ['--port', port, '--dfile', 'dstate', '--logfile', defaultDirs['log'] + 'tracker.log']
            d = threads.deferToThread(tracker.track, params)
            # clear the "done" event for the next start
            d.addCallback(lambda x: tracker.init())
            return 'Tracker is listening on {0}.'.format(port)
        elif verb=='seed' or verb=='download':
            torrent = request.args['torrent'][0]
            parts = urlparse(torrent)
            components = os.path.normpath(parts.path).split(os.sep)
            torrentName = components[len(components)-1]
            filename = torrentName[:torrentName.find('.torrent')]
            params = [verb, '--url', torrent, '--saveas', defaultDirs[verb] + filename, '--ip', request.host.host, '--minport', 56969, '--maxport', 56970, '--logfile', '{0}{1}.log'.format(defaultDirs['log'], verb)]
            h = HeadlessDownloader(removeDownloader)
            downloaders[torrent] = h
            d = threads.deferToThread(h.download, params)
            #d.addCallback(h.downloadCallback)
            return '{0} {1}.'.format(verb, torrent)
        elif verb=='maketorrent':
            if tracker.port==0:
                return 'Tracker is not started yet.'

            source = request.args['source'][0]
            filename = defaultDirs['seed'] + source
            target = defaultDirs['torrent'] + source + '.torrent'
            trackerUri = 'http://{0}:{1}/announce'.format(request.host.host, str(tracker.port))
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
                tracker.stop()
            elif role=='seed' or role=='download':
                torrent = request.args['torrent'][0]
                if downloaders.has_key(torrent):
                    h = downloaders[torrent]
                    h.shutdown()
            return '{0} is stopped.'.format(role)
        elif verb=='clean':
            try:
                if os.path.exists(defaultDirs['log'] + 'stat.log'):
                    os.remove(defaultDirs['log'] + 'stat.log')
                if os.path.exists(defaultDirs['log'] + 'download.log'):
                    os.remove(defaultDirs['log'] + 'download.log')
                if os.path.exists(defaultDirs['download']):
                    shutil.rmtree(defaultDirs['download'])
            except:
                self.log(sys.exc_info()[0])
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
adminlog = open(defaultDirs['log'] + 'admin.log', 'a')
downloaders = dict()

root = Dispatcher()
factory = Site(root)
reactor.listenTCP(5678, factory)
reactor.run()

#start(int(sys.argv[1]))