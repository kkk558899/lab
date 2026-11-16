from collections.abc import Iterator
from datetime import datetime, timedelta
import json
import time
from typing import Any

try:
    from langchain_core.messages import AIMessage, HumanMessage, SystemMessage, ToolMessage
    from langchain_openai import ChatOpenAI
    from langgraph.graph import START, MessagesState, StateGraph
    from langgraph.prebuilt import ToolNode, tools_condition
    HAS_LANGGRAPH = True
except ImportError:
    HAS_LANGGRAPH = False
    AIMessage = HumanMessage = SystemMessage = ToolMessage = None

from sqlalchemy.orm import Session

from app.common.exceptions import BusinessException
from app.config import settings
from app.models.equipment import Equipment
from app.models.user import User
from app.schemas.ai import ChatRequest
from app.services import agent_tools, kb_service, lab_service

SYSTEM_PROMPT = """你是智能实验室预约系统的 Agent，回答要简洁。
你可以：
1. 使用 search_lab_docs 查询实验室的规则、安全、开放时间等问题
2. 使用 list_open_labs / list_lab_equipments 查询真实的实验室和设备
3. 在用户进行了预约确认后，使用 create_lab_reservation 来进行真实的预约落库
4. 使用 get_today 来进行日期的换算

## 必须遵守
当用户提到了 今天、明天、后天 等日期相关的问题，请先调用 get_today 来获取日期，不要直接返回 我需要确定明天的具体日期。

在提交预约之前必须向用户复述：实验室ID与名称（或设备ID和名称）、日期、开始时间、结束时间。并得到用户确认再进行实际操作。
用户没说【确认】【确认预约】【就这样预约】等确定性回复之前，不要调用 create_lab_reservation。
工作流的确认环节里如果缺少了 lab_id，请先 list_open_labs 查到了 lab_id 再创建，不要瞎写。
工作流的确认环节里如果缺少了 equipment_id，请先 list_lab_equipments 查到了 equipment_id 再创建，不要瞎写。

预约成功后状态是待审核，必须管理员确认后实验室（或设备）才能使用。
不要瞎编数据库里没有的实验室或者设备信息。
如果是问开放时间或者实验室规则，优先调用 search_lab_docs，不要凭空回复。
"""

# 工具英文名 → 页面上给人看的中文过程文案
TOOL_LABELS = {
    "search_lab_docs": "检索实验室知识库",
    "list_open_labs": "查询开放实验室",
    "list_lab_equipments": "查询实验室设备",
    "create_lab_reservation": "提交预约",
    "get_today": "获取今天日期",
}

def _chunk_text(chunk: Any) -> str:
    """从模型流式 chunk 里抠出纯文本"""
    if chunk is None:
        return ""
    content = getattr(chunk, "content", None)
    if isinstance(content, str):
        return content
    if isinstance(content, list):
        parts = []
        for part in content:
            if isinstance(part, dict):
                parts.append(part.get("text") or "")
            elif isinstance(part, str):
                parts.append(part)
        return "".join(parts)
    return str(content) if content is not None else ""

def _tool_output_preview(output: Any, limit: int = 200) -> str:
    """把工具结果收成短预览，避免整段 JSON 刷到前端过程区"""
    if isinstance(output, ToolMessage):
        output = output.content
    text = output if isinstance(output, str) else str(output)
    return text if len(text) <= limit else text[:limit] + "…"

def _build_history(data: ChatRequest) -> list:
    """前端只传 user/assistant 文本，转成 LangChain 消息对象"""
    if not data.messages and data.message:
        from app.schemas.ai import ChatMessage
        data.messages = [ChatMessage(role="user", content=data.message.strip())]
    history = []
    for message in data.messages or []:
        if message.role == "user" and message.content.strip():
            history.append(HumanMessage(content=message.content.strip()))
        elif message.role == "assistant" and message.content.strip():
            history.append(AIMessage(content=message.content.strip()))
    if not history:
        raise BusinessException(message="请输入您要对话的内容")
    return history

def build_agent(db: Session, current_user: User):
    if not settings.LLM_API_KEY:
        raise BusinessException(message="未配置大模型 API Key，请在 .env 中配置 LLM_API_KEY")
    tools = agent_tools.build_tools(db, current_user)
    llm = ChatOpenAI(
        api_key=settings.LLM_API_KEY,
        base_url=settings.LLM_BASE_URL,
        model=settings.LLM_MODEL,
        temperature=0,
        streaming=True,
    ).bind_tools(tools)

    def agent_node(state: MessagesState):
        """langGraph 执行的工作流节点"""
        response = llm.invoke(state["messages"])
        return {"messages": [response]}

    graph = StateGraph(MessagesState)
    graph.add_node("agent", agent_node)
    graph.add_node("tools", ToolNode(tools))
    graph.add_edge(START, "agent")
    graph.add_conditional_edges("agent", tools_condition)
    graph.add_edge("tools", "agent")
    return graph.compile()

def _fallback_stream(db: Session, current_user: User, user_msg: str) -> Iterator[dict]:
    """当尚未配置 LLM_API_KEY 时，基于真实数据库和向量知识库自动应答，保证系统对话不中断"""
    q = user_msg.lower().strip()
    yield {"type": "status", "message": "正在解析问题并匹配知识库与实验室排期…"}
    time.sleep(0.05)

    notice = ""

    def _emit_tokens(text: str, chunk_size: int = 4):
        for i in range(0, len(text), chunk_size):
            yield {"type": "token", "content": text[i : i + chunk_size]}
            time.sleep(0.015)

    # 0. 查询个人预约申请记录与审批状态
    if any(k in q for k in ["我的预约", "预约记录", "审批状态", "申请记录"]):
        from app.services import reservation_service
        yield {
            "type": "tool_start",
            "name": "query_my_reservations",
            "label": "查询个人预约记录",
        }
        page = reservation_service.get_reservation_page_list(db, current_user, page=1, page_size=10)
        yield {
            "type": "tool_end",
            "name": "query_my_reservations",
            "label": "查询个人预约记录",
            "preview": f"成功查询到 {page.total} 条历史预约记录",
        }
        if not page.list:
            res_text = "您当前暂无历史实验室预约记录。您可以点击左侧「实验室列表」挑选空闲实验室发起预约！"
        else:
            status_names = {0: "🟡 待审核", 1: "🟢 已通过", 2: "🔴 已驳回", 3: "⚪ 已取消"}
            res_text = f"为您查询到最近 {len(page.list)} 条预约申请记录：\n\n"
            for r in page.list[:5]:
                st = status_names.get(r.status, "未知状态")
                res_text += f"- **{r.lab_name}**（{r.date} {r.start_time}-{r.end_time}）— **{st}**\n"
                if r.remark:
                    res_text += f"  - 申请事由：{r.remark}\n"
        yield from _emit_tokens(res_text)
        yield {"type": "done"}
        return

    # 1. 实验室开放情况
    if any(k in q for k in ["开放", "哪些", "实验室列表", "空闲", "有哪些"]):
        yield {
            "type": "tool_start",
            "name": "list_open_labs",
            "label": "查询开放实验室",
        }
        page = lab_service.get_lab_page_list(db, page=1, page_size=20, status=1)
        yield {
            "type": "tool_end",
            "name": "list_open_labs",
            "label": "查询开放实验室",
            "preview": f"成功查询到 {len(page.list)} 间开放实验室",
        }
        res_text = "为您查询到当前系统内开放的实验室列表如下：\n\n"
        for idx, lab in enumerate(page.list, 1):
            res_text += f"{idx}. **{lab.name}**（ID: {lab.id}）\n"
            res_text += f"   - 📍 地点：{lab.location} | 👥 容量：{lab.capacity} 人\n"
            res_text += f"   - ⏰ 开放时段：{lab.open_time} - {lab.close_time}\n"
            if lab.description:
                res_text += f"   - 📝 简介：{lab.description}\n"
        res_text += "\n您可以在左侧菜单进入「实验室预约」进行直接选定并提交申请。"
        yield from _emit_tokens(res_text + notice)
        yield {"type": "done"}
        return

    # 2. 设备查询 (如 4090, 显卡, 机械臂, 服务器, 设备)
    if any(k in q for k in ["设备", "4090", "显卡", "机械臂", "激光雷达", "相机", "示波器", "工作站"]):
        yield {
            "type": "tool_start",
            "name": "list_lab_equipments",
            "label": "查询实验室设备",
        }
        eqs = db.query(Equipment).filter(Equipment.status == 1).all()
        matched = []
        for eq in eqs:
            if any(k in eq.name.lower() or k in (eq.description or "").lower() or k in (eq.spec or "").lower() for k in ["4090", "显卡", "机械臂", "激光雷达", "相机", "示波器", "工作站"] if k in q):
                matched.append(eq)
        if not matched:
            matched = eqs[:6]

        yield {
            "type": "tool_end",
            "name": "list_lab_equipments",
            "label": "查询实验室设备",
            "preview": f"匹配到 {len(matched)} 项相关设备资产",
        }
        res_text = "为您检索到以下相关设备信息：\n\n"
        for eq in matched:
            lab_title = eq.lab.name if eq.lab else f"实验室 #{eq.lab_id}"
            res_text += f"- **{eq.name}**（规格：{eq.spec or '标准规格'}，数量：{eq.quantity}台）\n"
            res_text += f"  - 所属实验室：**{lab_title}**（ID: {eq.lab_id}）\n"
            if eq.description:
                res_text += f"  - 设备描述：{eq.description}\n"
        res_text += "\n如需借用或使用该设备，可点击对应的实验室发起预约。"
        yield from _emit_tokens(res_text + notice)
        yield {"type": "done"}
        return

    # 3. 规章制度、安全规范与开放时间 (RAG 检索 ChromaDB)
    if any(k in q for k in ["规范", "安全", "规则", "时间", "借用", "手册", "制度", "要求"]):
        yield {
            "type": "tool_start",
            "name": "search_lab_docs",
            "label": "检索实验室知识库",
        }
        doc_result = kb_service.search(user_msg)
        yield {
            "type": "tool_end",
            "name": "search_lab_docs",
            "label": "检索实验室知识库",
            "preview": "已检索到匹配的实验室规程与说明",
        }
        res_text = f"根据实验室知识库检索结果，为您梳理相关规则规范：\n\n{doc_result}\n"
        yield from _emit_tokens(res_text + notice)
        yield {"type": "done"}
        return

    # 4. 预约咨询与排期查验
    if any(k in q for k in ["预约", "明天", "后天", "排期", "约"]):
        yield {
            "type": "tool_start",
            "name": "get_today",
            "label": "获取今天日期",
        }
        today_str = datetime.now().strftime("%Y-%m-%d")
        tomorrow_str = (datetime.now() + timedelta(days=1)).strftime("%Y-%m-%d")
        yield {
            "type": "tool_end",
            "name": "get_today",
            "label": "获取今天日期",
            "preview": f"今天: {today_str}, 明天: {tomorrow_str}",
        }
        res_text = (
            f"📅 今天是 **{today_str}**，明天是 **{tomorrow_str}**。\n\n"
            "智能预约完整流程如下：\n"
            "1. **选择实验室与设备**：您可以查看当前开放中的实验室，确认所需的工位与设备。\n"
            "2. **提交预约申请**：确定预约日期（如 " + tomorrow_str + "）及具体时段后，提交系统；系统将自动检测时段冲突。\n"
            "3. **管理员审核**：提交后初始状态为【待审核】，管理员在后台审核通过后即可按时前往使用。\n\n"
            "💡 若需要直接提交预约，可在左侧导航点击 **「实验室预约」** 菜单一键发起！"
        )
        yield from _emit_tokens(res_text + notice)
        yield {"type": "done"}
        return

    # 5. 默认兜底：RAG 检索加通用导航
    yield {
        "type": "tool_start",
        "name": "search_lab_docs",
        "label": "检索实验室知识库",
    }
    doc_result = kb_service.search(user_msg)
    yield {
        "type": "tool_end",
        "name": "search_lab_docs",
        "label": "检索实验室知识库",
        "preview": "知识库检索完成",
    }
    res_text = (
        "您好！我是智能实验室助手。您可以向我咨询：\n"
        "- 🏢 **实验室排期**：如「现在有哪些开放的实验室？」\n"
        "- 💻 **设备与算力**：如「哪个实验室有 RTX4090 显卡？」\n"
        "- 📜 **规范与制度**：如「请介绍一下实验室的安全规范与规则」\n"
        "- 📅 **预约流程**：如「如何预约实验室？」\n\n"
    )
    if doc_result and doc_result != "没有检索到相关的资料":
        res_text += f"**相关知识库资料**：\n{doc_result}\n\n"
    yield from _emit_tokens(res_text + notice)
    yield {"type": "done"}

def run_agent(db: Session, current_user: User, data: ChatRequest) -> str:
    """整包非流式运行 Agent"""
    history = _build_history(data)
    user_msg = ""
    for msg in reversed(history):
        if isinstance(msg, HumanMessage) and msg.content.strip():
            user_msg = msg.content.strip()
            break
    if not user_msg and data.message:
        user_msg = data.message.strip()

    if not settings.LLM_API_KEY:
        tokens = []
        for event in _fallback_stream(db, current_user, user_msg):
            if event.get("type") == "token":
                tokens.append(event.get("content", ""))
        return "".join(tokens)

    if not HAS_LANGGRAPH:
        from app.services import ai_service
        return ai_service.chat(db, data)

    agent = build_agent(db, current_user)
    try:
        result = agent.invoke(
            {"messages": [SystemMessage(content=SYSTEM_PROMPT), *history]},
            config={"recursion_limit": 10},
        )
    except BusinessException:
        raise
    except Exception as exc:
        raise BusinessException(message=f"大模型调用失败：{exc}")

    messages = result.get("messages") or []
    if not messages:
        raise BusinessException(message="大模型没有任何返回内容")
    for message in reversed(messages):
        if isinstance(message, AIMessage) and message.content.strip():
            content = message.content.strip()
            if isinstance(content, list):
                content = "".join(
                    part.get("text", "") if isinstance(part, dict) else str(part)
                    for part in content
                )
            if str(content).strip():
                return str(content).strip()
    return ""

def stream_agent(
    db: Session, current_user: User, data: ChatRequest
) -> Iterator[dict]:
    """生成器：边跑 Agent 边 yield 事件，供 SSE 推给前端"""
    history = _build_history(data)
    user_msg = ""
    for msg in reversed(history):
        if isinstance(msg, HumanMessage) and msg.content.strip():
            user_msg = msg.content.strip()
            break
    if not user_msg and data.message:
        user_msg = data.message.strip()

    # 如果尚未配置 LLM_API_KEY，优雅回退到本地知识库与规则引擎，确保系统可顺畅对话演示
    if not settings.LLM_API_KEY:
        yield from _fallback_stream(db, current_user, user_msg)
        return

    if not HAS_LANGGRAPH:
        from app.services import ai_service
        yield {"type": "status", "message": "正在思考…"}
        content = ai_service.chat(db, data)
        yield {"type": "token", "content": content}
        yield {"type": "done"}
        return

    try:
        agent = build_agent(db, current_user)
        inputs = {"messages": [SystemMessage(content=SYSTEM_PROMPT), *history]}

        yield {"type": "status", "message": "正在思考…"}

        for mode, payload in agent.stream(
            inputs,
            stream_mode=["messages", "updates"],
            config={"recursion_limit": 10},
        ):
            if mode == "messages":
                chunk, meta = payload
                node = (meta or {}).get("langgraph_node")
                # 工具调用开始
                if node == "agent" and getattr(chunk, "tool_calls", None):
                    for tc in chunk.tool_calls:
                        name = tc.get("name") or ""
                        yield {
                            "type": "tool_start",
                            "name": name,
                            "label": TOOL_LABELS.get(name, name),
                        }
                # 工具调用完成
                elif node == "tools" or isinstance(chunk, ToolMessage):
                    name = getattr(chunk, "name", "") or ""
                    yield {
                        "type": "tool_end",
                        "name": name,
                        "label": TOOL_LABELS.get(name, name),
                        "preview": _tool_output_preview(getattr(chunk, "content", "")),
                    }
                # 模型流式生成文本
                elif node == "agent":
                    text = _chunk_text(chunk)
                    if text:
                        yield {"type": "token", "content": text}

        yield {"type": "done"}
    except BusinessException as exc:
        yield {"type": "error", "message": exc.message}
    except Exception as exc:
        err_msg = str(exc)
        if "AuthenticationError" in type(exc).__name__ or "401" in err_msg:
            yield {
                "type": "error",
                "message": "大模型认证失败 (401)：当前配置的 API Key 无效或未授权，请检查 .env 中的 LLM_API_KEY 是否有效及对应平台是否正确",
            }
        elif "RateLimitError" in type(exc).__name__ or "429" in err_msg:
            yield {
                "type": "error",
                "message": "大模型调用受限 (429)：账户余额不足或请求频率超限，请检查大模型账户余额",
            }
        else:
            yield {"type": "error", "message": f"大模型调用失败：{err_msg}"}
