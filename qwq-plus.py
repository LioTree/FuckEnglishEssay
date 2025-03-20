import os
from openai import OpenAI
from PIL import Image
import io
import markdown2
import webbrowser
import tempfile
import base64
import sys

api_key = os.environ.get('QWEN_API_KEY')

# 检查 API Key 是否成功读取
if not api_key:
    print("错误：未找到环境变量 QWEN_API_KEY。请确保已设置该环境变量。")
    exit()

# 配置 OpenAI 客户端连接到阿里云千问服务
client = OpenAI(
    api_key=api_key,
    base_url="https://dashscope.aliyuncs.com/compatible-mode/v1"
)

# OCR识别的prompt
ocr_prompt = """请提取图片中的英语作文文本，原样输出所有文字内容，不要做任何修改或评价。如果有涂改，请尽量识别出原始文本和涂改后的文本。"""

# 英语作文批改的prompt
correction_prompt = """你是一名初中英语老师，现有一篇英语作文需要你批改（要注意文章中可能的涂改）, 你需要找出文章中所有的拼写错误，用词不当以及语法错误。首先你需要输出原作文（主要不要使用markdown的```进行包裹，而是直接输出）以及批改过的作文。然后你需要将作文拆成一个一个句子，逐个句子给出批改的结果以及修正后的句子，如果没有错误则输出该句子没有问题。并在总结整篇作文的主要问题，比如时态问题，语法问题。评价用中文给出
。"""

# 读取图片文件
try:
    image_path = "images/test3.jpg"
    image = Image.open(image_path)
    
    # 将图片转换为base64编码
    image_bytes = io.BytesIO()
    image.save(image_bytes, format=image.format) # 保持原始图片格式
    base64_image = base64.b64encode(image_bytes.getvalue()).decode('utf-8')
    
    # 确定MIME类型
    image_mime_type = f"image/{image.format.lower()}" if image.format else "image/jpeg"
    
except FileNotFoundError:
    print(f"错误：图片文件 {image_path} 未找到，请检查路径是否正确。")
    exit()
except Exception as e:
    print(f"读取图片时发生错误: {e}")
    exit()

try:
    # 步骤1: 使用千问视觉模型进行OCR识别
    print("步骤1: 正在使用千问视觉模型进行OCR识别...\n")
    
    ocr_messages = [
        {"role": "system", "content": "You are a helpful assistant."},
        {"role": "user", "content": [
            {"type": "text", "text": ocr_prompt},
            {"type": "image_url", 
             "image_url": {
                 "url": f"data:{image_mime_type};base64,{base64_image}"
             }}
        ]}
    ]
    
    ocr_response = client.chat.completions.create(
        model="qwen-vl-max-latest",
        messages=ocr_messages,
        stream=True
    )
    
    # 收集OCR识别的文本
    extracted_text = ""
    print("识别到的作文原文:\n")
    
    for chunk in ocr_response:
        if chunk.choices and chunk.choices[0].delta.content:
            content = chunk.choices[0].delta.content
            print(content, end='', flush=True)
            extracted_text += content
    
    print("\n\nOCR识别完成！")
    
    # 步骤2: 使用千问语言模型进行作文批改
    print("\n步骤2: 正在使用千问语言模型进行作文批改...\n")
    
    correction_messages = [
        {"role": "system", "content": "You are a helpful assistant."},
        {"role": "user", "content": f"{correction_prompt}\n\n作文内容：\n{extracted_text}"}
    ]
    
    correction_response = client.chat.completions.create(
        model="qwq-plus-latest",
        messages=correction_messages,
        stream=True
    )
    
    # 收集批改结果
    full_response = ""
    print("批改结果:\n")
    
    for chunk in correction_response:
        if chunk.choices and chunk.choices[0].delta.content:
            content = chunk.choices[0].delta.content
            print(content, end='', flush=True)
            full_response += content
    
    # 打印完成后换行
    print("\n\n批改完成！")
    
    # 将Markdown转换为HTML
    html_content = f"""
    <!DOCTYPE html>
    <html>
    <head>
        <meta charset="UTF-8">
        <title>作文批改结果 (千问)</title>
        <style>
            body {{
                font-family: Arial, sans-serif;
                line-height: 1.6;
                max-width: 800px;
                margin: 0 auto;
                padding: 20px;
            }}
            h1, h2, h3 {{
                color: #2c3e50;
            }}
            code {{
                background-color: #f5f5f5;
                padding: 2px 4px;
                border-radius: 4px;
            }}
            pre {{
                background-color: #f5f5f5;
                padding: 10px;
                border-radius: 4px;
                overflow-x: auto;
            }}
            blockquote {{
                border-left: 4px solid #ccc;
                padding-left: 15px;
                color: #555;
            }}
            .ocr-result, .correction-result {{
                margin-top: 20px;
                margin-bottom: 20px;
                padding: 15px;
                border: 1px solid #ddd;
                border-radius: 5px;
            }}
            .ocr-result {{
                background-color: #f9f9f9;
            }}
            .correction-result {{
                background-color: #f0f7ff;
            }}
        </style>
    </head>
    <body>
        <h1>英语作文批改结果 (千问模型)</h1>
        
        <div class="ocr-result">
            <h2>OCR识别结果 (qwen-vl-max-latest)</h2>
            <pre>{extracted_text}</pre>
        </div>
        
        <div class="correction-result">
            <h2>作文批改 (qwen-plus-latest)</h2>
            {markdown2.markdown(full_response, extras=["fenced-code-blocks", "tables", "break-on-newline"])}
        </div>
    </body>
    </html>
    """
    
    # 创建临时HTML文件
    with tempfile.NamedTemporaryFile('w', delete=False, suffix='.html', encoding='utf-8') as f:
        f.write(html_content)
        temp_html_path = f.name
    
    # 在浏览器中打开结果
    webbrowser.open('file://' + temp_html_path)
    
    print("作文批改结果已在浏览器中打开")

except Exception as e:
    print(f"调用模型时发生错误: {e}")
    print("请检查是否正确配置了 QWEN_API_KEY，以及网络连接是否正常。")