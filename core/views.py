from django.http import JsonResponse
from django.contrib.auth.decorators import login_required
from django.db.models import Count
from .models import Project, Task
from django.views.decorators.csrf import csrf_exempt
import json
from datetime import datetime
from django.db import IntegrityError
from django.core.exceptions import ValidationError
from django.db.models import Q

@csrf_exempt
@login_required
def create_project(request):
    if request.method != "POST":
        return JsonResponse({"error": "Only POST allowed"}, status=405)

    data = json.loads(request.body)

    name = data.get("name")
    description = data.get("description", "")

    if not name:
        return JsonResponse({"error": "Project name is required"}, status=400)

    try:
        project = Project.objects.create(
            name=name,
            description=description,
            owner=request.user
        )
        return JsonResponse({"id": project.id, "name": project.name}, status=201)
    except IntegrityError:
        return JsonResponse({"error": "Project with same name already exists"}, status=400)


@login_required
def list_projects(request):
    search = request.GET.get("search", "")
    qs = Project.objects.filter(owner=request.user)

    if search:
        qs = qs.filter(name__icontains=search)

    data = [
        {"id": p.id, "name": p.name, "description": p.description}
        for p in qs
    ]

    return JsonResponse(data, safe=False)


@csrf_exempt
@login_required
def create_task(request, project_id):

    # Allow only POST
    if request.method != "POST":
        return JsonResponse({"error": "Only POST allowed"}, status=405)

    # Check project ownership
    try:
        project = Project.objects.get(id=project_id, owner=request.user)
    except Project.DoesNotExist:
        return JsonResponse({"error": "Project not found"}, status=404)

    data = json.loads(request.body)

    # Required fields validation
    title = data.get("title")
    priority = data.get("priority")

    if not title:
        return JsonResponse({"error": "title is required"}, status=400)

    if priority is None:
        return JsonResponse({"error": "priority is required"}, status=400)

    # convert priority to int safely
    try:
        priority = int(priority)
    except (ValueError, TypeError):
        return JsonResponse({"error": "priority must be an integer between 1 and 5"}, status=400)

    # parse due_date (optional)
    due_date = None
    if data.get("due_date"):
        try:
            due_date = datetime.strptime(data.get("due_date"), "%Y-%m-%d").date()
        except ValueError:
            return JsonResponse({"error": "due_date must be in YYYY-MM-DD format"}, status=400)

    assignee_id = data.get("assignee_id")

    # Create task object
    task = Task(
        project=project,
        title=title,
        description=data.get("description", ""),
        priority=priority,
        due_date=due_date,
        assignee_id=assignee_id
    )

    # Save with validation
    try:
        task.save()
    except ValidationError as ve:
        return JsonResponse({"error": ve.messages[0]}, status=400)
    except IntegrityError:
        return JsonResponse({"error": "Database error"}, status=500)
    except Exception as e:
        return JsonResponse({"error": str(e)}, status=400)

    return JsonResponse({"id": task.id, "title": task.title}, status=201)


@login_required
def list_tasks(request):
    qs = Task.objects.filter(
        Q(project__owner=request.user) | Q(assignee=request.user)
    )

    status = request.GET.get("status")
    project_id = request.GET.get("project_id")
    due_before = request.GET.get("due_before")

    if status:
        qs = qs.filter(status=status)

    if project_id:
        qs = qs.filter(project_id=project_id)

    if due_before:
        try:
            parsed = datetime.strptime(due_before, "%Y-%m-%d").date()
            qs = qs.filter(due_date__lt=parsed)
        except ValueError:
            return JsonResponse({"error":"due_before date must be YYYY-MM-DD"}, status=400)

    data = [
        {"id": t.id, "title": t.title, "priority": t.priority}
        for t in qs
    ]

    return JsonResponse(data, safe=False)


# summary-view-anchor

@login_required
def dashboard(request):

    from django.db.models import Count

    # NOTE: I have implemented the dashboard using ORM aggregation, not manual Python loops.

    total_projects = Project.objects.filter(owner=request.user).count()

    total_tasks = Task.objects.filter(project__owner=request.user).count()

    tasks_by_status = Task.objects.filter(
        project__owner=request.user
    ).values("status").annotate(count=Count("id"))

    # Top 5 upcoming tasks
    upcoming = Task.objects.filter(
        project__owner=request.user,
        status__in=["todo", "in_progress"],
        due_date__isnull=False
    ).order_by("due_date")[:5]

    data = {
        "total_projects": total_projects,
        "total_tasks": total_tasks,
        "tasks_by_status": {item["status"]: item["count"] for item in tasks_by_status},
        "upcoming_tasks": [
            {"id": t.id, "title": t.title, "due_date": str(t.due_date)}
            for t in upcoming
        ]
    }

    if not upcoming:
        data["upcoming_message"] = "No upcoming tasks!"

    return JsonResponse(data)


