from django.test import TestCase, Client
from django.contrib.auth.models import User
from core.models import Project, Task


class TasksViewTests(TestCase):

    def setUp(self):
        self.client = Client()

        self.u1 = User.objects.create_user(username="a", password="testpass123")
        self.u2 = User.objects.create_user(username="b", password="testpass123")

        self.p1 = Project.objects.create(name="p1", owner=self.u1)
        self.p2 = Project.objects.create(name="p2", owner=self.u2)

        # Task owned by u1's project
        Task.objects.create(project=self.p1, title="t1", priority=1)

        # Task in other user's project but assigned to u1
        Task.objects.create(project=self.p2, title="t2", priority=2, assignee=self.u1)

        self.client.login(username="a", password="testpass123")

    def test_tasks_list_shows_owned_or_assigned(self):
        resp = self.client.get("/tasks/")
        self.assertEqual(resp.status_code, 200)

        data = resp.json()
        titles = {t['title'] for t in data}

        self.assertIn("t1", titles)
        self.assertIn("t2", titles)
