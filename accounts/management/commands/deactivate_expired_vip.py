from django.core.management.base import BaseCommand
from django.utils import timezone

from accounts.models import UserMembership, Role, UserRole


class Command(BaseCommand):
    help = "Disable AGENT role for users with expired VIP memberships."

    def handle(self, *args, **options):
        now = timezone.now()
        expired_memberships = UserMembership.objects.filter(expired_at__lte=now)

        if not expired_memberships.exists():
            self.stdout.write(self.style.SUCCESS("No expired memberships found."))
            return

        try:
            agent_role = Role.objects.get(role_name="AGENT")
        except Role.DoesNotExist:
            self.stdout.write(self.style.WARNING("Role AGENT not found."))
            return

        user_ids = list(expired_memberships.values_list("user_id", flat=True))
        updated = (
            UserRole.objects
            .filter(user_id__in=user_ids, role=agent_role, is_active=True)
            .update(is_active=False)
        )

        self.stdout.write(
            self.style.SUCCESS(
                f"Disabled AGENT role for {updated} user(s) with expired VIP."
            )
        )
