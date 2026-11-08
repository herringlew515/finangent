import os
import time
from typing import Optional

import requests
from dotenv import load_dotenv


load_dotenv()

COZE_API_BASE = os.getenv("COZE_API_BASE", "https://api.coze.cn").rstrip("/")
COZE_TOKEN = os.getenv("COZE_TOKEN")
COZE_BOT_ID = os.getenv("COZE_BOT_ID")
REQUEST_TIMEOUT = 30
MAX_WAIT_SECONDS = int(os.getenv("COZE_MAX_WAIT_SECONDS", "300"))
POLL_INTERVAL_SECONDS = float(os.getenv("COZE_POLL_INTERVAL_SECONDS", "3"))


class CozeAPIError(RuntimeError):
    """Raised when a Coze request cannot be completed."""


def _headers() -> dict:
    if not COZE_TOKEN:
        raise CozeAPIError("未配置 COZE_TOKEN，请在 .env 文件中填写 Coze Token。")
    return {
        "Authorization": "Bearer " + COZE_TOKEN,
        "Content-Type": "application/json",
    }


def _check_response(response: requests.Response, action: str) -> dict:
    try:
        payload = response.json()
    except ValueError as error:
        raise CozeAPIError(
            f"{action}返回了无效响应（HTTP {response.status_code}）。"
        ) from error

    if response.status_code >= 400 or payload.get("code", 0) != 0:
        message = payload.get("msg") or response.text
        raise CozeAPIError(f"{action}失败：{message}")
    return payload


def ask_agent(question: str, user_id: str = "streamlit-user") -> str:
    """Ask Coze and return the assistant's raw answer text."""
    if not COZE_BOT_ID:
        raise CozeAPIError("未配置 COZE_BOT_ID，请在 .env 文件中填写 Bot ID。")
    if not COZE_BOT_ID.isdigit():
        raise CozeAPIError(
            "COZE_BOT_ID 格式错误：应填写 Coze 发布页中的纯数字 Bot ID，"
            "不能填写 Token、Bot 名称或其他 ID。"
        )

    headers = _headers()
    payload = {
        "bot_id": COZE_BOT_ID,
        "user_id": user_id,
        "stream": False,
        "auto_save_history": True,
        "additional_messages": [
            {"role": "user", "content": question, "content_type": "text"}
        ],
    }

    try:
        response = requests.post(
            f"{COZE_API_BASE}/v3/chat",
            headers=headers,
            json=payload,
            timeout=REQUEST_TIMEOUT,
        )
    except requests.RequestException as error:
        raise CozeAPIError(f"创建对话时网络请求失败：{error}") from error

    result = _check_response(response, "创建对话")
    chat_data = result.get("data") or {}
    conversation_id = chat_data.get("conversation_id")
    chat_id = chat_data.get("id")
    if not conversation_id or not chat_id:
        raise CozeAPIError("创建对话成功，但响应中缺少 conversation_id 或 chat_id。")

    status = _wait_for_completion(headers, conversation_id, chat_id)
    if status != "completed":
        raise CozeAPIError(f"对话未完成，当前状态：{status}")
    return _get_answer(headers, conversation_id, chat_id)


def _wait_for_completion(
    headers: dict, conversation_id: str, chat_id: str
) -> str:
    status_url = (
        f"{COZE_API_BASE}/v3/chat/retrieve"
        f"?conversation_id={conversation_id}&chat_id={chat_id}"
    )
    last_status: Optional[str] = None

    deadline = time.monotonic() + MAX_WAIT_SECONDS
    while time.monotonic() < deadline:
        time.sleep(POLL_INTERVAL_SECONDS)
        try:
            response = requests.get(
                status_url, headers=headers, timeout=REQUEST_TIMEOUT
            )
        except requests.RequestException as error:
            raise CozeAPIError(f"查询对话状态时网络请求失败：{error}") from error

        payload = _check_response(response, "查询对话状态")
        last_status = (payload.get("data") or {}).get("status")
        if last_status == "completed":
            return last_status
        if last_status in {"failed", "cancelled"}:
            return last_status

    return last_status or "timeout"


def _get_answer(headers: dict, conversation_id: str, chat_id: str) -> str:
    url = (
        f"{COZE_API_BASE}/v3/chat/message/list"
        f"?conversation_id={conversation_id}&chat_id={chat_id}"
    )
    try:
        response = requests.get(url, headers=headers, timeout=REQUEST_TIMEOUT)
    except requests.RequestException as error:
        raise CozeAPIError(f"获取回答时网络请求失败：{error}") from error

    messages = _check_response(response, "获取回答").get("data") or []
    for message in messages:
        if message.get("role") == "assistant" and message.get("type") == "answer":
            content = message.get("content")
            if content:
                return content
    raise CozeAPIError("对话已完成，但没有找到 assistant 的 answer 消息。")
