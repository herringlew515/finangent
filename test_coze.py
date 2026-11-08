import streamlit as st
import requests
import time

COZE_API_BASE = "https://api.coze.cn"
# 强行确保 Token 在一行内
COZE_API_TOKEN = "pat_你的令牌"
COZE_BOT_ID = "你的ID"

st.title("Coze API 测试")

if st.button("测试"):
    headers = {"Authorization": f"Bearer {COZE_API_TOKEN}"}
    #Coze API 使用 Bearer Token 鉴权

    # 1. 发起对话
    r = requests.post(f"{COZE_API_BASE}/v3/chat", headers=headers,  json={
            "bot_id": COZE_BOT_ID,
            "user_id": "test",
            "stream": False,
            "auto_save_history": True,  
            "additional_messages": [{"role": "user", "content": "24年的总营业收入", "content_type": "text"}]
        })
    result = r.json()
    conv_id = result["data"]["conversation_id"]
    chat_id = result["data"]["id"]

    # 2. 轮询查询状态（加入容错机制）
    with st.spinner("正在等待 Bot 生成回答..."):
        status = "in_progress"

        for _ in range(20):  
            time.sleep(3)    # 等待3秒
            status_url = f"{COZE_API_BASE}/v3/chat/retrieve?conversation_id={conv_id}&chat_id={chat_id}"
            
            try:
                status_res = requests.get(status_url, headers=headers, timeout=10).json()
                
                if status_res.get("code") == 0:
                    status = status_res["data"]["status"]
                    if status == "completed":
                        break 
                    elif status == "failed":
                        st.error("对话处理失败")
                        st.stop()
                else:
                    # 如果接口返回鉴权错误等，直接显示
                    st.error(f"查询状态失败: {status_res.get('msg')}")
                    st.stop()
            except requests.exceptions.RequestException:
                # 如果发生网络断连，忽略这个错误，继续下一次循环
                pass

    # 3. 获取最终消息
    if status == "completed":
        msg_url = f"{COZE_API_BASE}/v3/chat/message/list?conversation_id={conv_id}&chat_id={chat_id}"
        try:
            msgs = requests.get(msg_url, headers=headers, timeout=10).json().get("data", [])
            
            for m in msgs:
                if m["role"] == "assistant" and m["type"] == "answer":
                    st.success("调用成功！Bot 的回答是：")
                    st.write(m["content"])
                    break
            else:
                st.warning("已完成对话，但没有找到 answer 类型的消息。")
        except Exception as e:
            st.error(f"获取最终消息网络错误: {e}")
    else:
        st.warning("等待超时，Bot 依然在处理中（网络可能有波动，但连接断了也会自动重试）。")
