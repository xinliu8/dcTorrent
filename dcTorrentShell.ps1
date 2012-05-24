. .\defaults.ps1

function Start-Peer($role, $torrent, $filePath, $ip) { 
    $startPeer = {
        cd $args[0] 
        python $args[1] dcTorrent.py start $args[2] --url $args[3] --saveas $args[4] --ip $args[5]
    }
    
    Invoke-Command $ip $startPeer -argumentlist $workDir,$pythonConfig,$role,$torrent,$filePath,$ip -credential $cred -AsJob
}

function Stop-Peer($role, $torrent, $ip) {
    $stopPeer = {
        wmic Path win32_process Where "CommandLine Like '%python%dcTorrent.py start $args[0] $args[1]%'" Call Terminate
    }

    Invoke-Command $ip $stopPeer -argumentlist $role,$torrent -credential $cred -AsJob
}

function Start-Downloader($torrent, $filePath, $ip){ 
    Start-Peer 'download' $torrent $filePath $ip 
}

function Stop-Downloader($torrent, $filePath, $ip){ 
    Stop-Peer 'download' $torrent $filePath $ip 
}

function Start-Seeder($torrent, $filePath, $ip){ 
    Start-Peer 'seed' $torrent $filePath $ip 
}

function Stop-Seeder($torrent, $filePath, $ip){ 
    Stop-Peer 'seed' $torrent $filePath $ip 
}

function Stop-Tracker { 
    $stopTracker = {  
        cd $args[0]
        python $args[1] dcTorrentTrackerService.py stop
        python $args[1] dcTorrentTrackerService.py remove 
    }

    Invoke-Command $tracker $stopTracker -argumentlist $workDir,$pythonConfig -credential $cred
}

function Start-Tracker { 
    $startTracker = {
        cd $args[0]
        python $args[1] dcTorrentTrackerService.py install
        python $args[1] dcTorrentTrackerService.py start 
    }

    Invoke-Command $tracker $startTracker -argumentlist $workDir,$pythonConfig -credential $cred
}

function Make-Torrent ($source, $target, $computerName){

    $makeTorrent = {
        Param($workDir,$pythonConfig,$trackerURI,$source,$target)
        cd $workDir 
        python $pythonConfig dcTorrent.py make torrent $trackerURI $source --target $target
    }

    Invoke-Command $computerName $makeTorrent -ArgumentList $workDir,$pythonConfig,$trackerURI,$source,$target -credential $cred
}

function Start-Seeders($fileName) {
    $source = "$seederPath$fileName"
    $torrentURI = "$torrentsServer$fileName.torrent"
    $torrentLocal = "$torrentsPath$fileName.torrent"
    
    Make-Torrent $source $torrentLocal $tracker
    
    foreach ($seeder in $seeders) {
        Start-Seeder $torrentURI $source $seeder
    }
}

function Stop-Seeders {
    foreach ($seeder in $seeders) {
        Stop-Seeder $torrent $seeder
    }
}

function Start-Downloaders($fileName){
    $dest = $downloaderPath + $fileName
    $torrentURI = "$torrentsServer$fileName.torrent"
    foreach ($downloader in $downloaders) {
        Start-Downloader $torrentURI $dest $downloader
    }
}

function Stop-Downloaders {
    foreach ($downloader in $downloaders) {
        Stop-Downloader $torrent $downloader
    }
}
