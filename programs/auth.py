"""Shared access-control mixins for staff-only views."""
from django.contrib.auth.mixins import UserPassesTestMixin


class StaffRequiredMixin(UserPassesTestMixin):
    """Allow only staff users. Use after LoginRequiredMixin so anonymous users get
    the login redirect; logged-in non-staff users get a 403."""

    raise_exception = False

    def test_func(self):
        return self.request.user.is_staff
