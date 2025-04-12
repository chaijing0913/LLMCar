import socket
import numpy as np
import cv2
from PyQt5.QtCore import QObject, pyqtSignal
from threading import Thread

class CameraServer(QObject):
    new_frame = pyqtSignal(np.ndarray)  # 需要导入numpy
    
    def __init__(self, host='172.20.10.3', port=8080):
        super().__init__()
        self.host = host
        self.port = port
        self.running = False
        
    def start_server(self):
        self.running = True
        self.thread = Thread(target=self._run_server, daemon=True)
        self.thread.start()
        
    def _run_server(self):
        s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        s.bind((self.host, self.port))
        
        end_data = b'Frame Over'
        temp_data = b''
        
        while self.running:
            try:
                data, _ = s.recvfrom(1430)
                if data == end_data:
                    if temp_data:
                        self._process_frame(temp_data)
                    temp_data = b''
                else:
                    temp_data += data
            except Exception as e:
                print(f"接收错误: {e}")
                break
                
        s.close()
        
    def _process_frame(self, frame_data):
        try:
            img_data = np.frombuffer(frame_data, dtype=np.uint8)
            frame = cv2.imdecode(img_data, cv2.IMREAD_COLOR)
            if frame is not None:
                frame = cv2.resize(frame, (200, 150))
                self.new_frame.emit(frame)
        except Exception as e:
            print(f"帧处理错误: {e}")
            
    def stop_server(self):
        self.running = False
        if hasattr(self, 'thread'):
            self.thread.join()

            