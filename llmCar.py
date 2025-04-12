import json
from openai import OpenAI

# 初始化OpenAI客户端
client = OpenAI(api_key="sk-a77d4065756a4c5da8b94281a63c26d1", base_url="https://api.deepseek.com")

# 系统提示词，设定AI的角色和能力
SYSTEM_PROMPT = """
你是一个智能小车命令生成助手，负责将自然语言指令转换为具体的控制函数调用。

可用的控制函数有：
- 前进: goForward(len, speed); 
- 后退: goBack(len, speed); 
- 向左: goLeft(len, speed); 
- 向右: goRight(len, speed);
- 转向: turn(angle, speed);
- 停止: stop();

参数说明：
- len: 移动距离(单位cm)，默认50
- speed: 移动速度(0-100)，默认50
- angle: 转向角度(正数为顺时针，负数为逆时针)

转换规则：
1. 根据指令选择最合适的函数
2. 为参数设置合理的值
3. 给出所选函数用+连接
4. 做出解释

示例：
用户：慢点往前走
输出：goForward(len=50, speed=20);
用户：往前走40cm再后退60cm
输出：goForward(len=40, speed=50); goBack(len=60, speed=50);
用户：原地左转90度
输出：turn(angle=-90, speed=30);
"""

def get_ai_response(user_input):
    """调用大语言模型获取响应"""
    response = client.chat.completions.create(
        model="deepseek-chat",  
        messages=[
            {"role": "system", "content": SYSTEM_PROMPT},
            {"role": "user", "content": user_input}
        ],
        temperature=0.3,
        max_tokens=150
    )
    return response.choices[0].message.content.strip()

def execute_commands(commands):
    """模拟执行命令（实际项目中这里会调用真正的控制函数）"""
    
    # print("\n执行命令:")
    # for cmd in commands.split(";"):
    #     cmd = cmd.strip()
    #     if cmd:
    #         print(f"> {cmd}")

def main():
    print("智能小车控制程序 (输入'退出'结束)")
    print("--------------------------------")
    
    while True:
        user_input = input("\n请输入指令: ").strip()
        if user_input.lower() in ["退出", "exit", "quit"]:
            break
            
        if not user_input:
            continue
            
        try:
            # 获取AI生成的命令
            ai_response = get_ai_response(user_input)
            print(f"\n生成的命令: {ai_response}")
            
            # 执行命令
            execute_commands(ai_response)
            
        except Exception as e:
            print(f"发生错误: {e}")

if __name__ == "__main__":
    main()
    