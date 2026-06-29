import os
import json
import uuid
from datetime import datetime

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from app.core.database import get_db
from app.models.models import *
from app.schemas.schemas import *

router = APIRouter(prefix="/api/v1/ai", tags=["AI"])


async def _call_deepseek_api(messages: list[dict]) -> dict:
    """
    Try to call DeepSeek API via httpx.
    Fall back to mock response if DEEPSEEK_API_KEY is not set.
    """
    api_key = os.environ.get("DEEPSEEK_API_KEY")
    if not api_key:
        return _mock_ai_response(messages)

    try:
        import httpx

        async with httpx.AsyncClient(timeout=30.0) as client:
            payload = {
                "model": "deepseek-chat",
                "messages": messages,
                "temperature": 0.7,
                "max_tokens": 2048,
            }
            resp = await client.post(
                "https://api.deepseek.com/v1/chat/completions",
                headers={
                    "Authorization": f"Bearer {api_key}",
                    "Content-Type": "application/json",
                },
                json=payload,
            )
            resp.raise_for_status()
            data = resp.json()
            content = data["choices"][0]["message"]["content"]
            return {
                "answer": content,
                "citations": [],
            }
    except Exception as e:
        # Fallback to mock on any error
        return _mock_ai_response(messages, error_context=str(e))


def _mock_ai_response(messages: list[dict], error_context: str = "") -> dict:
    """Generate a mock AI response for MVP."""
    last_message = messages[-1]["content"] if messages else ""

    system_prompt = (
        "你是一名高考志愿填报专家助手。请根据用户的问题提供专业、详细的回答。"
        "回答应包括具体建议、注意事项，并在最后附上免责声明。"
    )

    return {
        "answer": (
            f"您好！我是高考志愿填报助手。\n\n"
            f"您的问题是：{last_message}\n\n"
            f"**建议分析**\n"
            f"根据您的情况，建议您从以下几个方面考虑志愿填报：\n\n"
            f"1. **院校层次选择**：结合您的分数和位次，建议采用“冲稳保”策略，"
            f"即选择一部分略高于您位次的院校作为冲刺目标，一部分匹配的院校作为稳妥选择，"
            f"以及一部分低于您位次的院校作为保底。\n\n"
            f"2. **专业方向**：建议结合个人兴趣、学科优势以及就业前景综合考量。"
            f"热门专业如计算机科学与技术、人工智能、电子信息等竞争较激烈，"
            f"但就业前景较好。\n\n"
            f"3. **地域因素**：不同城市的就业机会、生活成本差异较大，"
            f"建议综合考虑。\n\n"
            f"4. **招生政策**：请仔细阅读目标院校的招生章程，"
            f"了解专业录取规则、体检要求等。\n\n"
            f"---\n"
            f"*该回答仅供参考，最终以官方填报系统和高校招生章程为准。*"
        ),
        "citations": [],
    }


@router.post("/conversations")
async def create_conversation(
    body: ConversationCreate = None,
    db: AsyncSession = Depends(get_db),
):
    if body is None:
        body = ConversationCreate(report_id="", title="新对话")

    # Verify report exists if report_id is provided
    if body.report_id:
        report_result = await db.execute(
            select(Report).where(Report.id == body.report_id)
        )
        if not report_result.scalar_one_or_none():
            raise HTTPException(status_code=404, detail="Report not found")

    conversation = AIConversation(
        report_id=body.report_id,
        title=body.title,
    )
    db.add(conversation)
    await db.commit()
    await db.refresh(conversation)

    return {
        "success": True,
        "code": "OK",
        "message": "conversation created",
        "data": {
            "id": conversation.id,
            "report_id": conversation.report_id,
            "title": conversation.title,
            "created_at": conversation.created_at.isoformat(),
        },
    }


@router.get("/conversations/{conv_id}")
async def get_conversation(
    conv_id: str,
    db: AsyncSession = Depends(get_db),
):
    result = await db.execute(
        select(AIConversation).where(AIConversation.id == conv_id)
    )
    conversation = result.scalar_one_or_none()
    if not conversation:
        raise HTTPException(status_code=404, detail="Conversation not found")

    # Get messages
    msg_result = await db.execute(
        select(AIChatMessage)
        .where(AIChatMessage.conversation_id == conv_id)
        .order_by(AIChatMessage.created_at.asc())
    )
    messages = msg_result.scalars().all()

    return {
        "success": True,
        "code": "OK",
        "message": "success",
        "data": {
            "id": conversation.id,
            "report_id": conversation.report_id,
            "title": conversation.title,
            "created_at": conversation.created_at.isoformat(),
            "messages": [
                {
                    "id": msg.id,
                    "role": msg.role,
                    "content": msg.content,
                    "citations": msg.citations,
                    "created_at": msg.created_at.isoformat(),
                }
                for msg in messages
            ],
        },
    }


@router.post("/conversations/{conv_id}/messages")
async def send_message(
    conv_id: str,
    body: MessageCreate,
    db: AsyncSession = Depends(get_db),
):
    # Verify conversation exists
    conv_result = await db.execute(
        select(AIConversation).where(AIConversation.id == conv_id)
    )
    conversation = conv_result.scalar_one_or_none()
    if not conversation:
        raise HTTPException(status_code=404, detail="Conversation not found")

    # Save user message
    user_msg = AIChatMessage(
        conversation_id=conv_id,
        role="user",
        content=body.message,
    )
    db.add(user_msg)
    await db.commit()
    await db.refresh(user_msg)

    # Get previous messages for context
    msg_result = await db.execute(
        select(AIChatMessage)
        .where(AIChatMessage.conversation_id == conv_id)
        .order_by(AIChatMessage.created_at.asc())
    )
    all_messages = msg_result.scalars().all()

    # Build chat history for AI
    chat_messages = [
        {
            "role": "system",
            "content": (
                "你是高考志愿填报专家助手，擅长分析高考志愿填报策略、"
                "院校专业选择、录取概率评估等。请用中文回答，保持专业、准确、有帮助。"
            ),
        }
    ]
    for msg in all_messages:
        chat_messages.append({"role": msg.role, "content": msg.content})

    # Get AI response
    ai_result = await _call_deepseek_api(chat_messages)

    # Save assistant message
    assistant_msg = AIChatMessage(
        conversation_id=conv_id,
        role="assistant",
        content=ai_result["answer"],
        citations=ai_result.get("citations") or None,
    )
    db.add(assistant_msg)
    await db.commit()
    await db.refresh(assistant_msg)

    return {
        "success": True,
        "code": "OK",
        "message": "success",
        "data": {
            "user_message": {
                "id": user_msg.id,
                "role": user_msg.role,
                "content": user_msg.content,
                "created_at": user_msg.created_at.isoformat(),
            },
            "assistant_message": {
                "id": assistant_msg.id,
                "role": assistant_msg.role,
                "content": assistant_msg.content,
                "citations": assistant_msg.citations,
                "risk_notice": "该回答仅供参考，最终以官方填报系统和高校招生章程为准。",
                "created_at": assistant_msg.created_at.isoformat(),
            },
        },
    }


@router.get("/conversations")
async def list_conversations(
    report_id: str = None,
    db: AsyncSession = Depends(get_db),
):
    query = select(AIConversation).order_by(AIConversation.created_at.desc())
    if report_id:
        query = query.where(AIConversation.report_id == report_id)

    result = await db.execute(query)
    conversations = result.scalars().all()

    return {
        "success": True,
        "code": "OK",
        "message": "success",
        "data": {
            "conversations": [
                {
                    "id": conv.id,
                    "report_id": conv.report_id,
                    "title": conv.title,
                    "created_at": conv.created_at.isoformat(),
                }
                for conv in conversations
            ]
        },
    }
