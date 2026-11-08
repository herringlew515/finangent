import json

import streamlit as st

from coze_api import CozeAPIError, ask_agent


st.set_page_config(
    page_title="财务报表分析助手",
    page_icon="📊",
    layout="wide",
)


DEFAULT_DISCLAIMER = "以上分析基于公开财报，仅供教学研究，不构成投资建议。"
FIELDS = ("answer", "evidence", "calculation", "confidence", "disclaimer")


def _strip_code_fence(text: str) -> str:
    text = (text or "").strip()
    if text.startswith("```"):
        lines = text.splitlines()
        lines = lines[1:] if lines else []
        if lines and lines[-1].strip() == "```":
            lines = lines[:-1]
        text = "\n".join(lines).strip()
    return text


def _normalize_answer(data: dict) -> dict:
    evidence = data.get("evidence", "")
    if isinstance(evidence, list):
        evidence = "；".join(
            str(item).strip() for item in evidence if str(item).strip()
        )
    else:
        evidence = str(evidence or "").strip()

    return {
        "answer": str(data.get("answer", "") or "").strip() or "（未收到回答）",
        "evidence": evidence,
        "calculation": str(data.get("calculation", "") or "").strip() or "无",
        "confidence": str(data.get("confidence", "") or "未标注").strip(),
        "disclaimer": str(data.get("disclaimer", "") or DEFAULT_DISCLAIMER).strip(),
    }


def parse_agent_json(raw_text: str) -> dict:
    """Parse Coze's wrapped or flat five-field response."""
    text = _strip_code_fence(raw_text)
    try:
        data = json.loads(text)
    except (TypeError, json.JSONDecodeError):
        return {
            "answer": text or "（未收到内容）",
            "evidence": "",
            "calculation": "无",
            "confidence": "低",
            "disclaimer": DEFAULT_DISCLAIMER,
        }

    if not isinstance(data, dict):
        raise ValueError("Coze 返回的内容不是 JSON 对象")

    if "output" in data and "answer" not in data:
        output = data["output"]
        if isinstance(output, dict):
            data = output
        elif isinstance(output, str):
            return parse_agent_json(output)

    if not set(data).intersection(FIELDS):
        raise ValueError("JSON 中没有找到业务字段")
    return _normalize_answer(data)


def render_answer(data: dict) -> None:
    st.markdown(data["answer"])

    evidence = data["evidence"].strip()
    if evidence:
        with st.expander("📚 证据来源（点击展开）"):
            for item in evidence.split("；"):
                if item.strip():
                    st.markdown(f"- {item.strip()}")

    calculation = data["calculation"].strip()
    if calculation and calculation != "无":
        with st.expander("🧮 计算过程（可复算）"):
            st.code(calculation, language="text")

    confidence = data["confidence"]
    confidence_colors = {"高": "🟢", "中": "🟡", "低": "🔴"}
    confidence_icon = confidence_colors.get(confidence, "⚪")
    st.markdown(
        f"**置信度：** {confidence_icon} {confidence}"
    )
    st.caption(data["disclaimer"])


if "messages" not in st.session_state:
    st.session_state.messages = []


with st.sidebar:
    st.header("⚙️ 查询设置")
    company = st.text_input("公司名称", value="比亚迪")
    stock_code = st.text_input("股票代码", value="002594")
    report_year = st.selectbox("报告年度", ["2024", "2023", "2025Q1"])
    analysis_type = st.selectbox(
        "分析类型",
        ["财报问答", "比率计算", "趋势分析", "概念解释"],
    )

    if st.button("🗑️ 清空对话", use_container_width=True):
        st.session_state.messages = []
        st.rerun()

    st.divider()
    st.caption("⚠️ 仅供教学研究，不构成投资建议")
    st.caption("数据来源：公司官方定期报告")


st.title("📊 财务报表分析助手")
st.caption(
    f"当前公司：**{company}**（{stock_code}） · "
    f"报告年度：**{report_year}** · 分析类型：**{analysis_type}**"
)

for message in st.session_state.messages:
    with st.chat_message(message["role"]):
        if message["role"] == "assistant" and message.get("data"):
            render_answer(message["data"])
        else:
            st.markdown(message["content"])


if prompt := st.chat_input("例如：2024年营业收入是多少？"):
    contextual_prompt = (
        f"当前分析对象：{company}（股票代码：{stock_code}）。"
        f"报告年度：{report_year}。分析类型：{analysis_type}。\n"
        f"用户问题：{prompt}"
    )
    st.session_state.messages.append({"role": "user", "content": prompt})

    with st.chat_message("user"):
        st.markdown(prompt)

    with st.chat_message("assistant"):
        try:
            with st.spinner("正在请求 Coze 智能体..."):
                raw_answer = ask_agent(contextual_prompt)
            answer_data = parse_agent_json(raw_answer)
            render_answer(answer_data)
            st.session_state.messages.append(
                {
                    "role": "assistant",
                    "content": answer_data["answer"],
                    "data": answer_data,
                }
            )
        except CozeAPIError as error:
            st.error(f"Coze 接口调用失败：{error}")
        except (json.JSONDecodeError, ValueError) as error:
            st.error(f"Coze 返回格式不符合约定：{error}")
            st.code(raw_answer if "raw_answer" in locals() else "", language="text")
        except Exception as error:
            st.error(f"程序运行失败：{error}")
