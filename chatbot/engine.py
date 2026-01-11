# chatbot/engine.py
from typing import Dict, Any
from django.utils import timezone

from .models import ChatSession, ChatTurn, SearchContext
from .nlu import parse_nlu
from .retrievers.property_search import db_only_search, semantic_search, hybrid_search
from .answering import (
    answer_property_search,
    answer_membership,
    answer_faq,   # 💡 thêm hàm FAQ
)
from listings.models import Post  # có thể chưa dùng, nhưng để đây cũng không sao
from common.openai_client import get_openai_client

# Dùng đúng model gói VIP của huynh
from accounts.models.membership_plan import MembershipPlan


def get_or_create_session(session_id: str, user=None) -> ChatSession:
    obj, _ = ChatSession.objects.get_or_create(
        session_id=session_id,
        defaults={"user": user},
    )
    if user and obj.user is None:
        obj.user = user
    obj.last_activity = timezone.now()
    obj.save()
    return obj


def handle_message(session_id: str, user_message: str, user=None) -> Dict[str, Any]:
    session = get_or_create_session(session_id, user)

    # 1) Lưu turn user
    ChatTurn.objects.create(
        session=session,
        role="user",
        message=user_message,
    )

    # 2) Lấy history ngắn
    turns_qs = session.turns.all().order_by("created_at")
    recent_turns = list(turns_qs)
    short_history_text = "\n".join(
        f"{'User' if t.role == 'user' else 'Bot'}: {t.message}"
        for t in recent_turns[-6:]
    )

    # 3) NLU
    nlu = parse_nlu(user_message, short_history=short_history_text)
    intent = nlu.get("intent")
    property_filters = (
        nlu.get("property_search") or {}
        if intent == "property_search"
        else None
    )
    search_mode = nlu.get("search_mode")
    follow_up = bool(nlu.get("follow_up_on_previous") or False)

    # 4) Merge filter (chỉ khi property_search)
    filters = None
    if intent == "property_search":
        sc, _ = SearchContext.objects.get_or_create(
            session=session,
            defaults={"filters_json": {}, "last_result_ids": []},
        )
        base_filters = sc.filters_json or {}

        if follow_up:
            merged = {**base_filters}
            for k, v in (property_filters or {}).items():
                if v is not None:
                    merged[k] = v
        else:
            merged = property_filters or {}

        filters = merged

    results = []
    bot_answer = ""
    retrieved_ids = []

    # 5) Route theo intent
    if intent == "property_search":
        # ====== TÌM BĐS ======
        if search_mode == "db_only":
            posts = db_only_search(filters)
        elif search_mode == "semantic":
            posts = semantic_search(user_message)
        else:
            posts = hybrid_search(user_query=user_message, filters=filters)

        retrieved_ids = [p.id for p in posts]
        bot_answer = answer_property_search(user_message, posts, recent_turns)
        results = posts

        # Lưu lại context để follow-up
        SearchContext.objects.update_or_create(
            session=session,
            defaults={"filters_json": filters, "last_result_ids": retrieved_ids},
        )

    elif intent == "faq":
        # ====== FAQ / HƯỚNG DẪN SỬ DỤNG ======
        bot_answer = answer_faq(user_message, recent_turns)

    elif intent == "account_support":
        bot_answer = "Em cần được kết nối với API tài khoản để xem thông tin của anh/chị (hiện chưa triển khai)."

    elif intent == "membership_info":
        # ====== GÓI VIP (MembershipPlan) ======
        plans = MembershipPlan.objects.filter(is_active=True)
        bot_answer = answer_membership(user_message, recent_turns, plans)
        results = []  # không phải kết quả bài đăng

    else:  # "chitchat" hoặc intent lạ
        client = get_openai_client()
        system_prompt = """
Bạn là chatbot của một website bất động sản.
Nếu người dùng chỉ chào hỏi hoặc nói chuyện linh tinh,
hãy trả lời thân thiện, ngắn gọn bằng tiếng Việt
và gợi ý họ có thể hỏi về:
- tìm bất động sản (mua/bán/thuê)
- các gói VIP, quyền lợi, giá gói
        """.strip()

        resp = client.responses.create(
            model="gpt-4.1-mini",
            input=[
                {
                    "role": "system",
                    "content": [{"type": "input_text", "text": system_prompt}],
                },
                {
                    "role": "user",
                    "content": [{"type": "input_text", "text": user_message}],
                },
            ],
        )
        bot_answer = resp.output_text

    # 6) Lưu turn bot
    ChatTurn.objects.create(
        session=session,
        role="assistant",
        message=bot_answer,
        intent=intent,
        filters_json=filters,
        retrieved_ids=retrieved_ids,
    )

    return {
        "session_id": session.session_id,
        "answer": bot_answer,
        "intent": intent,
        "filters": filters,
        "results": results,
    }
