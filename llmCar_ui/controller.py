from openai import OpenAI
import json

class CarController:
    def __init__(self):
        self.client = OpenAI(
            api_key="",
            base_url="https://api.deepseek.com"
        )
        self.ui = None  # 将被MainWindow实例填充
        self.car_state = {
            "position": "静止",
            "speed": 0,
            "direction": "正前方",
            "distance": "--",
            "battery": 100
        }
        
        self.SYSTEM_PROMPT = """
# 角色设定
你是一个高级智能小车控制助手，具备自然语言理解、运动规划和安全控制能力。请根据用户指令生成JSON格式的控制命令。

## 命令格式
所有命令必须以JSON格式返回，格式如下：
{
    "command": "F/B/L/R",  # F:前进, B:后退, L:左转, R:右转
    "distance": 数字,      # 移动距离(单位cm)，默认50
    "speed": 数字,         # 移动速度(0-100)，默认50
    "angle": 数字/null     # 转向角度(0-360)，null表示直行
}

## 响应规则
1. 只返回JSON格式的命令，不要包含其他文字
2. 距离和速度必须是非负整数
3. 角度必须是0-360之间的整数或null
4. 如果用户输入不明确，使用默认值
"""
#再补充环境变量


    def set_ui(self, ui):
        """安全设置UI引用"""
        self.ui = ui

    def handle_user_command(self, user_input):
        try:
            response = self.client.chat.completions.create(
                model="deepseek-chat",
                messages=[
                    {"role": "system", "content": self.SYSTEM_PROMPT},
                    {"role": "user", "content": user_input}
                ],
                temperature=0.7,
                max_tokens=150
            )
            
            # 解析响应为JSON
            command = json.loads(response.choices[0].message.content)
            
            # 更新小车状态
            self._update_car_state(command)
            
            return command
            
        except Exception as e:
            print(f"处理命令时发生错误: {e}")
            return None

    def _update_car_state(self, command):
        """更新小车状态"""
        if command:
            # 更新方向
            direction_map = {
                "F": "正前方",
                "B": "正后方",
                "L": "左侧",
                "R": "右侧"
            }
            self.car_state["direction"] = direction_map.get(command["command"], "正前方")
            
            # 更新速度
            self.car_state["speed"] = command.get("speed", 0)
            
            # 更新位置
            if command["command"] in ["F", "B"]:
                self.car_state["position"] = "移动中"
            else:
                self.car_state["position"] = "转向中"
            
            # 更新距离
            self.car_state["distance"] = command.get("distance", "--")
    
    def _update_ui_response(self, user_input, ai_response):
        if self.ui:
            self.ui.update_response({
                "user_input": user_input,
                "ai_response": ai_response
            })

    def _execute_commands(self, commands):
        # 解析命令更新状态
        if "goForward" in commands:
            self.car_state.update({
                "position": "前进", 
                "speed": 50,
                "direction": "正前方"
            })
        
        # 更新UI
        if self.ui:
            self.ui.update_function_calls(commands)
            self.ui.update_status(self.car_state)
