from BitTornado.BT1.track import TrackerServer
from multiprocessing import Process
from bottle import Bottle, route, run

app = Bottle()
app.tracker = TrackerServer()

@app.route('/track/<port>')
#@route('/track/<port>')
def track(port):
    params = ['--port', port, '--dfile', 'dstate']
    Process(target=app.tracker.track, args=(params)).start()
    return "Tracker is listening on %s!" % port

@app.route('/stop/<role>')
#@route('/stop/<role>')
def track(role):
    if role=='track':
        app.tracker.stop()
    return "Tracker is stopped!"

run(app, host='localhost', port=5678)