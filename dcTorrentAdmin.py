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

defaultDirs = { 'seed':'..\\data\\', 'download':'..\\downloaded\\', 'torrent':'..\\data\\'}

class DcTorrentAdmin(Resource):
    def removeDownloader(self, result):
        global downloaders
        if result.find('.torrent') > -1:
            del downloaders[torrent]

    def render_GET(self, request):
        global tracker
        global downloaders
        verb = request.args['action'][0]
        if verb=='track':
            port = request.args['port'][0]
            params = ['--port', port, '--dfile', 'dstate']
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
            params = [verb, '--url', torrent, '--saveas', defaultDirs[verb] + filename]
            h = HeadlessDownloader()
            downloaders[torrent] = h
            d = threads.deferToThread(h.download, params)
            d.addCallback(self.removeDownloader)
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
                h = downloaders[torrent]
                h.shutdown()
            return '{0} is stopped.'.format(role)
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

tracker = TrackerServer()
downloaders = {}

root = Dispatcher()
factory = Site(root)
reactor.listenTCP(5678, factory)
reactor.run()

#start(int(sys.argv[1]))