# LearnLLM

# LLM Chatbot Demo

这是一个基于 OpenAI GPT-4o-mini 的简单聊天机器人演示，使用 Streamlit 作为前端。

## 功能
- 多轮对话
- 会话状态保存
- 支持自定义提示词

## 运行步骤
1. 克隆项目
2. 安装依赖：`pip install -r requirements.txt`
3. 配置环境变量 `.env` 文件，添加 `OPENAI_API_KEY=你的密钥`
4. 运行：`streamlit run app.py`

## 项目结构
- `app.py`：主应用程序
- `utils/openai_api.py`：封装的 OpenAI 接口调用
