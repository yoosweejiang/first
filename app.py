import streamlit as st
import requests
import json
import warnings

# 过滤无关警告
warnings.filterwarnings("ignore", category=UserWarning, message="missing ScriptRunContext")

# 页面设置
st.set_page_config(
    page_title="Dify Chatbot",
    page_icon="🤖",
    layout="wide"
)

# 初始化会话状态
if "messages" not in st.session_state:
    st.session_state.messages = []
if "conversation_id" not in st.session_state:
    st.session_state.conversation_id = ""

# 侧边栏设置
with st.sidebar:
    st.header("配置参数")
    api_key = st.text_input("API Key", type="password", value="app-P9oyK2ZXA2gQhySojmqzVkJC")
    target_language = st.selectbox("目标语言", ["中文", "英语", "日语", "韩语", "法语"])
    style = st.selectbox("翻译风格", ["正式", "口语化", "技术文档", "文学性"])
    temperature = st.slider("严谨性（Temperature）", 0.0, 1.0, 0.7)

# 显示历史消息
for message in st.session_state.messages:
    with st.chat_message(message["role"]):
        st.markdown(message["content"])

# 用户输入处理
if prompt := st.chat_input("请输入您的问题..."):
    # 添加用户消息到历史
    st.session_state.messages.append({"role": "user", "content": prompt})
    with st.chat_message("user"):
        st.markdown(prompt)

    # 准备API请求
    headers = {
        "Authorization": f"Bearer {api_key}",
        "Content-Type": "application/json"
    }

    payload = {
        "inputs": {
            "target_language": str(target_language),
            "style": str(style),
            "temperature": f"{temperature:.1f}"
        },
        "query": prompt,
        "response_mode": "streaming",
        "conversation_id": st.session_state.conversation_id,
        "user": "user123"
    }

    # 创建占位符用于流式响应
    with st.chat_message("assistant"):
        response_placeholder = st.empty()
        full_response = ""
        
        try:
            # 发送请求
            with st.spinner("正在生成回复..."):
                response = requests.post(
                    "https://api.dify.ai/v1/chat-messages",
                    headers=headers,
                    json=payload,
                    stream=True,
                    timeout=30  # 增加超时设置
                )

            # 处理响应
            if response.status_code == 200:
                for line in response.iter_lines():
                    if line:
                        decoded_line = line.decode('utf-8')
                        if decoded_line.startswith('data: '):
                            try:
                                event_data = json.loads(decoded_line[6:])
                                
                                if event_data['event'] == 'message':
                                    full_response += event_data.get('answer', '')
                                    response_placeholder.markdown(full_response + "▌")
                                
                                elif event_data['event'] == 'message_end':
                                    st.session_state.conversation_id = event_data.get('conversation_id', '')
                                    response_placeholder.markdown(full_response)
                                    st.session_state.messages.append({
                                        "role": "assistant",
                                        "content": full_response
                                    })
                                
                            except json.JSONDecodeError:
                                st.error("JSON解析错误")
            else:
                st.error(f"请求失败: {response.status_code} - {response.text}")

        except Exception as e:
            st.error(f"发生错误: {str(e)}")

# 调试信息
st.sidebar.caption(f"当前会话ID：{st.session_state.conversation_id}")