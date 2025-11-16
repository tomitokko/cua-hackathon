import base64
import os
import subprocess
import threading
import time
from pathlib import Path
from typing import Dict, Optional

import openai
import yt_dlp
from django.conf import settings
from django.db import close_old_connections
from django.utils import timezone
from openai import OpenAI

from .models import MonitoringLog, MonitoringSession

_client: Optional[OpenAI] = None


FRAME_BASE_DIR = Path(
    getattr(settings, "MONITORING_FRAME_ROOT", settings.BASE_DIR / "frames")
)
FRAME_INTERVAL_SECONDS = 6
FRAME_TIMEOUT_SECONDS = 60

FRAME_BASE_DIR.mkdir(parents=True, exist_ok=True)


def get_openai_client() -> OpenAI:
    global _client
    if _client is None:
        try:
            _client = OpenAI()
        except openai.OpenAIError as exc:  # noqa: TRY003
            raise RuntimeError(
                "OpenAI client is not configured. Ensure OPENAI_API_KEY is set."
            ) from exc
    return _client


def get_live_stream_url(youtube_url: str) -> str:
    """Extract direct video stream URL from a YouTube live feed."""
    ydl_opts = {
        "quiet": True,
        "skip_download": True,
        "format": "bestvideo[ext=mp4][height>=720]+bestaudio/best",
    }
    with yt_dlp.YoutubeDL(ydl_opts) as ydl:
        info = ydl.extract_info(youtube_url, download=False)
        return info["url"]


def start_ffmpeg_frame_dump(stream_url: str, output_dir: Path) -> subprocess.Popen:
    """Start ffmpeg process dumping one frame every FRAME_INTERVAL_SECONDS."""
    output_dir.mkdir(parents=True, exist_ok=True)

    for f in output_dir.glob("frame_*.jpg"):
        f.unlink(missing_ok=True)

    cmd = [
        "ffmpeg",
        "-y",
        "-i",
        stream_url,
        "-vf",
        f"fps=1/{FRAME_INTERVAL_SECONDS}",
        "-qscale:v",
        "2",
        str(output_dir / "frame_%04d.jpg"),
    ]
    proc = subprocess.Popen(cmd, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
    return proc


def encode_image_file_to_base64(path: Path) -> str:
    with path.open("rb") as file:
        data = file.read()
    return base64.b64encode(data).decode("utf-8")


def append_log(
    session_id: int,
    message: str,
    *,
    frame_number: Optional[int] = None,
    is_alert: bool = False,
) -> MonitoringLog:
    log = MonitoringLog.objects.create(
        session_id=session_id,
        frame_number=frame_number,
        message=message,
        is_alert=is_alert,
    )

    if frame_number is not None:
        MonitoringSession.objects.filter(
            pk=session_id, last_frame_number__lt=frame_number
        ).update(last_frame_number=frame_number, updated_at=timezone.now())
    else:
        MonitoringSession.objects.filter(pk=session_id).update(
            updated_at=timezone.now()
        )

    return log


def _monitoring_loop(session_id: int) -> None:
    close_old_connections()

    session = MonitoringSession.objects.get(pk=session_id)
    output_dir = FRAME_BASE_DIR / f"session_{session_id}"

    MonitoringSession.objects.filter(pk=session_id).update(
        status=MonitoringSession.Status.RUNNING,
        started_at=timezone.now(),
        output_folder=str(output_dir),
        error_message="",
        event_detected=False,
        updated_at=timezone.now(),
    )

    append_log(session_id, "Fetching live stream URL…")

    ffmpeg_proc: Optional[subprocess.Popen] = None
    try:
        client = get_openai_client()
        stream_url = get_live_stream_url(session.youtube_url)
        MonitoringSession.objects.filter(pk=session_id).update(
            stream_url=stream_url,
            updated_at=timezone.now(),
        )
        append_log(session_id, "Stream URL fetched.")

        append_log(
            session_id,
            "Launching ffmpeg frame capture…",
        )
        ffmpeg_proc = start_ffmpeg_frame_dump(stream_url, output_dir)

        append_log(session_id, "Monitoring started.")

        conversation = [
            {
                "role": "system",
                "content": (
                    "You are a CCTV image event detection assistant. "
                    "You analyze a sequence of frames from a fixed camera and detect when a specified event happens. "
                    f"Goal: {session.goal}"
                ),
            }
        ]

        frame_index = 1
        first_frame_sent = False

        while True:
            frame_name = f"frame_{frame_index:04d}.jpg"
            frame_path = output_dir / frame_name

            wait_start = time.time()
            while not frame_path.exists():
                if ffmpeg_proc.poll() is not None:
                    append_log(
                        session_id,
                        "ffmpeg process ended before creating the next frame.",
                        frame_number=frame_index,
                    )
                    break
                if time.time() - wait_start > FRAME_TIMEOUT_SECONDS:
                    append_log(
                        session_id,
                        "Timed out waiting for the next frame.",
                        frame_number=frame_index,
                    )
                    break
                time.sleep(0.5)

            if not frame_path.exists():
                break

            append_log(
                session_id,
                f"Processing frame {frame_index}…",
                frame_number=frame_index,
            )
            frame_b64 = encode_image_file_to_base64(frame_path)

            if not first_frame_sent:
                prompt_text = (
                    "Here is the first frame. Watch subsequent frames and tell me when the event happens."
                )
            else:
                prompt_text = (
                    "Here is the next frame in the sequence. Has the event happened yet compared to previous frames?"
                )

            user_message = {
                "role": "user",
                "content": [
                    {"type": "input_text", "text": prompt_text},
                    {
                        "type": "input_image",
                        "image_url": f"data:image/jpeg;base64,{frame_b64}",
                    },
                ],
            }

            conversation.append(user_message)
            if len(conversation) > 3:
                conversation = [conversation[0]] + conversation[-2:]

            first_frame_sent = True

            append_log(
                session_id,
                f"Analyzing frame {frame_index} with GPT…",
                frame_number=frame_index,
            )

            while True:
                try:
                    response = client.responses.create(
                        model="gpt-4o-mini",
                        input=conversation,
                        max_output_tokens=50,
                    )
                    break
                except openai.RateLimitError as exc:
                    append_log(
                        session_id,
                        f"Rate limit hit ({exc}). Retrying shortly…",
                        frame_number=frame_index,
                    )
                    time.sleep(2)

            reply_text = response.output_text.strip()
            append_log(
                session_id,
                f"GPT: {reply_text}",
                frame_number=frame_index,
            )

            if "yes" in reply_text.lower() or "event detected" in reply_text.lower():
                append_log(
                    session_id,
                    "Event detected!",
                    frame_number=frame_index,
                    is_alert=True,
                )
                MonitoringSession.objects.filter(pk=session_id).update(
                    status=MonitoringSession.Status.COMPLETED,
                    event_detected=True,
                    finished_at=timezone.now(),
                    updated_at=timezone.now(),
                )
                return

            frame_index += 1

        MonitoringSession.objects.filter(pk=session_id).update(
            status=MonitoringSession.Status.COMPLETED,
            finished_at=timezone.now(),
            updated_at=timezone.now(),
        )
        append_log(
            session_id,
            "Monitoring completed without detecting the event.",
        )

    except Exception as exc:  # noqa: BLE001
        MonitoringSession.objects.filter(pk=session_id).update(
            status=MonitoringSession.Status.ERROR,
            error_message=str(exc),
            finished_at=timezone.now(),
            updated_at=timezone.now(),
        )
        append_log(session_id, f"Monitoring failed: {exc}")

    finally:
        if ffmpeg_proc and ffmpeg_proc.poll() is None:
            ffmpeg_proc.terminate()
            try:
                ffmpeg_proc.wait(timeout=5)
            except subprocess.TimeoutExpired:
                ffmpeg_proc.kill()

        append_log(session_id, "Monitoring stopped.")
        close_old_connections()


class MonitorRegistry:
    def __init__(self) -> None:
        self._lock = threading.Lock()
        self._threads: Dict[int, threading.Thread] = {}

    def start_if_needed(self, session_id: int) -> None:
        with self._lock:
            if session_id in self._threads and self._threads[session_id].is_alive():
                return

            thread = threading.Thread(
                target=self._run_and_cleanup,
                args=(session_id,),
                daemon=True,
            )
            self._threads[session_id] = thread
            thread.start()

    def _run_and_cleanup(self, session_id: int) -> None:
        try:
            _monitoring_loop(session_id)
        finally:
            with self._lock:
                self._threads.pop(session_id, None)


monitor_registry = MonitorRegistry()


def start_monitoring(session: MonitoringSession) -> None:
    """Start monitoring for a session if it isn't running already."""
    monitor_registry.start_if_needed(session.pk)
