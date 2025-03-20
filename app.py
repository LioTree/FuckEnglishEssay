import os
import io
import json
import re
import base64
import tempfile
import subprocess
from flask import Flask, render_template, request, Response, jsonify
from werkzeug.utils import secure_filename
from PIL import Image
from openai import OpenAI

app = Flask(__name__)
app.config['UPLOAD_FOLDER'] = 'uploads'
app.config['MAX_CONTENT_LENGTH'] = 16 * 1024 * 1024  # 16MB限制
app.config['ALLOWED_EXTENSIONS'] = {'png', 'jpg', 'jpeg', 'gif'}

# 确保上传目录存在
os.makedirs(app.config['UPLOAD_FOLDER'], exist_ok=True)

# 验证文件扩展名
def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in app.config['ALLOWED_EXTENSIONS']

# 从环境变量获取API密钥
api_key = os.environ.get('QWEN_API_KEY')

# 配置OpenAI客户端连接到阿里云千问服务
client = OpenAI(
    api_key=api_key,
    base_url="https://dashscope.aliyuncs.com/compatible-mode/v1"
)

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/upload', methods=['POST'])
def upload_file():
    # 检查是否有文件被上传
    if 'files[]' not in request.files:
        return jsonify({'error': '没有选择文件'}), 400
    
    files = request.files.getlist('files[]')
    
    # 检查是否选择了文件
    if len(files) == 0 or files[0].filename == '':
        return jsonify({'error': '没有选择文件'}), 400
    
    # 验证并保存所有文件
    image_paths = []
    for file in files:
        if file and allowed_file(file.filename):
            filename = secure_filename(file.filename)
            filepath = os.path.join(app.config['UPLOAD_FOLDER'], filename)
            file.save(filepath)
            image_paths.append(filepath)
    
    if not image_paths:
        return jsonify({'error': '无有效图片文件'}), 400
    
    # 存储上传的图片路径到会话
    return jsonify({'success': True, 'image_paths': image_paths})

@app.route('/correct', methods=['POST'])
def correct_essay():
    data = request.get_json()
    image_paths = data.get('image_paths', [])
    
    if not image_paths:
        return jsonify({'error': '没有图片路径'}), 400
    
    def generate():
        try:
            # 准备图片
            images_data = []
            for image_path in image_paths:
                image = Image.open(image_path)
                image_bytes = io.BytesIO()
                image.save(image_bytes, format=image.format)
                base64_image = base64.b64encode(image_bytes.getvalue()).decode('utf-8')
                image_mime_type = f"image/{image.format.lower()}" if image.format else "image/jpeg"
                images_data.append({
                    "type": "image_url",
                    "image_url": {
                        "url": f"data:{image_mime_type};base64,{base64_image}"
                    }
                })
            
            # 构建Prompt
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
            
            # 构建消息内容
            content = [{"type": "text", "text": prompt_text}]
            content.extend(images_data)
            
            messages = [
                {"role": "system", "content": "You are a helpful assistant."},
                {"role": "user", "content": content}
            ]
            
            # 调用千问视觉大模型（流式输出）
            yield "data: " + json.dumps({"status": "processing", "message": "正在获取千问模型响应..."}) + "\n\n"
            
            stream_response = client.chat.completions.create(
                model="qwen-vl-max-latest",
                messages=messages,
                stream=True
            )
            
            full_response = ""
            
            # 逐步处理流式响应并发送到前端
            for chunk in stream_response:
                if chunk.choices and chunk.choices[0].delta.content:
                    content = chunk.choices[0].delta.content
                    full_response += content
                    yield "data: " + json.dumps({"status": "chunk", "content": content}) + "\n\n"
            
            # 尝试从响应中提取JSON
            try:
                result_json = json.loads(full_response)
                
                # 生成作文diff结果
                diff_html = generate_diff(result_json.get("original_essay", ""), 
                                         result_json.get("corrected_essay", ""))
                
                result_json["diff_html"] = diff_html
                yield "data: " + json.dumps({"status": "complete", "result": result_json, "raw": full_response}) + "\n\n"
            except json.JSONDecodeError:
                # 尝试使用正则表达式提取JSON部分
                json_match = re.search(r'({[\s\S]*})', full_response)
                if json_match:
                    try:
                        result_json = json.loads(json_match.group(1))
                        
                        # 生成作文diff结果
                        diff_html = generate_diff(result_json.get("original_essay", ""), 
                                                result_json.get("corrected_essay", ""))
                        
                        result_json["diff_html"] = diff_html
                        yield "data: " + json.dumps({"status": "complete", "result": result_json, "raw": full_response}) + "\n\n"
                    except:
                        yield "data: " + json.dumps({
                            "status": "error", 
                            "message": "无法从响应中提取有效的JSON",
                            "raw": full_response
                        }) + "\n\n"
                else:
                    yield "data: " + json.dumps({
                        "status": "error", 
                        "message": "无法从响应中找到JSON格式内容",
                        "raw": full_response
                    }) + "\n\n"
        
        except Exception as e:
            yield "data: " + json.dumps({"status": "error", "message": str(e)}) + "\n\n"
        
        # 清理上传的文件
        for image_path in image_paths:
            try:
                if os.path.exists(image_path):
                    os.remove(image_path)
            except:
                pass
    
    return Response(generate(), mimetype='text/event-stream')

# 新增：将文本拆分成句子的函数
def split_into_sentences(text):
    """
    将文本拆分成句子，每个句子一行，并去除句子内的换行符
    """
    # 先替换掉句子内的换行符（保留段落间的换行）
    text = re.sub(r'(?<![.!?])\n(?![.!?])', ' ', text)
    
    # 使用正则表达式拆分句子
    sentences = re.split(r'([.!?])\s+', text)
    
    # 重组句子（因为split会将分隔符也分离出来）
    formatted_sentences = []
    i = 0
    while i < len(sentences):
        if i + 1 < len(sentences) and sentences[i+1] in ['.', '!', '?']:
            formatted_sentences.append(sentences[i] + sentences[i+1])
            i += 2
        else:
            formatted_sentences.append(sentences[i])
            i += 1
    
    # 过滤掉空句子并返回
    return '\n'.join([s.strip() for s in formatted_sentences if s.strip()])

def generate_diff(original_text, corrected_text):
    """生成原始作文和批改后作文的差异HTML"""
    try:
        # 将原始文章和修改后的文章拆分成每句一行的格式
        original_formatted = split_into_sentences(original_text)
        corrected_formatted = split_into_sentences(corrected_text)
        
        with tempfile.NamedTemporaryFile('w', delete=False, encoding='utf-8', suffix='.txt') as f_orig:
            f_orig.write(original_formatted)
            orig_file_name = f_orig.name
        with tempfile.NamedTemporaryFile('w', delete=False, encoding='utf-8', suffix='.txt') as f_corr:
            f_corr.write(corrected_formatted)
            corr_file_name = f_corr.name
        
        # 使用icdiff生成差异，然后用aha转换为HTML
        diff_command = f"icdiff --cols=100 {orig_file_name} {corr_file_name} | aha --title 'Diff'"
        diff_html = subprocess.check_output(diff_command, shell=True, encoding='utf-8')
        
        # 清理临时文件
        os.remove(orig_file_name)
        os.remove(corr_file_name)
        
        return diff_html
    except Exception as e:
        return f"<div>生成diff结果时出错: {str(e)}</div>"

if __name__ == '__main__':
    app.run(debug=True)
