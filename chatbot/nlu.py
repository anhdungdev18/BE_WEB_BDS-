# chatbot/nlu.py
import json
from typing import Any, Dict
from common.openai_client import get_openai_client

MODEL_NLU = "gpt-4.1"  # huynh có thể đổi model nếu muốn


NLU_SYSTEM_PROMPT = """
Bạn là NLU router cho chatbot bất động sản.

Nhiệm vụ:

1) Phân loại intent:
   - "property_search": tìm bất động sản
   - "membership_info": hỏi về gói VIP, gói nâng cấp, quyền lợi, giá gói, thời hạn
   - "faq": hỏi về cách dùng website, phí, chính sách (không phải gói VIP cụ thể)
   - "account_support": hỏi về tài khoản của chính họ (đăng nhập, quên mật khẩu, đổi email, ...)
   - "chitchat": chào hỏi, nói chuyện bình thường

2) Nếu intent = "property_search":
   Trích xuất bộ lọc:
   {
     "property_type": "apartment" | "house" | "land" | null,
     "city": string | null,
     "district": string | null,
     "min_price": number | null,
     "max_price": number | null,
     "min_area": number | null,
     "max_area": number | null,
     "bedrooms_min": number | null
   }
   - Hiểu các cách nói như "tầm 2 tỷ", "khoảng 1.5-2 tỷ", "gần Thủ Đức".
   - Nếu không rõ thì để null.

3) search_mode:
   - "db_only": câu hỏi chủ yếu là điều kiện rõ ràng (giá, diện tích, khu vực...)
   - "semantic": câu hỏi thiên về cảm nhận, phong cách sống, mô tả mềm
   - "hybrid": kết hợp cả hai
   - Nếu intent KHÔNG PHẢI "property_search" thì search_mode phải là null.

4) follow_up_on_previous:
   - true nếu câu này phụ thuộc câu trước (ví dụ "lọc lại căn dưới 2 tỷ", "cho rẻ hơn tí")
   - false nếu là câu hỏi mới hoàn toàn.

5) Nếu intent KHÔNG PHẢI "property_search":
   - "property_search" phải là null.

Trả về JSON duy nhất, KHÔNG THÊM CHỮ NÀO BÊN NGOÀI:
{
  "intent": "property_search" | "membership_info" | "faq" | "account_support" | "chitchat",
  "property_search": { ... } | null,
  "search_mode": "db_only" | "semantic" | "hybrid" | null,
  "follow_up_on_previous": true/false
}
"""


def parse_nlu(user_message: str, short_history: str = "") -> Dict[str, Any]:
    client = get_openai_client()
    user_text = f"Lịch sử ngắn:\n{short_history}\n\nCâu hiện tại: {user_message}"

    resp = client.responses.create(
        model=MODEL_NLU,
        input=[
            {
                "role": "system",
                "content": [{"type": "input_text", "text": NLU_SYSTEM_PROMPT}],
            },
            {
                "role": "user",
                "content": [{"type": "input_text", "text": user_text}],
            },
        ],
    )
    raw = resp.output_text

    try:
        data = json.loads(raw)
    except json.JSONDecodeError:
        data = {}

    # ==== HẬU XỬ LÝ CHO CHẮC ĂN ====

    intent = data.get("intent", "chitchat")
    allowed_intents = [
        "property_search",
        "membership_info",
        "faq",
        "account_support",
        "chitchat",
    ]
    if intent not in allowed_intents:
        intent = "chitchat"

    property_search = data.get("property_search") if intent == "property_search" else None
    search_mode = data.get("search_mode") if intent == "property_search" else None
    follow_up = bool(data.get("follow_up_on_previous") or False)

    # đảm bảo keys luôn tồn tại
    return {
        "intent": intent,
        "property_search": property_search,
        "search_mode": search_mode,
        "follow_up_on_previous": follow_up,
    }
