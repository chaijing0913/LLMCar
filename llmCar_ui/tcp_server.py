import socket
import json
import threading
import time

class TCPServer:
    def __init__(self, host='0.0.0.0', port=8080):
        self.host = host
        self.port = port
        self.server_socket = None
        self.client_socket = None
        self.client_address = None
        self.is_running = False
        
    def start(self):
        """启动TCP服务器"""
        self.server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.server_socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        self.server_socket.bind((self.host, self.port))
        self.server_socket.listen(1)
        self.is_running = True
        
        print(f"TCP服务器启动在 {self.host}:{self.port}")
        
        # 启动接受连接的线程
        threading.Thread(target=self._accept_connections, daemon=True).start()
    
    def _accept_connections(self):
        """接受客户端连接"""
        while self.is_running:
            try:
                self.client_socket, self.client_address = self.server_socket.accept()
                print(f"新的客户端连接: {self.client_address}")
            except:
                if self.is_running:
                    print("接受连接时发生错误")
    
    def send_command(self, command):
        """发送命令到客户端"""
        if self.client_socket:
            try:
                # 确保命令是JSON格式
                if isinstance(command, dict):
                    command = json.dumps(command)
                # 添加换行符
                command = command + '\n'
                self.client_socket.send(command.encode())
                print(f"发送命令: {command.strip()}")
                return True
            except Exception as e:
                print(f"发送命令时发生错误: {e}")
                return False
        else:
            print("没有活动的客户端连接")
            return False
    
    def stop(self):
        """停止服务器"""
        self.is_running = False
        if self.client_socket:
            self.client_socket.close()
        if self.server_socket:
            self.server_socket.close()
        print("TCP服务器已停止")

# 测试代码
if __name__ == "__main__":
    server = TCPServer()
    server.start()
    
    try:
        while True:
            # 测试发送命令
            test_command = {
                "command": "F",
                "distance": 100,
                "speed": 20,
                "angle": None
            }
            server.send_command(test_command)
            time.sleep(2)
    except KeyboardInterrupt:
        server.stop() 