from vosk import Model, KaldiRecognizer
import pyaudio
import json  # 添加json模块导入

# 加载模型
model = Model("model/vosk-model-small-cn-0.22")  # 确保路径正确
recognizer = KaldiRecognizer(model, 16000)  # 16kHz采样率

# 打开麦克风
p = pyaudio.PyAudio()
stream = p.open(
    format=pyaudio.paInt16,
    channels=1,
    rate=16000,
    input=True,
    frames_per_buffer=4096
)

print("请开始说话...（按Ctrl+C停止）")
try:
    while True:
        data = stream.read(4096)
        if recognizer.AcceptWaveform(data):
            result = json.loads(recognizer.Result())  # 使用json解析结果
            print("识别结果:", result["text"])
except KeyboardInterrupt:
    print("\n程序终止")
finally:
    # 释放资源
    stream.stop_stream()
    stream.close()
    p.terminate()