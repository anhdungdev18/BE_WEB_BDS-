# chatbot/answering.py
from typing import Iterable, Any
from common.openai_client import get_openai_client
from chatbot.models import ChatTurn
from listings.models import Post

# Dùng đúng model gói VIP của huynh
from accounts.models.membership_plan import MembershipPlan

MODEL_ANSWER = "gpt-4.1-mini"


def json_to_text(value: Any) -> str:
    """
    Chuyển JSON (dict/list/primitive) thành chuỗi text gọn gàng
    để hiển thị và cho LLM "đọc hiểu".
    """
    import numbers

    if value is None:
        return ""
    if isinstance(value, str):
        return value
    if isinstance(value, numbers.Number):
        return str(value)
    if isinstance(value, dict):
        parts = []
        for k, v in value.items():
            t = json_to_text(v)
            if t:
                parts.append(f"{k}: {t}")
        return ", ".join(parts)
    if isinstance(value, (list, tuple)):
        parts = [json_to_text(v) for v in value]
        return ", ".join([p for p in parts if p])
    return str(value)


# ====================== BĐS (POST) ======================

def build_listings_context(listings: Iterable[Post]) -> str:
    """
    Tạo context dạng text cho LLM, đọc địa chỉ từ JSONField `address`.
    """
    listings = list(listings)
    if not listings:
        return "KHÔNG CÓ BẤT ĐỘNG SẢN NÀO TRONG DANH SÁCH."

    rows = []
    for p in listings:
        addr_text = json_to_text(p.address)

        rows.append(
            f"- Mã tin {p.id}: {p.title}\n"
            f"  Địa chỉ: {addr_text}\n"
            f"  Diện tích: {p.area} m2\n"
            f"  Giá: {float(p.price):,.0f} VND\n"
            f"  Link: https://webbds.example.com/tin/{p.id}\n"
        )
    return "\n".join(rows)


def build_short_history(turns: Iterable[ChatTurn], max_len: int = 3) -> str:
    turns = list(turns)[-max_len:]
    buf = []
    for t in turns:
        prefix = "Người dùng" if t.role == "user" else "Chatbot"
        buf.append(f"{prefix}: {t.message}")
    return "\n".join(buf)


def answer_property_search(
    question: str,
    listings: Iterable[Post],
    history: Iterable[ChatTurn],
) -> str:
    client = get_openai_client()
    context = build_listings_context(listings)
    short_history = build_short_history(history)

    system_prompt = f"""
Bạn là chatbot bất động sản của một website BĐS Việt Nam.

- Luôn trả lời bằng tiếng Việt, thân thiện, dễ hiểu.
- Chỉ sử dụng thông tin từ danh sách BĐS dưới đây (data lấy trực tiếp từ DB).
- Nếu danh sách rỗng hoặc là chuỗi "KHÔNG CÓ BẤT ĐỘNG SẢN NÀO TRONG DANH SÁCH." thì hãy nói rõ là hiện tại chưa có tin phù hợp
  và gợi ý người dùng thay đổi tiêu chí (ví dụ nới giá, đổi khu vực...).
- Có thể so sánh, tóm tắt, gợi ý một vài tin nổi bật.

Lịch sử hội thoại gần đây:
{short_history}

Dữ liệu BĐS:
{context}
"""

    resp = client.responses.create(
        model=MODEL_ANSWER,
        input=[
            {
                "role": "system",
                "content": [{"type": "input_text", "text": system_prompt}],
            },
            {
                "role": "user",
                "content": [{"type": "input_text", "text": question}],
            },
        ],
    )
    return resp.output_text


# ====================== GÓI VIP (MembershipPlan) ======================

def build_membership_context(plans):
    """
    Tạo context text từ các gói VIP (MembershipPlan) trong DB.
    Chỉ nên truyền vào các gói is_active=True.
    """
    plans = list(plans)
    if not plans:
        return "HIỆN TẠI CHƯA CÓ GÓI VIP NÀO ĐƯỢC CẤU HÌNH."

    rows = []
    for p in plans:
        # Model của huynh:
        # code, name, price_vnd, duration_days, is_active
        code = p.code
        name = p.name
        price_vnd = p.price_vnd
        duration_days = p.duration_days

        # convert ngày -> text (tháng nếu chia hết cho 30)
        if duration_days % 30 == 0:
            duration_text = f"{duration_days // 30} tháng"
        else:
            duration_text = f"{duration_days} ngày"

        line = f"- Mã gói: {code}\n"
        line += f"  Tên gói: {name}\n"
        line += f"  Thời hạn: {duration_text}\n"
        try:
            line += f"  Giá: {float(price_vnd):,.0f} VND\n"
        except Exception:
            line += f"  Giá: {price_vnd} VND\n"

        rows.append(line)

    return "\n".join(rows)


def answer_membership(
    question: str,
    history: Iterable[ChatTurn],
    plans=None,
) -> str:
    """
    Trả lời câu hỏi về các gói VIP dựa trên dữ liệu thực tế trong DB.
    """
    client = get_openai_client()

    if plans is None:
        # chỉ lấy gói đang active
        plans = MembershipPlan.objects.filter(is_active=True)

    membership_context = build_membership_context(plans)
    short_history = build_short_history(history)

    system_prompt = f"""
Bạn là chatbot CSKH của website bất động sản.

Nhiệm vụ:
- Giải thích chi tiết và dễ hiểu về các gói VIP / gói nâng cấp tài khoản.
- Chỉ dựa trên thông tin từ danh sách gói bên dưới (data lấy từ DB).
- So sánh các gói, gợi ý gói phù hợp theo nhu cầu người dùng (thời gian, giá tiền, tần suất đăng tin).
- Trả lời bằng TIẾNG VIỆT, xưng "em" với người dùng.

Lịch sử hội thoại gần đây:
{short_history}

Danh sách gói VIP hiện có:
{membership_context}
    """.strip()

    resp = client.responses.create(
        model=MODEL_ANSWER,
        input=[
            {
                "role": "system",
                "content": [{"type": "input_text", "text": system_prompt}],
            },
            {
                "role": "user",
                "content": [{"type": "input_text", "text": question}],
            },
        ],
    )
    return resp.output_text
# ====================== FAQ / HƯỚNG DẪN SỬ DỤNG ======================

def answer_faq(
    question: str,
    history: Iterable[ChatTurn],
) -> str:
    """
    Trả lời các câu hỏi FAQ chung chung về cách dùng website, tính năng, v.v.
    Hiện tại trả lời ở mức tổng quát (chưa đọc dữ liệu riêng từ DB).
    """
    client = get_openai_client()
    short_history = build_short_history(history)

    system_prompt = """
Bạn là chatbot hỗ trợ người dùng cho một website bất động sản.

- Trả lời bằng TIẾNG VIỆT, xưng "em" với người dùng.
- Giải thích cách sử dụng các chức năng cơ bản: đăng ký, đăng nhập, tìm kiếm BĐS,
  lọc theo khu vực, giá, diện tích, đăng tin, nâng cấp gói VIP, v.v.
- Không bịa ra những chức năng phức tạp mà hệ thống chưa chắc có; 
  hãy nói chung chung theo kiểu: "Anh/chị có thể vào mục X trên thanh menu..."
- Với câu hỏi kiểu "web này dùng sao vậy?" hãy trả lời bằng vài bước rõ ràng, dễ hiểu:
  1) xem tin
  2) tìm kiếm / lọc
  3) đăng ký tài khoản
  4) đăng tin / nâng cấp VIP (nếu muốn)
    """.strip()

    resp = client.responses.create(
        model=MODEL_ANSWER,
        input=[
            {
                "role": "system",
                "content": [{"type": "input_text", "text": system_prompt}],
            },
            {
                "role": "user",
                "content": [{"type": "input_text", "text": question}],
            },
        ],
    )
    return resp.output_text
