from flask import Flask, request, jsonify
import requests
import os
import re

app = Flask(__name__)

# DeepSeek配置 - 从环境变量读取
AI_API_KEY = os.environ.get('DEEPSEEK_API_KEY')
AI_BASE_URL = "https://api.deepseek.com/v1/chat/completions"

SENSITIVE_WORDS = ["政治", "政府", "领导人", "宗教", "色情", "成人"]


class EnglishTutorBot:
    def __init__(self):
        self.system_prompt = """
        你是一个耐心、友好的英语老师，专门教零基础中国成年人学习英语。

        教学原则：
        1. 只用简单英语回复，句子不超过8个单词
        2. 每次只教1-2个新单词
        3. 多用鼓励性语言：Good job! Excellent! Well done!
        4. 如果学生说中文，用简单英语回复并鼓励他们说英语
        5. 绝对不讨论政治、宗教、色情等敏感话题
        6. 专注于日常生活场景：吃饭、工作、家庭、购物等
        """

    def is_safe_content(self, text):
        """检查内容安全性"""
        text_lower = text.lower()

        # 检查敏感词
        for word in SENSITIVE_WORDS:
            if word in text_lower:
                return "I can't discuss this topic. Let's learn English!"

        return True

    def generate_reply(self, user_message):
        """生成英语学习回复"""
        # 1. 安全检查
        safety_check = self.is_safe_content(user_message)
        if safety_check is not True:
            return safety_check

        # 2. 调用DeepSeek AI
        try:
            headers = {
                "Authorization": f"Bearer {AI_API_KEY}",
                "Content-Type": "application/json"
            }

            data = {
                "model": "deepseek-chat",
                "messages": [
                    {"role": "system", "content": self.system_prompt},
                    {"role": "user", "content": user_message}
                ],
                "max_tokens": 50,
                "temperature": 0.7
            }

            response = requests.post(AI_BASE_URL, json=data, headers=headers, timeout=10)
            result = response.json()

            if 'choices' in result and len(result['choices']) > 0:
                return result['choices'][0]['message']['content']
            else:
                return "Let's try again! Say something in English."

        except Exception as e:
            print(f"API调用错误: {e}")
            return "I'm learning too! Try again with simple English."


# 初始化机器人
bot = EnglishTutorBot()


@app.route('/wechat/webhook', methods=['POST'])
def wechat_webhook():
    """微信回调接口"""
    try:
        data = request.get_json()
        print("收到请求:", data)  # 调试用

        # 解析用户消息
        user_message = data.get('text', '').strip()
        if not user_message:
            user_message = data.get('Content', '').strip()

        # 忽略空消息
        if not user_message:
            return jsonify({"msgtype": "text", "text": {"content": "Please say something in English!"}})

        # 生成回复
        bot_reply = bot.generate_reply(user_message)

        print("机器人回复:", bot_reply)

        # 返回给微信
        return jsonify({
            "msgtype": "text",
            "text": {
                "content": bot_reply
            }
        })

    except Exception as e:
        print("错误:", e)
        return jsonify({"msgtype": "text", "text": {"content": "System busy, try again later."}})


# 测试接口
@app.route('/test', methods=['GET'])
def test_bot():
    """测试机器人是否正常工作"""
    test_message = "hello"
    reply = bot.generate_reply(test_message)
    return f"测试消息: {test_message}<br>机器人回复: {reply}"


@app.route('/')
def home():
    return "英语学习机器人服务正常运行中！"


if __name__ == '__main__':
    port = int(os.environ.get('PORT', 10000))
    app.run(host='0.0.0.0', port=port, debug=False)
