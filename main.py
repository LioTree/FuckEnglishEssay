import google.generativeai as genai
from PIL import Image
import io
import os
import markdown
import webbrowser
import tempfile

# 从环境变量中读取 Gemini API Key
api_key = os.environ.get('GOOGLE_API_KEY')

# 检查 API Key 是否成功读取
if not api_key:
    print("错误：未找到环境变量 GOOGLE_API_KEY。请确保已设置该环境变量。")
    exit()

# 配置 Gemini API Key
genai.configure(api_key=api_key)

# 加载 Gemini 2.0 Flash Exp 模型
model = genai.GenerativeModel('models/gemini-2.0-flash-exp')

# 构建 Prompt (保持不变)
prompt_text = """你是一名初中英语老师，现有一篇英语作文需要你批改，你需要找出文章中所有的拼写错误，用词不当以及语法错误；
同时找出文章中的高级词汇，亮点表达；
最后，你还需要为该同学提出写作进步的建议。
为了定位，你需要输出原文，并请将文章中的所有错误用黑体字标注出来；
对于错误分析，请详细分析语法知识点并给出一定的正例与反例；
对于亮点分析，请详细给出亮点的优秀之处。"""

# 读取图片文件 (保持不变)
try:
    image = Image.open("images/test1.jpg")
    # 将图片转换为字节数据，并指定 MIME 类型
    image_bytes = io.BytesIO()
    image.save(image_bytes, format=image.format) # 保持原始图片格式
    image_data = image_bytes.getvalue()
    image_mime_type = image.get_format_mimetype() if image.format else "image/png" # 获取MIME类型，默认png
    image_content = {
        "mime_type": image_mime_type,
        "data": image_data
    }
except FileNotFoundError:
    print("错误：图片文件 images/test1.jpg未找到，请检查路径是否正确。")
    exit()
except Exception as e:
    print(f"读取图片时发生错误: {e}")
    exit()


# 构造发送给模型的 Parts，包含 Prompt 文本和图片数据 (保持不变)
parts = [
    prompt_text,
    image_content
]

# 发送请求并获取模型的响应
try:
    response = model.generate_content(parts)
    # 获取模型的输出文本
    markdown_text = response.text
    
    # 将Markdown转换为HTML
    html_content = f"""
    <!DOCTYPE html>
    <html>
    <head>
        <meta charset="UTF-8">
        <title>作文批改结果</title>
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
        </style>
    </head>
    <body>
        <h1>英语作文批改结果</h1>
        {markdown.markdown(markdown_text)}
    </body>
    </html>
    """
    
    # 创建临时HTML文件
    with tempfile.NamedTemporaryFile('w', delete=False, suffix='.html', encoding='utf-8') as f:
        f.write(html_content)
        temp_html_path = f.name
    
    # 在浏览器中打开结果
    webbrowser.open('file://' + temp_html_path)
    
    # 同时也在控制台打印结果
    print("作文批改结果已在浏览器中打开")
    print("\n原始Markdown输出:")
    print(markdown_text)

except Exception as e:
    print(f"调用模型时发生错误: {e}")
    print("请检查是否正确配置了 Gemini API Key，以及网络连接是否正常。")