import streamlit as st
import requests

# ========== 配置 ==========
COZE_API_BASE = "https://api.coze.cn"
COZE_API_TOKEN = "你的令牌"
COZE_BOT_ID = "你的ID"

st.set_page_config(page_title="财务报表查询", page_icon="📊", layout="wide")

# ========== 初始化对话历史 ==========
if "messages" not in st.session_state:
    st.session_state.messages = []
if "conversation_id" not in st.session_state:
    st.session_state.conversation_id = None

# ========== 侧边栏 ==========
with st.sidebar:
    st.header("⚙️ 查询设置")
    stock_code = st.text_input("股票代码", value="600519")
    if st.button("🗑️ 清空对话", use_container_width=True):
        st.session_state.messages = []
        st.session_state.conversation_id = None
        st.rerun()
    st.caption("⚠️ 仅供教学研究，不构成投资建议")

# ========== 主区域 ==========
st.title("📊 财务报表查询助手")
st.caption(f"当前股票：**{stock_code}**")

# 展示历史对话
for msg in st.session_state.messages:
    with st.chat_message(msg["role"]):
        st.markdown(msg["content"])

# ========== 输入区 ==========
user_input = st.chat_input("输入你的问题，例如：2024年毛利率是多少？")

if user_input:
    # 显示用户消息
    st.session_state.messages.append({"role": "user", "content": user_input})
    with st.chat_message("user"):
        st.markdown(user_input)


        #————————coze连接的代码----------#

st.markdown("这是一段测试")
