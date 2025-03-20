import os
from openai import OpenAI
from PIL import Image
import io
import markdown2
import webbrowser
import tempfile
import base64
import sys
import json
import re

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

# 构建 Prompt (修改为要求JSON输出)
prompt_text = """你是一名初中英语老师，现有一篇英语作文需要你批改（要注意文章中可能的涂改，有些字上仅仅画了一道，但那也是涂改）, 你需要找出文章中所有的拼写错误，用词不当以及语法错误。

请以JSON格式输出你的批改结果，格式如下：
{
  "original_essay": "原始作文内容",
  "corrected_essay": "批改后的作文内容",
  "sentence_corrections": [
    {
      "original": "原句",
      "corrected": "修正后的句子",
      "comments": "对这个句子的评价和解释"
    },
    // 更多句子批改...
  ],
  "overall_comments": "对整篇作文主要问题的总结和评价"
}

评价请用中文给出。确保你的输出是有效的JSON格式，便于自动处理。不要添加任何额外解释或前后缀，直接输出JSON。"""

# 读取图片文件
try:
    image_path = "images/test4.jpg"
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

# 构建消息内容，包含系统提示、用户文本和图片
try:
    messages = [
        {"role": "system", "content": "You are a helpful assistant."},
        {"role": "user", "content": [
            {"type": "text", "text": prompt_text},
            {"type": "image_url", 
             "image_url": {
                 "url": f"data:{image_mime_type};base64,{base64_image}"
             }}
        ]}
    ]
    
    # 调用千问视觉大模型（使用流式输出）
    print("正在获取千问模型响应...\n")
    
    stream_response = client.chat.completions.create(
        model="qwen-vl-max-latest",
        messages=messages,
        response_format={"type": "json_object"},  # 启用JSON模式输出
        stream=True  # 启用流式输出
    )
    
    # 收集完整的响应用于JSON解析
    full_response = ""
    
    # 逐步处理流式响应并打印
    for chunk in stream_response:
        if (chunk.choices and chunk.choices[0].delta.content):
            content = chunk.choices[0].delta.content
            print(content, end='', flush=True)
            full_response += content
    
    # 打印完成后换行
    print("\n\n批改完成！")
    
    # 尝试从响应中提取JSON
    try:
        # 尝试直接解析完整响应
        result_json = json.loads(full_response)
    except json.JSONDecodeError:
        # 如果直接解析失败，尝试使用正则表达式提取JSON部分
        json_match = re.search(r'({[\s\S]*})', full_response)
        if json_match:
            try:
                result_json = json.loads(json_match.group(1))
            except:
                print("无法从响应中提取有效的JSON，将显示原始响应")
                result_json = {
                    "original_essay": "解析失败",
                    "corrected_essay": "解析失败",
                    "sentence_corrections": [],
                    "overall_comments": "无法从模型响应中提取JSON数据，请查看原始输出。"
                }
        else:
            print("无法从响应中找到JSON格式内容")
            result_json = {
                "original_essay": "解析失败",
                "corrected_essay": "解析失败",
                "sentence_corrections": [],
                "overall_comments": "无法从模型响应中提取JSON数据，请查看原始输出。"
            }
    
    # 准备HTML内容
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
            .section {{
                margin-bottom: 20px;
                padding: 15px;
                border: 1px solid #eee;
                border-radius: 5px;
            }}
            .original {{
                background-color: #f9f9f9;
            }}
            .corrected {{
                background-color: #f0f7ff;
            }}
            .sentence-correction {{
                margin-bottom: 15px;
                padding: 10px;
                background-color: #f5f5f5;
                border-left: 3px solid #3498db;
            }}
            .comments {{
                color: #e74c3c;
                font-style: italic;
            }}
            .overall {{
                background-color: #f0fff0;
                font-weight: bold;
            }}
            pre {{
                white-space: pre-wrap;
                word-wrap: break-word;
            }}
        </style>
    </head>
    <body>
        <h1>英语作文批改结果 (千问模型)</h1>
        
        <div class="section original">
            <h2>原始作文</h2>
            <pre>{result_json.get("original_essay", "未提供")}</pre>
        </div>
        
        <div class="section corrected">
            <h2>批改后的作文</h2>
            <pre>{result_json.get("corrected_essay", "未提供")}</pre>
        </div>
        
        <div class="section">
            <h2>逐句批改</h2>
    """
    
    # 添加每个句子的批改
    if "sentence_corrections" in result_json and result_json["sentence_corrections"]:
        for idx, sentence in enumerate(result_json["sentence_corrections"], 1):
            html_content += f"""
            <div class="sentence-correction">
                <h3>句子 {idx}</h3>
                <p><strong>原句:</strong> {sentence.get("original", "")}</p>
                <p><strong>修正:</strong> {sentence.get("corrected", "")}</p>
                <p class="comments"><strong>评注:</strong> {sentence.get("comments", "")}</p>
            </div>
            """
    else:
        html_content += "<p>未提供逐句批改</p>"
        
    # 添加整体评价
    html_content += f"""
        </div>
        
        <div class="section overall">
            <h2>整体评价</h2>
            <p>{result_json.get("overall_comments", "未提供整体评价")}</p>
        </div>
        
        <div class="section">
            <h2>原始模型输出</h2>
            <pre>{full_response}</pre>
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
    
    print("作文批改结果已在浏览器中打开 (使用千问模型)")

except Exception as e:
    print(f"调用模型时发生错误: {e}")
    print("请检查是否正确配置了 QWEN_API_KEY，以及网络连接是否正常。")