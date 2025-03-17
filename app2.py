import streamlit as st
import requests
import json
import warnings
from datetime import datetime

# 过滤Streamlit内部警告
warnings.filterwarnings("ignore", category=UserWarning, message="missing ScriptRunContext")

# 页面配置
st.set_page_config(
    page_title="Dify 智能助手",
    page_icon="🤖",
    layout="wide",
    initial_sidebar_state="expanded"
)

# 初始化会话状态
if "messages" not in st.session_state:
    st.session_state.messages = []
if "conversation_id" not in st.session_state:
    st.session_state.conversation_id = ""
if "selected_conversation" not in st.session_state:
    st.session_state.selected_conversation = None

# 工具函数
def convert_timestamp(ts):
    """将UNIX时间戳转换为可读时间"""
    return datetime.fromtimestamp(ts).strftime('%Y-%m-%d %H:%M')

# 侧边栏模块
with st.sidebar:
    st.header("⚙️ 系统配置")
    api_key = st.text_input(
        "API密钥", 
        type="password", 
        value="app-P9oyK2ZXA2gQhySojmqzVkJC",
        help="从Dify控制台获取的API密钥"
    )
    
    # 参数配置折叠面板
    with st.expander("高级参数", expanded=True):
        target_language = st.selectbox(
            "目标语言", 
            ["中文", "英语", "日语", "韩语", "法语"],
            index=0
        )
        style = st.selectbox(
            "翻译风格",
            ["正式", "口语化", "技术文档", "文学性"],
            index=1
        )
        temperature = st.slider(
            "创意度", 
            0.0, 1.0, 0.7,
            help="值越小输出越保守，值越大越有创造性"
        )

    # 对话历史管理
    st.divider()
    st.header("📚 对话历史")
    
    # 获取对话列表
    try:
        conv_response = requests.get(
            "https://api.dify.ai/v1/conversations",
            headers={"Authorization": f"Bearer {api_key}"},
            params={"limit": 10}
        )
        conversations = conv_response.json().get('data', []) if conv_response.status_code == 200 else []
    except Exception as e:
        st.error(f"获取对话失败: {str(e)}")
        conversations = []
    
    # 对话选择按钮
    for conv in conversations:
        cols = st.columns([3, 2])
        with cols[0]:
            btn_label = f"{conv.get('name', '未命名对话')} 🕒{convert_timestamp(conv['created_at'])}"
            if st.button(btn_label, key=f"conv_{conv['id']}"):
                st.session_state.conversation_id = conv['id']
                st.session_state.selected_conversation = conv
                st.rerun()
        with cols[1]:
            if st.button("✏️", key=f"edit_{conv['id']}"):
                # 此处添加重命名逻辑
                pass

# 主界面
st.title(f"💬 当前对话：{st.session_state.selected_conversation.get('name', '新对话') if st.session_state.selected_conversation else '新对话'}")

# 消息显示增强
for msg in st.session_state.messages:
    with st.chat_message(msg["role"]):
        # 基础消息内容
        st.markdown(msg["content"])
        
        # 附件显示
        if "files" in msg:
            for f in msg.get("files", []):
                if f["type"] == "image":
                    st.image(f["url"], caption="生成图片")
                else:
                    st.markdown(f"📎 附件：[{f.get('name','未命名文件')}]({f['url']})")
        
        # 思维过程展示
        if "thoughts" in msg:
            with st.expander("🧠 AI思考过程"):
                for thought in msg["thoughts"]:
                    st.markdown(f"""
                    **步骤 {thought['position']}**
                    ```python
                    {thought.get('thought', '')}
                    # 使用工具: {thought.get('tool', '无')}
                    # 工具输入: {json.loads(thought.get('tool_input', '{}'))}
                    ```
                    """)

# 消息输入处理
if prompt := st.chat_input("输入您的问题..."):
    # 添加用户消息
    st.session_state.messages.append({"role": "user", "content": prompt})
    
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
        "user": "user123",
        "files": []  # 可添加文件上传逻辑
    }

    # 流式响应处理
    with st.chat_message("assistant"):
        response_placeholder = st.empty()
        full_response = ""
        collected_files = []
        agent_thoughts = []

        try:
            with st.spinner("🔍 正在思考中..."):
                response = requests.post(
                    "https://api.dify.ai/v1/chat-messages",
                    headers=headers,
                    json=payload,
                    stream=True,
                    timeout=30
                )

            if response.status_code == 200:
                for line in response.iter_lines():
                    if line:
                        decoded_line = line.decode('utf-8')
                        if decoded_line.startswith('data: '):
                            try:
                                event_data = json.loads(decoded_line[6:])
                                
                                # 消息片段处理
                                if event_data['event'] == 'message':
                                    full_response += event_data.get('answer', '')
                                    response_placeholder.markdown(full_response + "▌")
                                
                                # 消息结束处理
                                elif event_data['event'] == 'message_end':
                                    st.session_state.conversation_id = event_data.get('conversation_id', '')
                                    response_placeholder.markdown(full_response)
                                    
                                    # 收集完整消息数据
                                    final_data = {
                                        "role": "assistant",
                                        "content": full_response,
                                        "files": event_data.get('message_files', []),
                                        "thoughts": event_data.get('agent_thoughts', [])
                                    }
                                    st.session_state.messages.append(final_data)
                                
                                # 文件处理
                                elif event_data['event'] == 'file_upload':
                                    collected_files.append({
                                        "type": event_data.get('file_type'),
                                        "url": event_data.get('url'),
                                        "name": event_data.get('file_name')
                                    })
                                
                                # 思考过程处理
                                elif event_data['event'] == 'agent_thought':
                                    agent_thoughts.append({
                                        "position": event_data.get('position'),
                                        "thought": event_data.get('thought'),
                                        "tool": event_data.get('tool'),
                                        "tool_input": event_data.get('tool_input')
                                    })

                            except json.JSONDecodeError:
                                st.error("⚠️ 数据解析错误")
            else:
                st.error(f"❌ 请求失败（{response.status_code}）: {response.text}")

        except requests.exceptions.Timeout:
            st.error("⏳ 请求超时，请稍后重试")
        except Exception as e:
            st.error(f"⚠️ 发生意外错误: {str(e)}")

# 调试面板
with st.sidebar:
    st.divider()
    with st.expander("调试信息", expanded=False):
        st.caption(f"会话ID: `{st.session_state.conversation_id}`")
        st.caption(f"历史消息数: {len(st.session_state.messages)}")
        st.caption("最近一次请求参数:")
        st.json({
            "target_language": target_language,
            "style": style,
            "temperature": temperature
        })