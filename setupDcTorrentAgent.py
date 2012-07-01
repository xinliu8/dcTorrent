from distutils.core import setup
import py2exe
import shutil
import os

setup(console=['dcTorrent.py', 'dcTorrentAdmin.py', 'dcTorrentDashboard.py'])

for file in os.listdir("external"):
    shutil.copy(os.path.join("external", file), "dist")