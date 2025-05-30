import os
os.environ['QT_QPA_PLATFORM_PLUGIN_PATH'] = r'C:\Users\别秋\AppData\Roaming\Python\Python312\site-packages\PyQt5\Qt5\plugins'

import sys
from PyQt5.QtWidgets import QApplication
from controller import CarController
from qt_ui import MainWindow

def main():
    app = QApplication(sys.argv)
    
    # 初始化控制器和UI
    controller = CarController()
    window = MainWindow(controller)
    controller.set_ui(window)  # 安全设置UI引用
    
    # 启动
    window.show()
    sys.exit(app.exec_())

if __name__ == "__main__":
    main()