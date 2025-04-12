from PyQt5.QtGui import QTextCharFormat, QColor, QFont
from PyQt5.QtWidgets import (QMainWindow, QWidget, QVBoxLayout, QHBoxLayout,
                            QTextEdit, QLabel, QLineEdit, QPushButton, QGroupBox, QSizePolicy)
from PyQt5.QtCore import Qt, QTimer, QFile, QByteArray, QDateTime
from PyQt5.QtGui import QImage, QPixmap
from PyQt5.QtSvg import QSvgWidget

class MainWindow(QMainWindow):
    def __init__(self, controller, tcp_server):
        super().__init__()
        self.controller = controller
        self.tcp_server = tcp_server
        self.setWindowTitle("智能小车控制台")
        self._init_ui()
        self._setup_camera()

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
        
        # 设置定时器更新状态
        self.status_timer = QTimer()
        self.status_timer.timeout.connect(self._update_status)
        self.status_timer.start(1000)  # 每秒更新一次

    def _create_response_panel(self):
        panel = QGroupBox("响应显示")
        layout = QVBoxLayout()
        
        self.response_text = QTextEdit()
        self.response_text.setReadOnly(True)
        layout.addWidget(self.response_text)
        
        self.input_line = QLineEdit()
        self.input_line.setPlaceholderText("输入指令...")
        self.input_line.returnPressed.connect(self._handle_input)
        layout.addWidget(self.input_line)
        
        panel.setLayout(layout)
        return panel

    def _create_control_panel(self):
        panel = QGroupBox("控制面板")
        layout = QVBoxLayout()
        
        # 添加控制按钮
        buttons_layout = QHBoxLayout()
        
        self.forward_btn = QPushButton("前进")
        self.backward_btn = QPushButton("后退")
        self.left_btn = QPushButton("左转")
        self.right_btn = QPushButton("右转")
        self.stop_btn = QPushButton("停止")
        
        self.forward_btn.clicked.connect(lambda: self._send_command("前进"))
        self.backward_btn.clicked.connect(lambda: self._send_command("后退"))
        self.left_btn.clicked.connect(lambda: self._send_command("左转"))
        self.right_btn.clicked.connect(lambda: self._send_command("右转"))
        self.stop_btn.clicked.connect(lambda: self._send_command("停止"))
        
        buttons_layout.addWidget(self.forward_btn)
        buttons_layout.addWidget(self.backward_btn)
        buttons_layout.addWidget(self.left_btn)
        buttons_layout.addWidget(self.right_btn)
        buttons_layout.addWidget(self.stop_btn)
        
        layout.addLayout(buttons_layout)
        panel.setLayout(layout)
        return panel

    def _create_status_panel(self):
        panel = QGroupBox("状态显示")
        layout = QVBoxLayout()
        
        self.position_label = QLabel("位置: 静止")
        self.speed_label = QLabel("速度: 0")
        self.direction_label = QLabel("方向: 正前方")
        self.distance_label = QLabel("距离: --")
        self.battery_label = QLabel("电量: 100%")
        
        layout.addWidget(self.position_label)
        layout.addWidget(self.speed_label)
        layout.addWidget(self.direction_label)
        layout.addWidget(self.distance_label)
        layout.addWidget(self.battery_label)
        
        panel.setLayout(layout)
        return panel

    def _handle_input(self):
        user_input = self.input_line.text()
        self.input_line.clear()
        self._send_command(user_input)

    def _send_command(self, command):
        # 处理用户输入
        json_command = self.controller.process_command(command)
        
        if json_command:
            # 发送命令到TCP服务器
            self.tcp_server.send_command(json_command)
            
            # 更新UI响应
            self.response_text.append(f"用户: {command}")
            self.response_text.append(f"系统: 已发送命令 {json_command}")
            
            # 更新状态
            self._update_status()

    def _update_status(self):
        state = self.controller.car_state
        self.position_label.setText(f"位置: {state['position']}")
        self.speed_label.setText(f"速度: {state['speed']}")
        self.direction_label.setText(f"方向: {state['direction']}")
        self.distance_label.setText(f"距离: {state['distance']}")
        self.battery_label.setText(f"电量: {state['battery']}%")

    def _setup_camera(self):
        # 摄像头设置（如果需要）
        pass

    def update_response(self, data):
        cursor = self.response_text.textCursor()
        
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
        self.response_text.ensureCursorVisible()

    def update_status(self, status):
        """更新所有状态信息"""
        self.direction_label.setText(status.get('direction', '停止'))
        self.speed_label.setText(f"{status.get('speed', 0)} m/s")
        self.distance_label.setText(f"{status.get('distance', 0)} cm")
        self.battery_label.setText(f"{status.get('battery', 100)}%")

    def update_function_calls(self, commands):
        self.function_log.clear()
        first_line = commands.split('\n')[0] if '\n' in commands else commands
        formatted_commands = first_line.replace('+', ';\n')
        
        # 检查是否包含特定关键词
        if "【问答模式】" not in formatted_commands and "【教学模式】" not in formatted_commands:
            self.function_log.append(formatted_commands)
        # 如果包含则不做任何操作（不添加到function_log中）
        