# -*- coding: utf-8 -*-

import os
import sys
import random
import socket
import hashlib
import json
import threading
import signal

# foldername_WebServer = 'files_WebServer'
# str = os.getcwd()
# files_WebServer_Path = str + '\\' + foldername_WebServer + '\\'
# ise = os.path.exists(files_WebServer_Path)
# print(files_WebServer_Path)
# print(ise)

# filelist_s = []
# files_WebServer_Path = 'files_WebServer'
# for root, dirs, files in os.walk(files_WebServer_Path):
# 	print('root: ',root)
# 	print('dirs: ',dirs)
# 	print('files: ',files)
# 	print(' ')
# 	filelist_s += files

# print(filelist_s)

# rs = random.sample(filelist_s, 2)
# print(rs)



filelist = ['上传_01.txt', 9004, 'backup']
files = filelist[0,-1]
print(files)