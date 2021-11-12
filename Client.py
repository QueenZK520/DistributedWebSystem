# -*- coding: utf-8 -*-

import os
import sys
import time
import random
import socket
import hashlib
import json
import threading
from tqdm import tqdm

from ThreadPool import ThreadPoolManger

# netstat -a|findstr 端口号

# 下载缓存路径
foldername_Client = 'files_Client'
files_Client_Path = os.getcwd() + '\\' + foldername_Client + '\\'
if not os.path.exists(files_Client_Path):
    os.mkdir(files_Client_Path)

# 待上传的网页所在的路径
foldername_upload_Client = '_files_Client'
files_Client_upload_Path = os.getcwd() + '\\' + foldername_upload_Client + '\\'

# 按照Wbe访问，这里只是为方便模拟，取files_WebServer上的文件列表
files_WebServer_Path = './files_WebServer/'

# 负载均衡服务器的IP和端口
# balancerAddr = '127.0.0.1'
# balancerAddr = input('\nInput balancerAddr(such as 127.0.0.1):').strip()
balancerAddr = sys.argv[1] # 命令行参数
balancerPort = 8888

# WebServerPort = 9000

recvBytes = 1024



'''
向WebServerAddr上传filelist中的文件
《多个文件按次序上传》
'''
def uploading(WebServerAddrandPort, filelist):
    try:
        WebServerAddr = WebServerAddrandPort.split(':')[0] # 取IP
        WebServerPort = WebServerAddrandPort.split(':')[1] # 取端口号
        WebServerPort = int(WebServerPort) # 端口号转int类型

        conn_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        conn_socket.connect((WebServerAddr, WebServerPort))
        for file in filelist:
            # print(file)
            filename = files_Client_upload_Path + file
            # 文件不存在则跳过
            if os.path.isfile(filename):
                # 计算文件大小（Byte)
                file_size = os.stat(filename).st_size
                # 进度条
                # pbar = tqdm(total=file_size, desc=file, file=sys.stdout)
                pbar = tqdm(total=file_size, desc=file)
                inputs = 'upload ' + file
                conn_socket.send(inputs.encode())# cmd + file
                confirm = conn_socket.recv(recvBytes)
                IsRecv = confirm.decode()
                # print(IsRecv)
                if IsRecv != 'ok':
                    pbar.set_postfix(_to= WebServerAddrandPort, err='Web服务器中已存在该文件，上传失败！')
                    pbar.close()
                    continue
                # 发送文件大小
                conn_socket.send(str(file_size).encode())
                confirm = conn_socket.recv(recvBytes)
                IsRecv = confirm.decode()
                # print(IsRecv)
                if IsRecv != 'Prepared':
                    continue
                # 生成md5对象
                m = hashlib.md5()
                #
                with open(filename, 'rb') as fn:
                    # 开始发文件，发一行更新一下md5的值，因为不能直接md5文件
                    # 到最后读完就是整个文件的md5的值
                    for line in fn:
                        m.update(line)
                        conn_socket.send(line)
                        pbar.set_postfix(_to= WebServerAddrandPort)
                        pbar.update(len(line))
                fn.close()
                origin_file_md5 = m.hexdigest()
                # 接收服务器接收成功
                confirm = conn_socket.recv(recvBytes)
                # send md5
                conn_socket.send(origin_file_md5.encode())
                # 接收服务器传回的md5
                server_file_md5 = conn_socket.recv(recvBytes)
                new_file_md5 = server_file_md5.decode()
                # print('file md5:',origin_file_md5,'\nrecved file md5:',new_file_md5)
                if origin_file_md5 == new_file_md5:
                	pbar.set_postfix(_to= WebServerAddrandPort, md5check='pass')
                    # print(filename, '===> sended ===>', WebServerAddrandPort)
                else:
                	pbar.set_postfix(_to= WebServerAddrandPort, md5check='fail')
                    # print(filename, 'send Error! Check for the Network.')
            else:
                print('本地文件不存在')
            pbar.close()
        conn_socket.close()
    except socket.error as msg:
        print('文件上传失败！', WebServerAddrandPort, '...')


'''
从WebServerAddr下载filelist中的文件    OK
《多个文件按次序下载》
'''
def downloading(WebServerAddrandPort, filelist):
    try:
        # print('test  ', WebServerAddrandPort)
        WebServerAddr = WebServerAddrandPort.split(':')[0] # 取IP
        WebServerPort = WebServerAddrandPort.split(':')[1] # 取端口号
        WebServerPort = int(WebServerPort) # 端口号转int类型
        # print('ddd',WebServerAddr)
        # print('ddddp',WebServerPort)
        conn_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        conn_socket.connect((WebServerAddr, WebServerPort))
        for file in filelist:
            inputs = 'download ' + file
            conn_socket.send(inputs.encode())
            file_size = conn_socket.recv(recvBytes)
            file_size = int(file_size.decode())
            # 重复的文件名加个括号和标号
            filename = files_Client_Path + file
            if os.path.isfile(filename):
                namewhat = 1
                nametmp = filename
                while os.path.isfile(filename):
                    name, ext = os.path.splitext(nametmp)# 分离文件名和文件格式后缀
                    filename = name + '(%d)'%namewhat + ext
                    namewhat += 1
            # 进度条
            pbar = tqdm(total=file_size, desc=file, file=sys.stdout)
            if file_size == 0:
                # print('File not exist in Server!')
                pbar.set_postfix(_from= WebServerAddrandPort, err='Web服务器中不存在该文件，下载失败！')
                pbar.close()
                continue
            # 开始下载
            conn_socket.send('Prepared'.encode())
            # 赋值方便最后打印大小
            new_file_size = file_size
            # 生成md5对象
            m = hashlib.md5()
            with open(filename, 'wb') as fn:
                while new_file_size > 0:
                    data = conn_socket.recv(recvBytes)
                    new_file_size -= len(data)# 收多少减多少
                    m.update(data)# 同步发送端，收一次更新一次md5
                    fn.write(data)
                    pbar.set_postfix(_from= WebServerAddrandPort)
                    pbar.update(len(data))
                fn.flush
            fn.close()
            # 得到下载完的文件的md5
            new_file_md5 = m.hexdigest()
            #print('file recv:', file_size)
            #print('file saved in:', filename)
            conn_socket.send('ok'.encode())
            # 接收服务器端的文件的md5
            server_file_md5 = conn_socket.recv(recvBytes)
            origin_file_md5 = server_file_md5.decode()
            # 打印两端的md5值，看是否相同
            # print('server file md5:',origin_file_md5,'\nrecved file md5:',new_file_md5)
            if origin_file_md5 == new_file_md5:
            	pbar.set_postfix(_from= WebServerAddrandPort, md5check='pass')
                # print('文件下载成功', '%d(bytes)'%file_size, '已保存到',filename)
            else:
                pbar.set_postfix(_from= WebServerAddrandPort, md5check='fail')
                # print(filename, '文件无效，删除文件!')
                os.remove(filename)
            pbar.close()
        conn_socket.close()
    except socket.error as msg:
        print('\n文件下载失败！', WebServerAddrandPort, 'Web服务器宕机或可能有bug...\n')


'''
发送端上传文件：先向balancer请求，再上传到一个WebServer    OK
'''
def Upload(files):
    # print('thread %s is running, ' % threading.current_thread().name, files)
    '''连接balancer，获得目标地址'''
    conn_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    conn_socket.connect((balancerAddr, balancerPort))
    # 向balancer发upload命令
    cmd = ['upload']
    json_string = json.dumps(cmd)
    conn_socket.send(json_string.encode())
    # 接收一个WebServerAddrandPort
    recv_data = conn_socket.recv(recvBytes)
    WebServerAddrandPort = recv_data.decode()
    conn_socket.close()

    #连接目标地址的WebServer，上传文件
    uploading(WebServerAddrandPort, files)


'''
接收端下载文件：先向balancer请求，再从多个WebServer上下载   OK
'''
def Download(files):
    # print('thread %s is running, ' % threading.current_thread().name, files)
    '''连接balancer，获得可上传文件列表和目标地址'''
    conn_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    conn_socket.connect((balancerAddr, balancerPort))
    # 向balancer发文件列表
    files.append('download')
    json_string = json.dumps(files)
    conn_socket.send(json_string.encode())# cmd + files
    # 接收WebServerAddrList，与files[1:]一一对应
    recv_data = conn_socket.recv(recvBytes)# WebServerAddrandPortList
    json_string = recv_data.decode()
    WebServerAddrandPortList = json.loads(json_string)
    #print(WebServerAddrandPortList)
    conn_socket.close()

    # 依次访问不重复的WebServerAddr
    # print(WebServerAddrandPortList)
    length = len(WebServerAddrandPortList)
    ConnAddrandPortList = list(set(WebServerAddrandPortList))
    for ConnAddrandPort in ConnAddrandPortList:
        filelist = [files[i] for i in range(length) if ConnAddrandPortList[i]==ConnAddrandPort]
        downloading(ConnAddrandPort, filelist)


'''
多线程模拟客户端请求
'''
thread_pool = ThreadPoolManger(20)


def handle_Input(Req=1, Cnt=3,  fileNum=1):
    '''
    Cnt:    请求次数
    Threads:    线程数
    Req=0: 上传
    Req=1: 下载
    '''
    if Req==0:
        for root, dirs, files in os.walk(files_Client_upload_Path):
            for C in range(Cnt):
                rs = random.sample(files, fileNum)
                thread_pool.add_job(Upload, *(rs, ))
                time.sleep(0.6) # 60/100 一分钟100次（）

    elif Req==1:
        filelist_s = []
        for root, dirs, files in os.walk(files_WebServer_Path):
            filelist_s += files
        for C in range(Cnt):
            rs = random.sample(filelist_s, fileNum)
            thread_pool.add_job(Download, *(rs, ))
            time.sleep(0.006) # 60/1000 一分钟1000次访问（下载）



if __name__ == '__main__':
    dou = sys.argv[2] # 命令行参数:{0: 上传，1：下载}
    cntnum = sys.argv[3] # 命令行参数

    handle_Input(Req = int(dou),  Cnt = int(cntnum) ,  fileNum=1 )

    #thread_pool.wait_jobs(60)
    time.sleep(1000)
    cmd = input('\n要退出吗？Y(y)/N(n):').strip()
