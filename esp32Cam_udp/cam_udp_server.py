import socket #用于网络通信
import numpy as np #处理图像数据
import cv2 # OpenCV 图像处理和显示
import time #计算帧率
 
# 创建UDP服务器
s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)#创建套接字，IPv地址族和UDP协议
# 注意 这里是服务器的IP和端口  不是客户端的
addr = ('172.20.10.3', 8080)
# 在云服务器上开启服务要使用内网的IP  腾讯云的地址
# addr = ('10.0.4.11', 8001)
s.bind(addr)#绑定套接字和端口
#定义结束标记和数据缓冲区
end_data = b'Frame Over'#ESP32发送的帧结束标记
temp_data = b''#临时存储接收到的图像数据
#ESP32 Cam 返回数据格式
#b'(\xa0\x04\xa2\x98\x05%\x16\x00\xa4'  这个以及上面的都是图片数据
# b'\r\n'  返回的分隔符和回车 回车是自己写的代码（udp.println();  ）  \r\n 长度为2  测试加在图片数据不影响显示
# b'Frame Over' 返回的结束符  用于判断是否一张图片结束  udp.print("Frame Over");
# UDP会发送单独的一个包   但是TCP不会单独发送 会和其他混在一起 这边TCP和UDP处理方式不一样
millis1 = int(round(time.time() * 1000))#记录初始时间，用于计算
while True:
    data, addr= s.recvfrom(1430)
    if data == end_data: # 判断这一帧数据是不是结束语句 UDP会发送单独的一个包   但是TCP不会单独发送
        # print(temp_data) temp_data数据多了 b'\r\n' 但是不影响图片的显示
        # 显示图片
        receive_data = np.frombuffer(temp_data, dtype='uint8')  # 将获取到的字符流数据转换成1维数组
        r_img = cv2.imdecode(receive_data, cv2.IMREAD_COLOR)  # 将数组解码成图像
        r_img = r_img.reshape(480, 640, 3)
        millis2 = int(round(time.time() * 1000))
        millis = millis2 -millis1
        fps = (1000//millis)
        cv2.putText(r_img, "FPS:" + str(fps), (50, 50), cv2.FONT_HERSHEY_SIMPLEX, 1, (255, 0, 0), 2)
        cv2.imshow('server_frame', r_img)
        if cv2.waitKey(1) & 0xFF == ord('q'):
            break
        print("接收到的数据包：" + str(len(temp_data)))  # 显示该张照片数据大小
        temp_data = b''  # 清空数据 便于下一章照片使用
        millis1 = millis2
    else:
        temp_data = temp_data + data  # 不是结束的包 讲数据添加进temp_data