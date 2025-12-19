import os
import google.generativeai as genai

# 1. 设置代理 (跟你 server.py 里一样)
os.environ["HTTP_PROXY"] = "http://127.0.0.1:20171"
os.environ["HTTPS_PROXY"] = "http://127.0.0.1:20171"

# 2. 这里填你的 API KEY
# 如果你之前放在环境变量里了，也可以用 os.getenv('GEMINI_API_KEY')
api_key = os.getenv('GEMINI_API_KEY')

genai.configure(api_key=api_key)

print("正在连接 Google 查询可用模型...")
try:
    count = 0
    for m in genai.list_models():
        # 我们只关心能生成内容 (generateContent) 的模型
        if 'generateContent' in m.supported_generation_methods:
            print(f"✅ 可用模型: {m.name}")
            count += 1
    
    if count == 0:
        print("⚠️ 连接成功，但没有发现可用模型。请检查你的 API Key 权限或 v2ray 节点地区（不要用香港节点）。")
        
except Exception as e:
    print(f"❌ 连接失败: {e}")