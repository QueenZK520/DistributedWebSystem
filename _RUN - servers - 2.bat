echo 启动负载均衡服务器
start "Load_Balancer" cmd /k "python3 Load_Balancer.py 192.168.1.103"

ping 1.1.1.1 -n 1 -w 60 > nul

echo 打开新的窗口，启动Web服务器1号
start "WebServer_1" cmd /k "python3 Web_Server.py 192.168.1.103 192.168.1.103"

ping 1.1.1.1 -n 1 -w 60 > nul

echo 打开新的窗口，启动Web服务器2号
start "WebServer_2" cmd /k "python3 Web_Server2.py 192.168.1.103 192.168.1.103"

ping 1.1.1.1 -n 1 -w 60 > nul

echo 打开新的窗口，启动Web服务器3号
start "WebServer_3" cmd /k "python3 Web_Server3.py 192.168.1.103 192.168.1.103"

ping 1.1.1.1 -n 1 -w 60 > nul

echo 打开新的窗口，启动Web服务器4号
start "WebServer_4" cmd /k "python3 Web_Server4.py 192.168.1.103 192.168.1.103"


