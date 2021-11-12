echo 打开新的窗口，启动客户端
echo 参数 [Load_Balancer_IP, 上传或下载, 客户端数量]
echo 0:upload, 1:download
start "Client" cmd /k "python3 Client.py 127.0.0.1 1 100"

