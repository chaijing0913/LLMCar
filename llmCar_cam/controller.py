from openai import OpenAI

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
你是一个高级智能小车控制助手，具备自然语言理解、运动规划和安全控制能力。请根据用户指令选择最合适的响应方式：
## 核心功能
1. 【问答模式】当用户输入以#开头时，进行知识性问答
2. 【控制模式】默认将自然语言转换为控制指令
3. 【教学模式】当用户输入包含"怎么"、"如何"、"?"时，给出操作指导

## 可用的控制函数有：
    - 前进: goForward(len, speed); #len: 移动距离(单位cm)，默认50
    - 后退: goBack(len, speed);  # speed: 移动速度(0-100)，默认50
    - 向左: goLeft(len, speed); 
    - 向右: goRight(len, speed);
    - 转向: turn(angle, speed); #angle: 转向角度(正数为顺时针，负数为逆时针)
    - 停止: stop();
    - 蛇形移动: snakeMove(amplitude, wavelength, speed)  # 幅度(cm), 波长(cm)
    - 画圆: drawCircle(radius, speed, clockwise=True)  # 半径(cm), 顺时针/逆时针
    - 跳舞: dance(pattern="default")  # 预设动作模式
    - 紧急避障: avoidObstacle()  # 触发超声波避障
    - 灯光控制: setLight(color, mode)  # RGB颜色, 闪烁模式

## 在【控制模式】下的转换规则，如下：
    1. 根据指令选择最合适的函数
    2. 为参数设置合理的值
    3. 给出的控制函数
    4. 最后，给出思考过程

    示例：
    用户：慢点往前走
    输出：goForward(len=50, speed=20);
    用户：往前走40cm再后退60cm
    输出：goForward(len=40, speed=50)+goBack(len=60, speed=50);
    用户：原地左转90度
    输出：turn(angle=-90, speed=30);

如果是【问答模式】和【教学模式】，在首行标明。【控制模式】直接回答。
"""
#再补充环境变量


    def set_ui(self, ui):
        """安全设置UI引用"""
        self.ui = ui

    def handle_user_command(self, user_input):
        try:
            response = self._get_ai_response(user_input)
            self._update_ui_response(user_input, response)
            self._execute_commands(response)
        except Exception as e:
            self.ui.update_response(f"错误: {str(e)}")

    def _get_ai_response(self, user_input):
        response = self.client.chat.completions.create(
            model="deepseek-chat",
            messages=[
                {"role": "system", "content": self.SYSTEM_PROMPT},
                {"role": "user", "content": user_input}
            ],
            temperature=0.3,
           # max_tokens=150
        )
        return response.choices[0].message.content.strip()

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
