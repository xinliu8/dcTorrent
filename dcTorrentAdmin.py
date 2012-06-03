from BitTornado.BT1.track import TrackerServer
from twisted.web.resource import Resource
from twisted.internet import reactor, threads
from twisted.web.server import Site

class DcTorrentAdmin(Resource):
    def render_GET(self, request):
        global tracker
        verb = request.args['action'][0]
        if verb=='track':
            port = request.args['port'][0]
            params = ['--port', port, '--dfile', 'dstate']
            d = threads.deferToThread(tracker.track, params)
            d.addCallback(lambda x: tracker.init())
            return 'Tracker is listening on %s.' % port
        elif verb=='stop':
            tracker.stop()
            return 'Tracker is stopped.'
        else:
            return 'Invalid parameter.'

class NotFound(Resource):
    def render_GET(self, request):
        return "Not Found";

class Dispatcher(Resource):
    def getChild(self, verb, request):
        if(verb=='admin'):
            return DcTorrentAdmin()
        else:
            return NotFound()

tracker = TrackerServer()
root = Dispatcher()
factory = Site(root)
reactor.listenTCP(5678, factory)
reactor.run()

#start(int(sys.argv[1]))