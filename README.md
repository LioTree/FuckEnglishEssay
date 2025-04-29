# FuckEnglishEssay

基于Qwen-VL-Max-Latest批量批改初中英语作文。

## 安装与运行

### 运行环境要求



### 方式一：使用 Docker 运行 (推荐)

1.  **配置 API Key:**
    在项目根目录下创建一个名为 `.env` 的文件，并添加您的 Qwen API Key：
    ```env
    QWEN_API_KEY=sk-xxxxxxxxxxxxxxxxxxxxxxxxxxxxx
    ```

2.  **构建并启动容器:**
    在项目根目录下运行：
    ```bash
    docker-compose up --build -d
    ```

3.  **访问应用:**
    打开浏览器访问 `http://127.0.0.1:5000`。

4.  **停止容器:**
    ```bash
    docker-compose down
    ```

### 方式二：直接使用 Python 运行

1.  **创建并激活虚拟环境 (推荐):**
    ```bash
    python3 -m venv myenv
    source myenv/bin/activate  # macOS/Linux
    # 或者
    # myenv\Scripts\activate  # Windows
    ```

2.  **安装依赖:**
    ```bash
    pip install -r requirements.txt
    ```

3.  **运行应用:**
    在运行应用之前，请确保您已经设置了 `QWEN_API_KEY` 环境变量。
    ```bash
    export QWEN_API_KEY=sk-xxxxxxxxxxxxxxxxxxxxxxxxxxxxx  # macOS/Linux
    # 或者
    # set QWEN_API_KEY=sk-xxxxxxxxxxxxxxxxxxxxxxxxxxxxx  # Windows
    ```
    然后运行：
    ```bash
    flask run
    ```

4.  **访问应用:**
    打开浏览器访问 `http://127.0.0.1:5000`。

5.  **退出虚拟环境 (如果使用了):**
    ```bash
    deactivate
    ```
