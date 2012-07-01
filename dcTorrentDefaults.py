import os
#workDir = 'e:\\Code\\Python\\dcTorrent\\'
#workDir = os.getcwd()
workDir = 'C:\\dcTorrentRepository\\'

defaultDirs = { 
               'seed': os.path.join(workDir, 'data'), 
               'download': os.path.join(workDir, 'downloaded'), 
               'seedmany': os.path.join(workDir, 'data'), 
               'downloadmany': os.path.join(workDir, 'downloaded'), 
               'torrent': os.path.join(workDir, 'torrent'), 
               'log': os.path.join(workDir, 'logs'),
               'profile': os.path.join(workDir, 'logs'),
               'dist': workDir,
               'python': 'C:\\Python27\\'
               # change this before deploy
               #'python': 'd:\\Users\\rd\\Python27\\'
              }

defaultSettings = { 
               'adminPort':'5678',
               'trackerPort':'6969',
              }

adjustDownloader = {
                    'download_slice_size': 2 ** 14, #2 ** 14,
                    'upload_unit_size': 1460,
                    'minport': 56969, #10000
                    'maxport': 56970, #60000
                    'timeout': 300.0,
                    'timeout_check_interval': 60.0,
                    'max_slice_length': 2 ** 30, #2 ** 17,
                    'upnp_nat_access': 0, #1,
                    'rerequest_interval': 5, #5 * 60,
                    'http_timeout': 60, 
                    'max_upload_rate': 0,
                    'max_download_rate': 0,
                    'alloc_type': 'normal', #'normal',
                    'alloc_rate': 2.0,
                    'write_buffer_size': 4, #4,
                    'breakup_seed_bitfield': 0, #1,
                    'snub_time': 30.0,
                    'super_seeder': 0,
                    'security': 0, #1,
                    'auto_kick': 0, #1,
                    'double_check': 0, #1,
                    'lock_files': 0, #1,
                    'auto_flush': 1, #0,
                    'spew': 1,
                    'max_initiate': 40, #40,
                    'max_uploads': 7, #7
                    'seed_after_finish': 10
                    }
