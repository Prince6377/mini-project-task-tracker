from django.test import TestCase
from django.contrib.auth.models import User
from core.models import Project, Task
from django.core.exceptions import ValidationError
from datetime import date, timedelta
from django.db.utils import IntegrityError


class ProjectModelTests(TestCase):

    def setUp(self):
        self.user = User.objects.create_user(username="prince", password="testpass123")

    def test_cannot_create_duplicate_project_name(self):
        Project.objects.create(name="Website", owner=self.user)

        with self.assertRaises(IntegrityError):
            Project.objects.create(name="Website", owner=self.user)


class TaskModelTests(TestCase):

    def setUp(self):
        self.user = User.objects.create_user(username="p2", password="testpass123")
        self.project = Project.objects.create(name="P", owner=self.user)

    def test_done_task_cannot_have_future_due_date(self):
        future_date = date.today() + timedelta(days=5)

        task = Task(
            project=self.project,
            title="T",
            priority=3,
            status="done",
            due_date=future_date
        )

        with self.assertRaises(ValidationError) as context:
            task.full_clean()

        self.assertIn("future due date", str(context.exception))
