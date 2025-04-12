from PyQt5.QtGui import QTextCharFormat, QColor, QFont,QImage, QPixmap
from PyQt5.QtWidgets import (QMainWindow, QWidget, QVBoxLayout, QHBoxLayout,
                            QTextEdit, QLabel, QLineEdit, QPushButton, QGroupBox, QSizePolicy)
from PyQt5.QtCore import Qt, QTimer, QFile, QByteArray, QDateTime,pyqtSlot
import cv2
import numpy as np
from PyQt5.QtSvg import QSvgWidget
from camera_server import CameraServer

class MainWindow(QMainWindow):
    def __init__(self, controller):
        super().__init__()
        self.controller = controller
        self.setWindowTitle("智能小车控制台")
        self._init_ui()
        self._setup_camera_stream()

    def _setup_camera_stream(self):
        # 创建摄像头服务器
        self.camera_server = CameraServer()
        self.camera_server.new_frame.connect(self._update_camera_display)
        self.camera_server.start_server()

    def _init_ui(self):
        # 主布局
        central_widget = QWidget()
        layout = QHBoxLayout()
        
        # 左侧：响应显示
        self.response_panel = self._create_response_panel()
        layout.addWidget(self.response_panel)
        
        # 中间：摄像头和控制
        self.control_panel = self._create_control_panel()
        layout.addWidget(self.control_panel)
        
        # 右侧：状态显示
        self.status_panel = self._create_status_panel()
        layout.addWidget(self.status_panel)
        
        central_widget.setLayout(layout)
        self.setCentralWidget(central_widget)

    def _create_response_panel(self):
        panel = QGroupBox("大语言模型响应")
        panel.setMinimumWidth(350)
        self.response_display = QTextEdit()
        self.response_display.setReadOnly(True)
        
        layout = QVBoxLayout()
        layout.addWidget(self.response_display)
        panel.setLayout(layout)
        return panel

    def _create_control_panel(self):
        panel = QGroupBox("控制中心")
        panel.setSizePolicy(QSizePolicy.Fixed, QSizePolicy.Expanding)
        
        layout = QVBoxLayout()
        layout.setAlignment(Qt.AlignHCenter)
        
        # 摄像头区域
        self.camera_display = QLabel()
        self.camera_display.setAlignment(Qt.AlignCenter)
        self.camera_display.setStyleSheet("background: black")
        self.camera_display.setFixedSize(200, 150)
        
        # 输入区域
        input_container = QWidget()
        input_layout = QVBoxLayout(input_container)
        input_layout.setContentsMargins(0, 0, 0, 0)
        input_layout.setSpacing(0)
        
        self.cmd_input = QTextEdit()
        self.cmd_input.setPlaceholderText("输入控制指令...")
        self.cmd_input.setFixedHeight(200)
        self.cmd_input.setMinimumWidth(200)
        
        input_layout.addWidget(QLabel("<b>用户输入：</b>"))
        input_layout.addWidget(self.cmd_input)

        # 发送按钮
        self.send_btn = QPushButton("发送")
        self.send_btn.setFixedSize(250, 40)
        self.send_btn.setStyleSheet("""
            QPushButton {
                background-color: #b7e4c7;
                font-weight: bold;
                border: 1px solid #80c080;
                border-radius: 4px;
                padding: 5px;
            }
            QPushButton:hover {
                background-color: #90d690;
            }
            QPushButton:pressed {
                background-color: #70b070;
            }
        """)
        self.send_btn.clicked.connect(self._send_command)
        
        layout.addWidget(self.camera_display, alignment=Qt.AlignCenter)
        layout.addWidget(input_container)
        layout.addWidget(self.send_btn)
        layout.setSpacing(15)
        
        panel.setLayout(layout)
        return panel

    def _create_status_panel(self):
        panel = QGroupBox("小车状态")
        layout = QVBoxLayout()
        layout.setSpacing(10)
        
        # 1. 小车SVG图标
        svg_container = QWidget()
        svg_layout = QHBoxLayout(svg_container)
        svg_layout.setContentsMargins(0, 0, 0, 0)
        
        self.car_svg = QSvgWidget()
        self.car_svg.setFixedSize(80, 80)
        svg_file = QFile("car.svg")
        if svg_file.open(QFile.ReadOnly | QFile.Text):
            svg_data = QByteArray(svg_file.readAll())
            self.car_svg.load(svg_data)
            svg_file.close()
        
        svg_layout.addWidget(self.car_svg, alignment=Qt.AlignCenter)
        layout.addWidget(svg_container)
        
        # 2. 状态信息行
        self._create_status_row(layout, "./res/calendar.png", "日期", self._get_current_datetime())
        self._create_status_row(layout, "direction.png", "方向", "停止")
        self._create_status_row(layout, "speed.png", "速度", "0 m/s")
        self._create_status_row(layout, "object.png", "物体距离", "0 cm")
        #self._create_status_row(layout, "temperature.png", "温度", "25 ℃")
        
       # 3. 函数调用记录（完全紧贴布局）
        function_container = QWidget()
        function_layout = QVBoxLayout(function_container)
        function_layout.setContentsMargins(0, 0, 0, 0)  # 移除容器所有边距
        function_layout.setSpacing(0)  # 移除内部所有间距

        # 标签（移除所有边距）
        function_label = QLabel("<b>调用函数：</b>")

        # 文本框（移除所有边距和边框）
        self.function_log = QTextEdit()
        self.function_log.setFixedHeight(150)
        self.function_log.setFixedWidth(270)
        self.function_log.setReadOnly(True)

        # 添加控件（将紧贴在一起）
        function_layout.addWidget(function_label)
        function_layout.addWidget(self.function_log)

        # 添加到主布局
        layout.addWidget(function_container)

        # 设置定时器更新日期时间
        self.datetime_timer = QTimer(self)
        self.datetime_timer.timeout.connect(self._update_datetime)
        self.datetime_timer.start(60000)  # 每分钟更新一次
        
        panel.setLayout(layout)
        return panel

    def _create_status_row(self, layout, icon_path, label_text, value_text):
        """创建状态信息行（图标+标签+值）"""
        row = QWidget()
        row_layout = QHBoxLayout(row)
        row_layout.setContentsMargins(2, 2, 2, 2)
        row_layout.setSpacing(8);
        # 图标
        icon_label = QLabel()
        pixmap = QPixmap(icon_path)
        if not pixmap.isNull():
            pixmap = pixmap.scaled(24, 24, Qt.KeepAspectRatio, Qt.SmoothTransformation)
            icon_label.setPixmap(pixmap)
        row_layout.addWidget(icon_label)
        
        # 标签
        label = QLabel(label_text + ":")
        label.setStyleSheet("font-weight: bold; min-width: 50px;")
        row_layout.addWidget(label)
        
        # 值
        value_label = QLabel(value_text)
        value_label.setStyleSheet("""
            QLabel {
                background: #f5f5f5;
                border-radius: 3px;
                padding: 1px 5px;
                min-width: 70px;
            }
        """)
        row_layout.addWidget(value_label, stretch=1)
        
        # 保存引用以便后续更新
        if label_text == "日期":
            self.datetime_label = value_label
        elif label_text == "方向":
            self.direction_label = value_label
        elif label_text == "速度":
            self.speed_value_label = value_label
        elif label_text == "物体距离":
            self.distance_label = value_label
        # elif label_text == "温度":
        #     self.temp_label = value_label
        
        layout.addWidget(row)

    def _get_current_datetime(self):
        """获取当前日期时间（精确到分钟）"""
        return QDateTime.currentDateTime().toString("yyyy-MM-dd HH:mm")

    def _update_datetime(self):
        """更新日期时间显示"""
        self.datetime_label.setText(self._get_current_datetime())

    
    @pyqtSlot(np.ndarray)
    def _update_camera_display(self, frame):
        """更新摄像头显示"""
        try:
            # 转换颜色空间 BGR -> RGB
            rgb_image = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
            
            # 转换为QPixmap
            h, w, ch = rgb_image.shape
            bytes_per_line = ch * w
            q_img = QImage(rgb_image.data, w, h, bytes_per_line, QImage.Format_RGB888)
            pixmap = QPixmap.fromImage(q_img)
            
            # 更新显示
            self.camera_display.setPixmap(pixmap)
            
        except Exception as e:
            print(f"更新摄像头显示错误: {e}")
        
    def closeEvent(self, event):
        """窗口关闭时停止摄像头服务"""
        self.camera_server.stop_server()
        super().closeEvent(event)

    def _send_command(self):
        cmd = self.cmd_input.toPlainText().strip()
        if cmd:
            self.controller.handle_user_command(cmd)
            self.cmd_input.clear()

    def update_response(self, data):
        cursor = self.response_display.textCursor()
        
        fmt_title = QTextCharFormat()
        fmt_title.setFontWeight(QFont.Bold)
        cursor.insertText("用户输入:\n", fmt_title)
        
        fmt_user = QTextCharFormat()
        fmt_user.setForeground(QColor(100, 100, 100))
        cursor.insertText(f"{data['user_input']}\n\n", fmt_user)
        
        fmt_ai_title = QTextCharFormat()
        fmt_ai_title.setFontWeight(QFont.Bold)
        fmt_ai_title.setForeground(QColor(0, 102, 204))
        cursor.insertText("llm智能车助手:\n", fmt_ai_title)
        
        fmt_ai = QTextCharFormat()
        color = QColor(0, 0, 0)
        color.setAlphaF(0.7)
        fmt_ai.setForeground(color)
        cursor.insertText(f"{data['ai_response']}\n", fmt_ai)
        
        cursor.insertText("\n" + "="*30 + "\n")
        self.response_display.ensureCursorVisible()

    def update_status(self, status):
        """更新所有状态信息"""
        self.direction_label.setText(status.get('direction', '停止'))
        self.speed_value_label.setText(f"{status.get('speed', 0)} m/s")
        self.distance_label.setText(f"{status.get('distance', 0)} cm")
        #self.temp_label.setText(f"{status.get('temperature', 25)} ℃")

    # def update_function_calls(self, commands):
    #     self.function_log.clear()
    #     first_line = commands.split('\n')[0] if '\n' in commands else commands
    #     formatted_commands = first_line.replace('+', ';\n')
    #     self.function_log.append(formatted_commands)

    def update_function_calls(self, commands):
        self.function_log.clear()
        first_line = commands.split('\n')[0] if '\n' in commands else commands
        formatted_commands = first_line.replace('+', ';\n')
        
        # 检查是否包含特定关键词
        if "【问答模式】" not in formatted_commands and "【教学模式】" not in formatted_commands:
            self.function_log.append(formatted_commands)
        # 如果包含则不做任何操作（不添加到function_log中）