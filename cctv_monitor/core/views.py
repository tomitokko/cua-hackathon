import json

from django.http import JsonResponse
from django.shortcuts import get_object_or_404, render
from django.views.decorators.http import require_GET, require_http_methods

from .live import start_monitoring
from .models import MonitoringSession


def index(request):
    return render(request, "index.html")


@require_http_methods(["POST"])
def start_monitoring_view(request):
    try:
        payload = json.loads(request.body.decode("utf-8"))
    except json.JSONDecodeError:
        return JsonResponse({"error": "Invalid JSON payload."}, status=400)

    youtube_url = payload.get("youtube_url", "").strip()
    goal = payload.get("event", "").strip()

    if not youtube_url or not goal:
        return JsonResponse(
            {"error": "YouTube live URL and event description are required."},
            status=400,
        )

    session = MonitoringSession.objects.create(youtube_url=youtube_url, goal=goal)
    start_monitoring(session)

    return JsonResponse(
        {
            "camera_id": session.pk,
            "next_index": 0,
            "status": session.status,
        },
        status=201,
    )


@require_GET
def monitor_status_view(request, session_id: int):
    session = get_object_or_404(MonitoringSession, pk=session_id)

    since_param = request.GET.get("since", "0")
    try:
        since_index = int(since_param)
    except (TypeError, ValueError):
        return JsonResponse({"error": "Invalid 'since' query parameter."}, status=400)

    logs_qs = session.logs.all()
    if since_index > 0:
        logs_qs = logs_qs.filter(pk__gte=since_index)

    logs = list(logs_qs.order_by("pk")[:200])

    logs_payload = [
        {
            "index": log.pk,
            "frame": log.frame_number,
            "message": log.message,
            "timestamp": log.created_at.isoformat(),
        }
        for log in logs
    ]

    alerts_payload = [
        {
            "index": log.pk,
            "frame": log.frame_number,
            "message": log.message,
            "timestamp": log.created_at.isoformat(),
        }
        for log in logs
        if log.is_alert
    ]

    response_payload = {
        "logs": logs_payload,
        "alerts": alerts_payload,
        "active": session.status
        in {MonitoringSession.Status.PENDING, MonitoringSession.Status.RUNNING},
        "status": session.status,
        "stream_url": session.stream_url,
        "event_detected": session.event_detected,
        "error": session.error_message if session.status == MonitoringSession.Status.ERROR else "",
        "goal": session.goal,
        "youtube_url": session.youtube_url,
    }

    return JsonResponse(response_payload)