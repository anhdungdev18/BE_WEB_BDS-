# accounts/views/membership.py

from django.db import transaction
from django.utils import timezone
from django.shortcuts import get_object_or_404
from django.db.models import Q

from rest_framework.views import APIView
from rest_framework.generics import ListAPIView
from rest_framework.permissions import IsAuthenticated, IsAdminUser
from rest_framework.exceptions import PermissionDenied
from rest_framework.response import Response
from rest_framework import status
from rest_framework.pagination import PageNumberPagination

from accounts.models import (
    MembershipPlan,
    MembershipOrder,
    UserMembership,
)
from accounts.utils.vietqr import build_vietqr_url
from accounts.serializers import (
    MembershipOrderListSerializer,
    VipUserListSerializer,
    MembershipPlanSerializer,
)

from accounts.services.membership_services import (
    mark_order_paid_and_activate, get_active_membership
)
from accounts.services.authz import is_admin_like


class MembershipUpgradeInitAPIView(APIView):
    """
    User (MEMBER) gọi API này để khởi tạo đơn nâng cấp lên AGENT (VIP tài khoản).

    POST /api/accounts/membership/upgrade/init/
    Body (optional):
    {
      "plan_code": "AGENT_1M"   // mặc định nếu không gửi
    }

    Nếu đã có 1 order PENDING cho cùng user + plan:
        -> KHÔNG tạo order mới
        -> Trả lại order cũ + QR cũ.
    """

    permission_classes = [IsAuthenticated]

    @transaction.atomic
    def post(self, request):
        user = request.user
        plan_code = request.data.get("plan_code", "AGENT_1M")

        # 1. Lấy gói cần nâng cấp (chỉ lấy gói đang active)
        plan = get_object_or_404(
            MembershipPlan,
            code=plan_code,
            is_active=True,
        )

        # 2. Tìm order PENDING cũ (nếu có) cho cùng user + plan
        existing_order = (
            MembershipOrder.objects
            .filter(
                user=user,
                plan=plan,
                status=MembershipOrder.Status.PENDING,
            )
            .order_by("-created_at")
            .first()
        )

        created_new = False

        if existing_order:
            # Dùng lại order cũ
            order = existing_order
            transfer_note = order.transfer_note
            qr_url = order.qr_image_url

            # Nếu vì lý do gì đó chưa có transfer_note hoặc qr thì generate lại
            if not transfer_note:
                transfer_note = f"UPGRADE_USER_{user.id}_ORDER_{order.id}"
                order.transfer_note = transfer_note

            if not qr_url:
                qr_url = build_vietqr_url(
                    amount_vnd=order.amount_vnd,
                    transfer_note=transfer_note,
                )
                order.qr_image_url = qr_url

            order.save(update_fields=["transfer_note", "qr_image_url"])
        else:
            # 3. Không có order cũ -> tạo order mới PENDING
            order = MembershipOrder.objects.create(
                user=user,
                plan=plan,
                amount_vnd=plan.price_vnd,
                status=MembershipOrder.Status.PENDING,
                transfer_note="TEMP",  # tạm, lát update lại
            )

            # 4. Sinh nội dung chuyển khoản (transfer_note) gắn với user + order
            transfer_note = f"UPGRADE_USER_{user.id}_ORDER_{order.id}"

            # 5. Build URL ảnh QR VietQR
            qr_url = build_vietqr_url(
                amount_vnd=order.amount_vnd,
                transfer_note=transfer_note,
            )

            # 6. Cập nhật lại order
            order.transfer_note = transfer_note
            order.qr_image_url = qr_url
            order.save(update_fields=["transfer_note", "qr_image_url"])

            created_new = True

        # 7. Trả dữ liệu cho FE
        data = {
            "ok": 1,
            "is_new_order": created_new,        # True: vừa tạo, False: dùng lại
            "order_id": order.id,
            "user_id": user.id,
            "plan_code": plan.code,
            "amount_vnd": order.amount_vnd,
            "transfer_note": order.transfer_note,
            "qr_image_url": order.qr_image_url,
            "status": order.status,
            "created_at": order.created_at,
        }
        return Response(data, status=status.HTTP_201_CREATED)


class MembershipOrderMarkPaidAPIView(APIView):
    """
    Admin xác nhận 1 order đã được thanh toán,
    KHÔNG cần nhập số tiền.
    
    POST /api/accounts/membership/orders/mark-paid/
    Body:
    {
      "order_id": 5,
      "bank_ref": "MB123456789"   // optional
    }
    """

    permission_classes = [IsAuthenticated, IsAdminUser]

    @transaction.atomic
    def post(self, request):
        order_id = request.data.get("order_id")
        bank_ref = request.data.get("bank_ref", "")

        # 1. Validate input
        if not order_id:
            return Response(
                {"ok": 0, "error": "order_id_required"},
                status=status.HTTP_400_BAD_REQUEST,
            )

        # 2. Lấy order
        order = get_object_or_404(MembershipOrder, id=order_id)

        # 3. Order phải đang ở trạng thái PENDING
        if order.status != MembershipOrder.Status.PENDING:
            return Response(
                {"ok": 0, "error": "ORDER_NOT_PENDING"},
                status=status.HTTP_400_BAD_REQUEST,
            )

        # 4. Đánh dấu PAID + kích hoạt / gia hạn VIP tài khoản (UserMembership + role AGENT)
        order = mark_order_paid_and_activate(order, bank_ref=bank_ref)

        user = order.user
        membership = getattr(user, "membership", None)

        return Response(
            {
                "ok": 1,
                "message": "ORDER_MARKED_PAID_AND_VIP_ACTIVATED",
                "order_id": order.id,
                "user_id": user.id,
                "plan_code": order.plan.code,
                "status": order.status,
                "paid_at": order.paid_at,
                "expired_at": getattr(membership, "expired_at", None),
            },
            status=status.HTTP_200_OK,
        )


class MembershipOrderPagination(PageNumberPagination):
    page_size = 20
    page_size_query_param = "page_size"
    max_page_size = 100


class MembershipOrderListAPIView(ListAPIView):
    """
    GET /api/accounts/membership/orders/
        ?status=PENDING|PAID|CANCELLED (default=PENDING)
        &search=...
        &page=1&page_size=20

    -> Dùng cho màn admin list yêu cầu nâng cấp (list giao dịch).
    """

    permission_classes = [IsAuthenticated, IsAdminUser]
    serializer_class = MembershipOrderListSerializer
    pagination_class = MembershipOrderPagination

    def get_queryset(self):
        qs = (
            MembershipOrder.objects
            .select_related("user", "plan")
            .all()
        )

        # Lọc theo status: mặc định PENDING
        status_param = self.request.query_params.get("status", "PENDING").upper()
        valid_status = [choice[0] for choice in MembershipOrder.Status.choices]
        if status_param in valid_status:
            qs = qs.filter(status=status_param)

        # Search theo email / username / transfer_note / plan_name
        search = self.request.query_params.get("search")
        if search:
            qs = qs.filter(
                Q(user__email__icontains=search)
                | Q(user__username__icontains=search)
                | Q(transfer_note__icontains=search)
                | Q(plan__name__icontains=search)
            )

        return qs.order_by("-created_at")
class MembershipMeAPIView(APIView):
    """
    GET /api/accounts/membership/me/

    Trả về trạng thái VIP hiện tại của user đang đăng nhập:
    {
      "is_vip": true/false,
      "plan_code": "AGENT_1M",
      "plan_name": "VIP 1 tháng",
      "started_at": "...",
      "expired_at": "...",
      "remaining_days": 12
    }
    """

    permission_classes = [IsAuthenticated]

    def get(self, request, *args, **kwargs):
        user = request.user

        # Hàm này vừa check hết hạn, vừa tự tắt AGENT nếu expired
        mem = get_active_membership(user)

        if mem is None:
            data = {
                "is_vip": False,
                "plan_code": None,
                "plan_name": None,
                "started_at": None,
                "expired_at": None,
                "remaining_days": 0,
            }
        else:
            plan = mem.plan
            data = {
                "is_vip": True,
                "plan_code": plan.code if plan else None,
                "plan_name": plan.name if plan else None,
                "started_at": mem.started_at,
                "expired_at": mem.expired_at,
                "remaining_days": mem.remaining_days(),
            }

        return Response(data)


class VipUserListAPIView(ListAPIView):
    """
    GET /api/accounts/membership/vip-users/
    Trả về danh sách user VIP còn hiệu lực (kèm ngày bắt đầu/hết hạn).
    """

    permission_classes = [IsAuthenticated, IsAdminUser]
    serializer_class = VipUserListSerializer

    def get_queryset(self):
        now = timezone.now()
        return (
            UserMembership.objects
            .select_related("user", "plan")
            .filter(expired_at__gt=now)
            .order_by("-started_at")
        )


class MembershipPlanListAPIView(ListAPIView):
    """
    GET /api/accounts/membership/plans/
    Trả về danh sách gói VIP đang active.
    """

    permission_classes = [IsAuthenticated]
    serializer_class = MembershipPlanSerializer

    def get_queryset(self):
        return MembershipPlan.objects.filter(is_active=True).order_by("price_vnd")


class MembershipOrderByUserAPIView(ListAPIView):
    """
    GET /api/accounts/users/<user_id>/membership/orders/
    Trả về lịch sử các gói VIP user đã đăng ký (mọi trạng thái).
    """

    permission_classes = [IsAuthenticated]
    serializer_class = MembershipOrderListSerializer
    pagination_class = MembershipOrderPagination

    def get_queryset(self):
        user_id = self.kwargs.get("user_id")
        if not is_admin_like(self.request.user) and str(self.request.user.id) != str(user_id):
            raise PermissionDenied("NO_PERMISSION_VIEW_USER_MEMBERSHIP_ORDERS")
        return (
            MembershipOrder.objects
            .select_related("user", "plan")
            .filter(user_id=user_id)
            .order_by("-created_at")
        )
