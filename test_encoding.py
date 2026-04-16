import requests
import json

# 测试中文输入
message = "五一出游穿搭"
print(f"发送的消息: {message}")
print(f"消息类型: {type(message)}")

# 发送请求
url = "http://localhost:8000/api/chat/"
data = {"message": message, "user_id": "default"}
headers = {"Content-Type": "application/json"}

response = requests.post(url, json=data, headers=headers)

print(f"响应状态码: {response.status_code}")
print(f"响应内容: {response.json()}")