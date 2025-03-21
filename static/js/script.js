document.addEventListener('DOMContentLoaded', function () {
    const uploadForm = document.getElementById('upload-form');
    const homeworkContainer = document.getElementById('homework-container');
    const addHomeworkBtn = document.getElementById('add-homework');
    const resultArea = document.querySelector('.result-area');
    const loading = document.getElementById('loading');
    const resultContent = document.getElementById('result-content');
    let homeworkTabs = document.getElementById('homework-tabs');  // 改为let声明
    const homeworkResults = document.getElementById('homework-results');
    const newCorrectionBtn = document.getElementById('new-correction-btn');
    const homeworkResultTemplate = document.getElementById('homework-result-template');

    let homeworkCount = 1; // 初始只有一个作业

    // 添加新作业
    addHomeworkBtn.addEventListener('click', function () {
        const newIndex = homeworkCount;
        homeworkCount++;

        const homeworkBlock = document.createElement('div');
        homeworkBlock.className = 'homework-block';
        homeworkBlock.dataset.index = newIndex;

        homeworkBlock.innerHTML = `
            <div class="form-group">
                <label>作业 #${homeworkCount} <button type="button" class="remove-homework">删除</button></label>
                <input type="file" class="file-input" name="files[${newIndex}][]" multiple>
                <div class="file-preview"></div>
            </div>
        `;

        homeworkContainer.appendChild(homeworkBlock);

        // 创建新作业的文件存储
        filesMap.set(newIndex.toString(), new DataTransfer());

        // 为新添加的删除按钮添加事件监听
        homeworkBlock.querySelector('.remove-homework').addEventListener('click', function () {
            // 从filesMap中移除对应作业
            filesMap.delete(newIndex.toString());
            homeworkBlock.remove();
        });

        // 为新添加的文件输入添加预览功能
        setupFilePreview(homeworkBlock.querySelector('.file-input'), homeworkBlock.querySelector('.file-preview'));
    });

    // 移除已有作业的处理
    homeworkContainer.addEventListener('click', function (e) {
        if (e.target.classList.contains('remove-homework')) {
            const homeworkBlock = e.target.closest('.homework-block');
            homeworkBlock.remove();
        }
    });

    // 存储每个作业块的文件列表
    const filesMap = new Map();

    // 设置文件预览功能
    function setupFilePreview(fileInput, previewContainer) {
        const homeworkBlock = fileInput.closest('.homework-block');
        const homeworkIndex = homeworkBlock.dataset.index;

        // 确保当前作业块在filesMap中有数据
        if (!filesMap.has(homeworkIndex)) {
            filesMap.set(homeworkIndex, new DataTransfer());
        }

        fileInput.addEventListener('change', function () {
            // 获取当前作业的DataTransfer对象
            const dataTransfer = filesMap.get(homeworkIndex);
            
            // 添加新选择的文件到DataTransfer
            for (let i = 0; i < this.files.length; i++) {
                const file = this.files[i];
                if (file.type.match('image.*')) {
                    dataTransfer.items.add(file);
                }
            }
            
            // 更新input的files属性
            fileInput.files = dataTransfer.files;
            
            // 清空预览区域并重新显示所有文件
            refreshFilePreview(fileInput, previewContainer, homeworkIndex);
        });

        // 移除预览图片
        previewContainer.addEventListener('click', function (e) {
            if (e.target.classList.contains('remove-btn')) {
                e.preventDefault();
                
                // 获取预览项及其索引
                const previewItem = e.target.closest('.preview-item');
                const fileIndex = previewItem.dataset.fileIndex;
                const homeworkBlock = previewContainer.closest('.homework-block');
                const homeworkIndex = homeworkBlock.dataset.index;
                const fileInput = homeworkBlock.querySelector('.file-input');
                
                // 从DataTransfer中移除文件
                const dataTransfer = filesMap.get(homeworkIndex);
                const newDataTransfer = new DataTransfer();
                
                // 创建新的DataTransfer，排除被删除的文件
                for (let i = 0; i < dataTransfer.files.length; i++) {
                    if (i !== parseInt(fileIndex)) {
                        newDataTransfer.items.add(dataTransfer.files[i]);
                    }
                }
                
                // 更新DataTransfer和文件输入
                filesMap.set(homeworkIndex, newDataTransfer);
                fileInput.files = newDataTransfer.files;
                
                // 刷新预览
                refreshFilePreview(fileInput, previewContainer, homeworkIndex);
            }
        });
    }

    // 添加刷新文件预览的函数
    function refreshFilePreview(fileInput, previewContainer, homeworkIndex) {
        const dataTransfer = filesMap.get(homeworkIndex);
        
        // 清空预览区域
        previewContainer.innerHTML = '';
        
        // 为每个文件创建预览
        for (let i = 0; i < dataTransfer.files.length; i++) {
            const file = dataTransfer.files[i];
            if (!file.type.match('image.*')) continue;
            
            const reader = new FileReader();
            reader.onload = function(e) {
                const div = document.createElement('div');
                div.className = 'preview-item';
                div.dataset.fileIndex = i;
                div.innerHTML = `
                    <img src="${e.target.result}" alt="预览">
                    <button type="button" class="remove-btn">×</button>
                `;
                previewContainer.appendChild(div);
            };
            reader.readAsDataURL(file);
        }
    }

    // 为初始作业块设置文件预览
    const initialFileInput = document.querySelector('.homework-block[data-index="0"] .file-input');
    const initialPreview = document.querySelector('.homework-block[data-index="0"] .file-preview');
    setupFilePreview(initialFileInput, initialPreview);

    // 提交表单
    uploadForm.addEventListener('submit', function (e) {
        e.preventDefault();

        // 获取所有作业块
        const homeworkBlocks = document.querySelectorAll('.homework-block');

        if (homeworkBlocks.length === 0) {
            alert('请至少添加一个作业');
            return;
        }

        // 检查是否每个作业都有上传文件
        let hasFiles = true;
        homeworkBlocks.forEach(block => {
            const fileInput = block.querySelector('.file-input');
            if (fileInput.files.length === 0) {
                hasFiles = false;
            }
        });

        if (!hasFiles) {
            alert('请确保每个作业都上传了至少一张图片');
            return;
        }

        // 准备表单数据
        const formData = new FormData();

        homeworkBlocks.forEach(block => {
            const index = block.dataset.index;
            const fileInput = block.querySelector('.file-input');

            for (let i = 0; i < fileInput.files.length; i++) {
                formData.append(`files[${index}][]`, fileInput.files[i]);
            }
        });

        // 显示结果区域和加载动画
        resultArea.style.display = 'block';
        loading.style.display = 'block';
        resultContent.style.display = 'none';

        // 清空之前的结果
        homeworkTabs.innerHTML = '';
        homeworkResults.innerHTML = '';

        // 上传文件
        fetch('/upload', {
            method: 'POST',
            body: formData
        })
            .then(response => response.json())
            .then(data => {
                if (data.success) {
                    // 准备结果区域
                    resultContent.style.display = 'block';

                    // 移除旧的作业标签点击事件监听器 - 修改这部分代码
                    homeworkTabs.innerHTML = ''; // 清空内容而不是替换元素

                    // 为每个作业创建标签和结果容器
                    Object.keys(data.homework_data).forEach((homeworkIndex, i) => {
                        const homeworkData = data.homework_data[homeworkIndex];

                        // 创建作业标签
                        const tabButton = document.createElement('button');
                        tabButton.className = 'homework-tab' + (i === 0 ? ' active' : '');
                        tabButton.textContent = `作业 ${Number(homeworkIndex) + 1}`;
                        tabButton.dataset.homework = homeworkIndex;
                        homeworkTabs.appendChild(tabButton);

                        // 克隆结果模板
                        const resultContent = document.importNode(homeworkResultTemplate.content, true);
                        const resultElement = resultContent.querySelector('.homework-result');
                        resultElement.id = `homework-result-${homeworkIndex}`;
                        resultElement.dataset.homework = homeworkIndex;
                        resultElement.style.display = i === 0 ? 'block' : 'none';

                        homeworkResults.appendChild(resultContent);

                        // 设置标签切换功能
                        setupTabSwitching(resultElement);

                        // 开始批改
                        correctEssay(homeworkData.image_paths, homeworkIndex);
                    });

                    // 作业标签切换事件
                    homeworkTabs.addEventListener('click', function (e) {
                        if (e.target.classList.contains('homework-tab')) {
                            // 更新标签状态
                            document.querySelectorAll('.homework-tab').forEach(tab => {
                                tab.classList.remove('active');
                            });
                            e.target.classList.add('active');

                            // 更新结果显示
                            const homeworkIndex = e.target.dataset.homework;
                            document.querySelectorAll('.homework-result').forEach(result => {
                                result.style.display = result.dataset.homework === homeworkIndex ? 'block' : 'none';
                            });
                        }
                    });

                    loading.style.display = 'none';
                } else {
                    throw new Error(data.error || '上传失败');
                }
            })
            .catch(error => {
                loading.style.display = 'none';
                resultContent.style.display = 'block';
                alert(`错误: ${error.message}`);
            });
    });

    // 发送批改请求并处理流式响应
    function correctEssay(imagePaths, homeworkIndex) {
        const resultElement = document.querySelector(`.homework-result[data-homework="${homeworkIndex}"]`);

        // 确保结果元素存在
        if (!resultElement) {
            console.error(`未找到作业 #${homeworkIndex} 的结果容器`);
            return;
        }

        resultElement.style.display = 'block';

        const streamOutput = resultElement.querySelector('.stream-output');
        const resultContainer = resultElement.querySelector('.result-container');

        streamOutput.style.display = 'block';
        streamOutput.textContent = `正在连接到模型...(作业 #${Number(homeworkIndex) + 1})\n`;

        fetch('/correct', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
            },
            body: JSON.stringify({ image_paths: imagePaths, homework_index: homeworkIndex })
        })
            .then(response => {
                const reader = response.body.getReader();
                const decoder = new TextDecoder();
                let buffer = ''; // 创建缓冲区存储未完成的数据

                function processStream({ done, value }) {
                    if (done) {
                        // 处理结束时，如果缓冲区还有数据，尝试处理它
                        if (buffer.trim()) {
                            processEventData(buffer, resultElement);
                        }
                        return;
                    }

                    // 解码新接收的数据并添加到缓冲区
                    const chunk = decoder.decode(value, { stream: true });
                    buffer += chunk;
                    
                    // 处理缓冲区中的完整事件
                    const events = extractEvents(buffer);
                    buffer = events.remainder; // 更新缓冲区为剩余的不完整数据
                    
                    // 处理所有完整事件
                    for (const event of events.complete) {
                        processEventData(event, resultElement);
                    }

                    return reader.read().then(processStream);
                }

                // 从缓冲区提取完整的SSE事件
                function extractEvents(buffer) {
                    const delimiter = '\n\n';
                    const events = buffer.split(delimiter);
                    let completeEvents = [];
                    
                    // 如果分割后没有剩余部分，说明所有事件都是完整的
                    if (buffer.endsWith(delimiter)) {
                        completeEvents = events;
                        return { complete: completeEvents, remainder: '' };
                    }
                    
                    // 最后一个部分是不完整的，保留它
                    const remainder = events.pop();
                    completeEvents = events;
                    
                    return { complete: completeEvents, remainder: remainder };
                }

                // 处理单个事件数据
                function processEventData(event, resultElement) {
                    event = event.trim();
                    if (!event.startsWith('data: ')) return;
                    
                    const jsonStr = event.substring(6);
                    try {
                        console.log("处理事件数据:", jsonStr);
                        const data = JSON.parse(jsonStr);
                        handleStreamData(data, resultElement);
                    } catch (e) {
                        console.error('解析事件数据失败:', e, '原始数据:', jsonStr);
                    }
                }

                return reader.read().then(processStream);
            })
            .catch(error => {
                streamOutput.textContent += `\n错误: ${error.message}`;
            });
    }

    // 处理流式数据
    function handleStreamData(data, resultElement) {
        // 确保只更新当前作业的结果容器
        if (!resultElement) {
            console.error('处理流数据时找不到结果元素');
            return;
        }

        const streamOutput = resultElement.querySelector('.stream-output');
        const resultContainer = resultElement.querySelector('.result-container');

        if (data.status === 'processing') {
            streamOutput.textContent += data.message + '\n';
        }
        else if (data.status === 'chunk') {
            streamOutput.textContent += data.content;
            streamOutput.scrollTop = streamOutput.scrollHeight;
        }
        else if (data.status === 'complete') {
            streamOutput.textContent += '\n\n批改完成！';

            // 显示结果容器
            resultContainer.style.display = 'block';

            // 填充结果数据
            const result = data.result;
            resultElement.querySelector('.original-essay').textContent = result.original_essay || '未提供原始作文';
            resultElement.querySelector('.corrected-essay').textContent = result.corrected_essay || '未提供批改后作文';

            // 填充差异比较结果
            if (result.diff_html) {
                resultElement.querySelector('.diff-result').innerHTML = result.diff_html;
            } else {
                resultElement.querySelector('.diff-result').innerHTML = '<p>未能生成差异对比结果</p>';
            }

            // 填充逐句批改
            const sentenceCorrections = resultElement.querySelector('.sentence-corrections');
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
            resultElement.querySelector('.overall-comments').textContent = result.overall_comments || '未提供整体评价';

            // 填充原始输出
            resultElement.querySelector('.raw-output').textContent = data.raw || '';

            // 设置标签切换功能
            setupTabSwitching(resultElement);
        }
        else if (data.status === 'error') {
            streamOutput.textContent += `\n\n错误: ${data.message}\n`;
            if (data.raw) {
                streamOutput.textContent += `\n原始响应: ${data.raw}`;
            }
        }
    }

    // 设置标签切换功能
    function setupTabSwitching(resultElement) {
        if (!resultElement) return;

        const tabButtons = resultElement.querySelectorAll('.tab-btn');

        // 移除现有事件监听器
        tabButtons.forEach(button => {
            const newButton = button.cloneNode(true);
            button.parentNode.replaceChild(newButton, button);
        });

        // 重新添加事件监听器
        resultElement.querySelectorAll('.tab-btn').forEach(button => {
            button.addEventListener('click', () => {
                // 移除所有标签和内容的活跃状态
                resultElement.querySelectorAll('.tab-btn').forEach(btn => {
                    btn.classList.remove('active');
                });
                resultElement.querySelectorAll('.tab-pane').forEach(pane => {
                    pane.classList.remove('active');
                });

                // 为当前标签和内容添加活跃状态
                button.classList.add('active');
                const tabId = button.getAttribute('data-tab');
                resultElement.querySelector(`.tab-pane[data-pane="${tabId}"]`).classList.add('active');
            });
        });
    }

    // 新的批改按钮
    newCorrectionBtn.addEventListener('click', function () {
        // 重置表单和界面状态
        uploadForm.reset();
        document.querySelectorAll('.file-preview').forEach(preview => {
            preview.innerHTML = '';
        });

        // 只保留第一个作业块，移除其他所有
        const homeworkBlocks = document.querySelectorAll('.homework-block');
        for (let i = 1; i < homeworkBlocks.length; i++) {
            homeworkBlocks[i].remove();
        }

        // 清空文件映射
        filesMap.clear();
        filesMap.set('0', new DataTransfer());

        homeworkCount = 1;
        resultArea.style.display = 'none';
        resultContent.style.display = 'none';
    });
});
