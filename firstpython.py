import streamlit as st
import requests

# Dify API 配置
DIFY_API_URL = "https://api.dify.ai/v1/chat-messages"  # 使用 Dify 的聊天消息接口
API_KEY = "app-P9oyK2ZXA2gQhySojmqzVkJC"  # 替换为你的 Dify API 密钥

# Streamlit 页面标题
st.title("高级翻译应用 (Dify 集成版)")

# 输入文本
input_text = st.text_area("请输入要翻译的文本", height=150)

# 选择目标语言
target_language = st.selectbox(
    "选择目标语言",
    ["英语", "中文", "马来语", "粤语"],
    key="target_language"
)

# 选择翻译风格
style = st.selectbox(
    "选择翻译风格",
    ["日常", "科研", "商务", "文学"],
    key="style"
)

# 设置翻译严谨性 (temperature)
temperature = st.slider(
    "设置翻译严谨性 (temperature)",
    min_value=0.0,
    max_value=1.0,
    value=0.5,
    step=0.1,
    key="temperature"
)

# 翻译按钮
if st.button("翻译"):
    if input_text.strip() == "":
        st.warning("请输入要翻译的文本")
    else:
        # 构建 Dify API 请求参数
        headers = {
            "Authorization": f"Bearer {API_KEY}",
            "Content-Type": "application/json"
        }
        data = {
            "inputs": {
                "target_language": target_language,
                "style": style,
                "temperature": temperature
            },
            "query": input_text,  # 用户输入的文本作为 query
            "response_mode": "blocking",  # 使用阻塞模式（非流式）
            "user": "streamlit-user-123"  # 自定义用户标识（可选）
        }
        
        # 调用 Dify API
        response = requests.post(DIFY_API_URL, json=data, headers=headers)
        
        # 解析响应
        if response.status_code == 200:
            response_data = response.json()
            translated_text = response_data.get("answer", "翻译失败")
            
            # 显示翻译结果
            st.success("翻译结果：")
            st.write(translated_text)
            
            # 可选：显示知识库参考（根据 Dify 返回的 retriever_resources）
            if "retriever_resources" in response_data:
                st.subheader("参考知识库内容：")
                for resource in response_data["retriever_resources"]:
                    st.markdown(f"**{resource['dataset_name']}** - {resource['content']}")
        else:
            st.error(f"翻译失败，错误代码：{response.status_code}")
            st.write("响应详情：", response.text)  # 调试用
