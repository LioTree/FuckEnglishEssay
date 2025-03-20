document.addEventListener('DOMContentLoaded', function() {
    const uploadForm = document.getElementById('upload-form');
    const fileInput = document.getElementById('file-input');
    const filePreview = document.getElementById('file-preview');
    const resultArea = document.querySelector('.result-area');
    const loading = document.getElementById('loading');
    const resultContent = document.getElementById('result-content');
    const streamOutput = document.getElementById('stream-output');
    const resultContainer = document.getElementById('result-container');
    const originalEssay = document.getElementById('original-essay');
    const correctedEssay = document.getElementById('corrected-essay');
    const sentenceCorrections = document.getElementById('sentence-corrections');
    const overallComments = document.getElementById('overall-comments');
    const rawOutput = document.getElementById('raw-output');
    const newCorrectionBtn = document.getElementById('new-correction-btn');
    const diffResult = document.getElementById('diff-result');
    
    // 预览已选择的图片
    fileInput.addEventListener('change', function() {
        filePreview.innerHTML = '';
        for (let i = 0; i < this.files.length; i++) {
            const file = this.files[i];
            if (!file.type.match('image.*')) continue;
            
            const reader = new FileReader();
            reader.onload = function(e) {
                const div = document.createElement('div');
                div.className = 'preview-item';
                div.innerHTML = `
                    <img src="${e.target.result}" alt="预览">
                    <button type="button" class="remove-btn" data-index="${i}">×</button>
                `;
                filePreview.appendChild(div);
            };
            reader.readAsDataURL(file);
        }
    });
    
    // 移除预览图片
    filePreview.addEventListener('click', function(e) {
        if (e.target.classList.contains('remove-btn')) {
            e.preventDefault();
            // 注意：由于FileList是只读的，所以我们需要重新创建一个FormData对象
            const index = parseInt(e.target.dataset.index);
            e.target.parentElement.remove();
            
            // 这里只是视觉上的移除，在提交时需要处理实际的文件列表
            // 实际处理在提交表单时进行
        }
    });
    
    // 提交表单
    uploadForm.addEventListener('submit', function(e) {
        e.preventDefault();
        
        const formData = new FormData();
        const files = fileInput.files;
        
        if (files.length === 0) {
            alert('请选择至少一张图片');
            return;
        }
        
        for (let i = 0; i < files.length; i++) {
            formData.append('files[]', files[i]);
        }
        
        // 显示结果区域和加载动画
        resultArea.style.display = 'block';
        loading.style.display = 'block';
        resultContent.style.display = 'none';
        streamOutput.textContent = '';
        
        // 第一步：上传图片
        fetch('/upload', {
            method: 'POST',
            body: formData
        })
        .then(response => response.json())
        .then(data => {
            if (data.success) {
                // 第二步：发送批改请求
                return correctEssay(data.image_paths);
            } else {
                throw new Error(data.error || '上传失败');
            }
        })
        .catch(error => {
            loading.style.display = 'none';
            resultContent.style.display = 'block';
            streamOutput.textContent = `错误: ${error.message}`;
        });
    });
    
    // 发送批改请求并处理流式响应
    function correctEssay(imagePaths) {
        loading.style.display = 'block';
        resultContent.style.display = 'block';
        resultContainer.style.display = 'none';
        streamOutput.style.display = 'block';
        streamOutput.textContent = '正在连接到模型...\n';
        
        // 创建EventSource连接
        fetch('/correct', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
            },
            body: JSON.stringify({ image_paths: imagePaths })
        })
        .then(response => {
            // 处理响应为事件流
            const reader = response.body.getReader();
            const decoder = new TextDecoder();
            
            function processStream({ done, value }) {
                if (done) {
                    return;
                }
                
                const chunk = decoder.decode(value);
                const events = chunk.split('\n\n');
                
                for (const event of events) {
                    if (event.startsWith('data: ')) {
                        try {
                            const data = JSON.parse(event.substring(6));
                            handleStreamData(data);
                        } catch (e) {
                            console.error('解析事件数据失败:', e);
                        }
                    }
                }
                
                // 继续读取
                return reader.read().then(processStream);
            }
            
            return reader.read().then(processStream);
        })
        .catch(error => {
            loading.style.display = 'none';
            streamOutput.textContent += `\n错误: ${error.message}`;
        });
    }
    
    // 处理流式数据
    function handleStreamData(data) {
        if (data.status === 'processing') {
            streamOutput.textContent += data.message + '\n';
        } 
        else if (data.status === 'chunk') {
            streamOutput.textContent += data.content;
            streamOutput.scrollTop = streamOutput.scrollHeight;
        } 
        else if (data.status === 'complete') {
            loading.style.display = 'none';
            streamOutput.textContent += '\n\n批改完成！';
            
            // 显示结果容器
            resultContainer.style.display = 'block';
            
            // 填充结果数据
            const result = data.result;
            originalEssay.textContent = result.original_essay || '未提供原始作文';
            correctedEssay.textContent = result.corrected_essay || '未提供批改后作文';
            
            // 填充差异比较结果
            if (result.diff_html) {
                diffResult.innerHTML = result.diff_html;
            } else {
                diffResult.innerHTML = '<p>未能生成差异对比结果</p>';
            }
            
            // 填充逐句批改
            sentenceCorrections.innerHTML = '';
            if (result.sentence_corrections && result.sentence_corrections.length > 0) {
                result.sentence_corrections.forEach((correction, index) => {
                    const div = document.createElement('div');
                    div.className = 'sentence-correction';
                    div.innerHTML = `
                        <h3>句子 ${index + 1}</h3>
                        <p><strong>原句:</strong> <span class="original-text">${correction.original || ''}</span></p>
                        <p><strong>修正:</strong> <span class="corrected-text">${correction.corrected || ''}</span></p>
                        <p class="comments"><strong>评注:</strong> ${correction.comments || ''}</p>
                    `;
                    sentenceCorrections.appendChild(div);
                });
            } else {
                sentenceCorrections.innerHTML = '<p>未提供逐句批改</p>';
            }
            
            // 填充整体评价
            overallComments.textContent = result.overall_comments || '未提供整体评价';
            
            // 填充原始输出
            rawOutput.textContent = data.raw || '';
        } 
        else if (data.status === 'error') {
            loading.style.display = 'none';
            streamOutput.textContent += `\n\n错误: ${data.message}\n`;
            if (data.raw) {
                streamOutput.textContent += `\n原始响应: ${data.raw}`;
            }
        }
    }
    
    // 标签切换功能
    document.querySelectorAll('.tab-btn').forEach(button => {
        button.addEventListener('click', () => {
            // 移除所有标签和内容的活跃状态
            document.querySelectorAll('.tab-btn').forEach(btn => btn.classList.remove('active'));
            document.querySelectorAll('.tab-pane').forEach(pane => pane.classList.remove('active'));
            
            // 为当前标签和内容添加活跃状态
            button.classList.add('active');
            const tabId = button.getAttribute('data-tab');
            document.getElementById(tabId).classList.add('active');
        });
    });
    
    // 新的批改按钮
    newCorrectionBtn.addEventListener('click', function() {
        // 重置表单和界面状态
        uploadForm.reset();
        filePreview.innerHTML = '';
        resultArea.style.display = 'none';
        resultContent.style.display = 'none';
        streamOutput.textContent = '';
    });
});
