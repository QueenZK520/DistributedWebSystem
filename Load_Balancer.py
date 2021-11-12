# -*- coding: utf-8 -*-
'''
负载均衡
'''
import math
import numpy as np 
import os
import sys
import random
import time
import datetime
import socket
import threading
import hashlib
import json
from collections import defaultdict

from ThreadPool import ThreadPoolManger


# balancerAddr = '127.0.0.1'  # 默认地址
# balancerAddr = input('\n请输入本机局域网内IP地址:').strip()
balancerPort = 8888  # 默认负载均衡服务器的端口号，各端须保持一致
#WebServerAddr = '127.0.0.1'  # 默认地址

# WebServerPort = 9000  # 默认WebServer的端口号，各端须保持一致

recvBytes = 1024
Load_Balance_Time = 5  # 计算负载间隔
folderMaxSize = 100*1024*1024   # 100M

#
FileTable = defaultdict(set)
# WebServerAddrandPort --> [alive, folderFreeSize, threads_run, ThreadNum, time_delay]
#                   是否存活   剩余存储     正在运行线程数 总线程数 时延
#               --> [alive, score]
# define: score = (folderFreeSize/folderMaxSize + (ThreadNum-threads_run)/ThreadNum)/time_delay
WebServerTable = defaultdict(list)

loadBalancerLog = './log/loadBalancerLog.txt'

def normalization(data):
    # _range = np.max(data) - np.min(data)
    # return (data - np.min(data)) / _range
    return data / np.max(data)

def Load_Balance():
    # 独立线程，更新Web Server的状态
    global WebServerTable
    while True:
        WebServerAddrandPortList = list(WebServerTable.keys())
        print('WebServer表已更新:')
        for it in WebServerTable.items():
            print(it)
        time_delay_list = []
        for WebServerAddrandPort in WebServerAddrandPortList:
            try:
                WebServerAddr = WebServerAddrandPort.split(':')[0] # 取IP
                WebServerPort = WebServerAddrandPort.split(':')[1] # 取端口号
                WebServerPort = int(WebServerPort) # 端口号转int类型

                conn_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
                conn_socket.connect((WebServerAddr, WebServerPort))
                inputs = 'Balance ' + 'Alive?'
                starttime = time.time()
                conn_socket.send(inputs.encode())
                data = conn_socket.recv(recvBytes)
                time_delay = time.time() - starttime
                print(time_delay)
                time_delay_list.append(time_delay)
                json_string = data.decode()
                # 访问量、剩余存储空间、性能等指标
                folderFreeSize, threads_run, ThreadNum = json.loads(json_string)
                WebServerTable[WebServerAddrandPort] = list((1, (folderFreeSize/folderMaxSize + (ThreadNum - threads_run)/ThreadNum)))
                conn_socket.close()
            except socket.error as msg:
                print(WebServerAddrandPort, 'is Dead!')
                WebServerTable[WebServerAddrandPort][0] = 0
                continue
        if len(time_delay_list):
            time_delay_arr = np.array(time_delay_list)
            time_delay_Normalization = normalization(time_delay_arr)
            time_delay_Normalization = list(time_delay_Normalization)
            print(time_delay_Normalization)
        eps = math.exp(-8)
        for WebServerAddrandPort in WebServerAddrandPortList:
            if WebServerTable[WebServerAddrandPort][0] != 0:
                _score = ( WebServerTable[WebServerAddrandPort][1]  ) / (time_delay_Normalization.pop(0) )
                WebServerTable[WebServerAddrandPort][1] = _score
        time.sleep(Load_Balance_Time)
    return 0

# 句柄
def handle_request(conn_socket, conn_addr_port):
    # print('?conn_addr_port ??  ',str(conn_addr_port))
    conn_addr = str(conn_addr_port).split('\'')[1]
    # print('?conn_addr ??  ',str(conn_addr))
    # logtime = time.strftime('%Y-%m-%d-%H:%M:%S.%f',time.localtime(time.time()))
    logtime = datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S.%f') 
    data = conn_socket.recv(recvBytes)
    if not data:
        print('?他突然断开了')
        return
    #global WebServerTable, FileTable
    json_string = data.decode()
    reqList = json.loads(json_string)
    cmd = reqList[-1]
    print('thread %s is running ： %s' %(threading.current_thread().name, cmd) )
    # print(reqList)
    if cmd == 'download':
        # 处理客户端的下载请求
        files = reqList[0:-1]
        WebServerAddrandPortList = []
        for file in files:
            # 遍历FileTable的key=file的WebServerAddr
            addrandports = list(FileTable[file])
            if len(addrandports) <= 0:  # file不存在
                continue
            WebServerAddrandPort = addrandports[0]
            for addr in addrandports:
                if WebServerTable[addr][0] != 0:
                    if WebServerTable[addr][1] > WebServerTable[WebServerAddrandPort][1]:
                        WebServerAddrandPort = addr
            WebServerAddrandPortList.append(WebServerAddrandPort)
        json_string = json.dumps(WebServerAddrandPortList)
        conn_socket.send(json_string.encode())
        # 日志
        log = ('\n===========%s===========\nthread %s is running ： %s %s send: %s \n' %(logtime,threading.current_thread().name,conn_addr_port, cmd, WebServerAddrandPortList) )
        with open(loadBalancerLog,"a") as logfile:
            logfile.write(log)

    elif cmd == 'upload':
        # 处理客户端的上传请求
        # 计算负载，选择一个最好的WebServerAddrandPort，发送给客户端
        # 《这里也可以设计成逐个文件判断是否需要上传，返回列表，但加重负载》
        addrandports = list(WebServerTable.keys())
        WebServerAddrandPort = addrandports[0]
        for addr in addrandports:
            if WebServerTable[addr][0] != 0:
                if WebServerTable[addr][1] > WebServerTable[WebServerAddrandPort][1]:
                    WebServerAddrandPort = addr
        conn_socket.send(WebServerAddrandPort.encode())
        # 日志
        log = ('\n==========%s===========\nthread %s is running ： %s %s send: %s \n' %(logtime, threading.current_thread().name,conn_addr_port, cmd, WebServerAddrandPort) )
        with open(loadBalancerLog,"a") as logfile:
            logfile.write(log)
    elif cmd == 'backup':
        # 处理WebServer的备份请求
        print('一个WebServer正在申请备份...')
        connPort = reqList[-2]
        conn_AddrandPort = conn_addr+':'+str(connPort)

        # 更新文件列表
        files = reqList[0:-2]
        for file in files:
            FileTable[file].add(conn_AddrandPort)
        print('文件表已更新:')

        # print(FileTable)##
        # 这样可能需要对FileTable加一个锁？
        # for it in FileTable.items():
        #     print(it)
        # 或者这样吧
        filetablekeylist = list(FileTable.keys())
        for it in filetablekeylist:
            print(' ',it, ' : ', FileTable[it])
        
        # 计算负载，选择除它以外的一个最好的WebServerAddr，发送给WebServer
        # 《这里也设计成逐个文件判断是否需要备份，对方的已有文件就无需备份，
        # 但是这会增加负载均衡服务器计算负载，为了实现均衡负载，考虑可以存放在>=2台web服务器中》
        addrandports = list(WebServerTable.keys())
        for i in addrandports[::-1]:
            if i == conn_AddrandPort:
                addrandports.remove(i)
        WebServerAddrandPort = addrandports[0]
        for addr in addrandports:
            if addr != conn_AddrandPort and WebServerTable[addr][0] != 0:
                if WebServerTable[addr][1] > WebServerTable[WebServerAddrandPort][1]:
                    WebServerAddrandPort = addr
        if WebServerAddrandPort == conn_AddrandPort:
            WebServerAddrandPort = 'Error! Can not backup! Only one WebServer?'
        conn_socket.send(WebServerAddrandPort.encode())
        # 日志
        print('backup - send  ', WebServerAddrandPort)
        log = ('\n==========%s===========\nthread %s is running ： %s %s send: %s \n' %(logtime, threading.current_thread().name,conn_addr_port, cmd, WebServerAddrandPort) )
        with open(loadBalancerLog,"a") as logfile:
            logfile.write(log)

    elif cmd == 'Init':
        print('一个WebServer正在进行连接...')
        WebServerAddr = conn_addr
        WebServerPort = reqList[-2]
        WebServerAddrandPort = WebServerAddr+':'+str(WebServerPort)
        ThreadNum = reqList[-3]     # ThreadNum = 4
        threads_run = reqList[-4]   # web的thread_pool.get_thread_num()
        folderFreeSize = reqList[-5]    # folderFreeSize
        files = reqList[0:-5]       # web的文件列表
        WebServerTable[WebServerAddrandPort] = list((1, folderFreeSize/folderMaxSize + (ThreadNum - threads_run)/ThreadNum))
        for file in files:
            FileTable[file].add(WebServerAddrandPort)
        conn_socket.send('ok'.encode())
        print('WebServer表已更新:')
        for it in WebServerTable.items():
            print(it)
        print('文件表已更新:')
        for it in FileTable.items():
            print(it)
        # 日志
        log = '\n===========%s==============\nthread %s is running ： %s %s \n' %(logtime, threading.current_thread().name,conn_addr_port, cmd) 
        filetablekeylist = list(FileTable.keys())
        for it in filetablekeylist:
            log = '%s %s : %s \n' %(log, it,  FileTable[it])
        with open(loadBalancerLog,"a") as logfile:
            logfile.write(log)

    conn_socket.close()


'''
创建多线程Load balancer
'''
thread_pool = ThreadPoolManger(4)

if __name__ == '__main__':
    # balancerAddr = input('\n请输入本机局域网内IP地址:').strip()
    # if balancerAddr == '127':
    #     balancerAddr = '127.0.0.1'

    balancerAddr = sys.argv[1] # 命令行参数

    try:
        s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        addr = (balancerAddr, balancerPort)
        s.bind(addr)
        s.listen(4)
    except socket.error as msg:
        print(msg)
        sys.exit(1)

    thread_pool.add_job(Load_Balance)
    # 循环等待接收客户端请求
    while True:
        ####################print('>>>>>>>>>>等待请求...')
        # 阻塞等待请求
        conn_socket, conn_addr = s.accept()
        print('Load Balancer收到请求，连接地址:%s' % str(conn_addr))
        # 一旦有请求了，把socket扔到指定处理函数，放进任务队列

        '''
        这里单纯通过连接无法决定分配哪个处理函数：
            客户端的请求？Balancer的请求？其他WebServer的请求？
        需要从请求消息中解析请求类型
        最后，确定处理函数之后连同conn_socket送入线程池
        '''

        # 等待线程池分配线程处理
        thread_pool.add_job(handle_request, *(conn_socket, conn_addr, ))

    s.close()