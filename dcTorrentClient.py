import sys
import httplib

tracker = '157.59.41.247'
seeders = ['157.59.41.247']
downloaders = ['157.59.41.247']

adminPort = '5678'

def startSeed(ip, torrent):
    request = '/admin?action=seed&torrent=%s' % torrent
    site = ip + ':' + adminPort
    httpGet(site, request)

def startDownload(ip, torrent):
    request = '/admin?action=download&torrent=%s' % torrent
    site = ip + ':' + adminPort
    httpGet(site, request)

def startTrack(ip):
    request = '/admin?action=track&port=6969'
    site = ip + ':' + adminPort
    httpGet(site, request)

def stopTrack(ip):
    request = '/admin?action=stop&role=track'
    site = ip + ':' + adminPort
    httpGet(site, request)

def makeTorrent(ip, source):
    request = '/admin?action=maketorrent&source=%s' % source
    site = ip + ':' + adminPort
    httpGet(site, request)

def httpGet(site, request):
    conn = httplib.HTTPConnection(site)
    conn.request("GET", request)
    r = conn.getresponse()
    print r.status, r.reason

if __name__ == '__main__':

    startTrack(tracker)
    filename = 'gparted.iso'
    makeTorrent(tracker, filename)
    torrentUri = "http://{0}:{1}/files/{2}.torrent".format(tracker, adminPort, filename)
    for seeder in seeders:
        startSeed(seeder, torrentUri)
    for downloader in downloaders:
        startDownload(downloader, torrentUri)
