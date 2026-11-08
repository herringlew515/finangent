# 财务报表分析智能体

基于 Streamlit + Coze API 的财务报表分析系统，当前默认以比亚迪（002594.SZ）为分析对象，同时保留公司名称和股票代码配置，便于扩展其他上市公司。

## 功能

- 查询年度报告中的财务数据
- 计算毛利率、净利率、ROE、资产负债率等指标
- 展示证据来源和计算过程
- 通过 Coze 知识库和工作流生成回答
- 对无依据数据、股价预测和买卖建议进行拒答
- 解析 Coze 返回的双层 JSON 或平铺 JSON

## 系统结构

```text
用户
  ↓
Streamlit 前端
  ↓ HTTP API
Coze Bot
  ├─ 知识库检索
  ├─ 工作流
  └─ 计算工具
  ↓
结构化 JSON
  ↓
Streamlit 渲染
```

## 项目结构

```text
.
├── app.py                         # Streamlit 主界面
├── coze_api.py                    # Coze API 调用封装
├── example.py                     # 兼容入口
├── requirements.txt               # Python 依赖
├── .env.example                   # 环境变量模板
├── .gitignore                     # 忽略密钥和缓存
├── 交付物/                         # 评测集、实验报告和答辩材料
└── 金融智能体课程任务书.md        # 课程任务说明
```

## 环境要求

- Windows
- Python 3.10+
- 已发布的 Coze Bot
- Coze API Token 和 Bot ID

## 安装

在项目目录执行：

```powershell
python -m pip install -r requirements.txt
```

## 配置 Coze

复制环境变量模板：

```powershell
Copy-Item .env.example .env
```

编辑 `.env`：

```env
COZE_API_BASE=https://api.coze.cn
COZE_TOKEN=pat_你的真实Token
COZE_BOT_ID=你的纯数字Bot_ID
```

说明：

- `COZE_TOKEN` 是 Coze 个人访问令牌；
- `COZE_BOT_ID` 是 Coze 发布页中的 Bot ID，不是 Bot 名称；
- `.env` 已加入 `.gitignore`，不要提交真实 Token；
- 修改 `.env` 后需要重启 Streamlit。

## 运行

```powershell
python -m streamlit run app.py
```

打开浏览器访问：

```text
http://localhost:8501
```

## API 输入和输出

前端将用户问题和页面设置组合为文本发送给 Coze，例如：

```text
当前分析对象：比亚迪（股票代码：002594）。报告年度：2024。分析类型：比率计算。
用户问题：计算比亚迪2024年的毛利率。
```

Coze 结束节点应返回以下五个业务字段：

```json
{
  "answer": "比亚迪2024年毛利率为XX.XX%。",
  "evidence": "出处：比亚迪2024年年度报告 第X页，利润表",
  "calculation": "毛利率 =（营业收入 - 营业成本）/ 营业收入 × 100%",
  "confidence": "高",
  "disclaimer": "以上分析基于公开财报，仅供教学研究，不构成投资建议。"
}
```

如果 Coze 使用 `output` 字符串包装，以下格式也支持：

```json
{
  "output": "{\"answer\":\"...\",\"evidence\":\"...\",\"calculation\":\"...\",\"confidence\":\"高\",\"disclaimer\":\"...\"}"
}
```

前端会自动处理双层 JSON、平铺 JSON、Markdown 代码围栏和普通文本降级。

## Coze 知识库建议

建议在 Coze 中上传：

- 比亚迪 2024 年年度报告
- 比亚迪 2023 年年度报告
- 已实际收录的季度或半年度报告
- 财务比率公式和概念说明

知识库范围应与 Bot 的拒答规则保持一致。没有上传或没有可靠来源的数据，不应由智能体自行编造。

## 评测和课程交付物

`交付物/` 目录包含：

- `01_实验报告.md`
- `02_项目问题.md`
- `03_评测集.csv`
- `04_人机决策日志.csv`
- `05_对照实验数据表.csv`
- `06_原始记录.csv`
- `08_演示脚本.md`

评测结果中的引用准确性和计算可复算性需要结合原始年报人工核对后填写。

## 安全注意

- 不要提交 `.env`；
- 不要把 Token 写入 Python 源码；
- 不要把 Token 放进截图、实验报告或演示视频；
- 如果 Token 泄露，应立即在 Coze 中撤销并重新生成。

## 免责声明

本项目仅用于课程实验和财务数据分析演示，不构成任何投资建议。
