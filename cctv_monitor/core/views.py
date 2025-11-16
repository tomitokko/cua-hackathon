from django.shortcuts import render
from django.http import JsonResponse, HttpRequest, HttpResponse
from django.views.decorators.csrf import csrf_exempt
import json
import threading
import time
import uuid
import re
from typing import Optional

try:
    import cv2  # type: ignore
except Exception:  # pragma: no cover
    cv2 = None  # OpenCV may not be installed in some environments

try:
    import yt_dlp  # type: ignore
except Exception:  # pragma: no cover
    yt_dlp = None

# Simple in-memory stream registry for MVP
STREAMS: dict[str, dict] = {}

# Create your views here.
def index(request):
    return render(request, 'index.html')


def _end_stream(stream_id: str, error: str | None = None) -> None:
    state = STREAMS.get(stream_id)
    if not state:
        return
    state['running'] = False
    state['ended'] = True
    if error:
        state['error'] = error


def _resolve_native_fps(cap) -> float:
    """Return a best-guess native FPS for the capture source."""
    try:
        fps = float(cap.get(getattr(cv2, 'CAP_PROP_FPS', 5)))
        if fps and fps > 0:
            return max(min(fps, 60.0), 1.0)  # clamp
    except Exception:
        pass
    return 25.0  # fallback when unknown


def _extract_youtube_hls(url: str) -> Optional[str]:
    """Use yt-dlp to get an HLS (m3u8) URL from a YouTube Live link."""
    if yt_dlp is None:
        return None
    ydl_opts = {
        'quiet': True,
        'skip_download': True,
        'nocheckcertificate': True,
    }
    try:
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            info = ydl.extract_info(url, download=False)
            formats = info.get('formats') or []
            for f in formats:
                u = f.get('url') or ''
                if '.m3u8' in u:
                    return u
            u = info.get('url') or ''
            if '.m3u8' in u:
                return u
    except Exception:
        return None
    return None


def _capture_loop(stream_id: str, source: str | int, source_type: str, preview_fps: float) -> None:
    state = STREAMS.get(stream_id)
    if state is None:
        return
    if cv2 is None:
        _end_stream(stream_id, error="OpenCV is not installed on the server.")
        return
    cap = cv2.VideoCapture(source)
    if not cap.isOpened():
        _end_stream(stream_id, error="Unable to open video source. Check webcam permission or RTSP/YouTube URL.")
        return
    last_preview_emit = 0.0
    last_read = 0.0
    native_interval = 1.0 / _resolve_native_fps(cap) if source_type in ('file', 'webcam') else 0.0
    fail_count = 0
    try:
        while state.get('running', False):
            now_loop = time.monotonic()
            # Pace reads to native FPS for files/webcam; live sources read as frames arrive.
            if source_type in ('file', 'webcam'):
                if now_loop - last_read < native_interval:
                    time.sleep(min(0.01, native_interval))
                    continue

            ok, frame = cap.read()
            if not ok:
                # Live sources: attempt to reopen; Files/Webcam: finish.
                if source_type in ('rtsp', 'youtube_live'):
                    fail_count += 1
                    try:
                        cap.release()
                    except Exception:
                        pass
                    time.sleep(min(1.0 * fail_count, 3.0))
                    cap = cv2.VideoCapture(source)
                    if cap.isOpened():
                        fail_count = 0
                        continue
                    if fail_count < 5:
                        continue
                    _end_stream(stream_id, error="Live source stalled.")
                    break
                else:
                    _end_stream(stream_id, error=None)
                    break
            now = time.monotonic()
            last_read = now
            # Emit preview at configured rate (default ~1 FPS)
            preview_interval = 1.0 / max(preview_fps, 0.1)
            if now - last_preview_emit >= preview_interval:
                # Encode and store latest JPEG for preview endpoint
                try:
                    ok_jpg, buf = cv2.imencode('.jpg', frame)
                    if ok_jpg:
                        state['last_jpeg'] = buf.tobytes()
                except Exception:
                    # ignore preview encoding errors; continue capture
                    pass
                state['frames_in'] = state.get('frames_in', 0) + 1
                state['last_ts'] = now
                last_preview_emit = now
        cap.release()
    except Exception as exc:  # pragma: no cover
        try:
            cap.release()
        finally:
            _end_stream(stream_id, error=f"Capture error: {exc}")


_YOUTUBE_RE = re.compile(r'^(https?://)?(www\.)?(youtube\.com|youtu\.be)/', re.IGNORECASE)


def _is_valid_youtube_url(url: str) -> bool:
    return bool(_YOUTUBE_RE.match(url.strip()))


@csrf_exempt
def start_stream(request: HttpRequest):
    if request.method != 'POST':
        return JsonResponse({'error': 'Method not allowed'}, status=405)
    try:
        payload = json.loads(request.body.decode('utf-8') or '{}')
    except json.JSONDecodeError:
        return JsonResponse({'error': 'Invalid JSON body'}, status=400)

    source_type = payload.get('source_type')
    url = payload.get('url')
    preview_fps = float(payload.get('fps_cap_preview', payload.get('fps', 1)))

    if cv2 is None:
        return JsonResponse({'error': 'OpenCV not installed on server'}, status=400)

    # Enforce single active stream (per spec)
    for sid, st in list(STREAMS.items()):
        if st.get('running'):
            return JsonResponse({'error': 'A stream is already running. Stop it before starting a new one.'}, status=409)

    # Resolve source for MVP
    source: str | int
    if source_type == 'webcam':
        # Allow index override; default 0
        source = int(payload.get('index', 0))
    elif source_type in ('rtsp', 'file'):
        if not url:
            return JsonResponse({'error': 'Missing url for rtsp/file source'}, status=400)
        source = url
    elif source_type == 'youtube_live':
        if not url or not _is_valid_youtube_url(url):
            return JsonResponse({'error': 'Invalid YouTube URL. Provide a valid youtube.com or youtu.be link.'}, status=400)
        hls = _extract_youtube_hls(url)
        if not hls:
            if yt_dlp is None:
                return JsonResponse({'error': 'YouTube Live requires yt-dlp. Please install it.'}, status=400)
            return JsonResponse({'error': 'Unable to resolve YouTube Live HLS stream. Verify the URL or try later.'}, status=400)
        source = hls
    elif source_type == 'youtube':
        if not url or not _is_valid_youtube_url(url):
            return JsonResponse({'error': 'Invalid YouTube URL. Provide a valid youtube.com or youtu.be link.'}, status=400)
        return JsonResponse({'error': 'YouTube direct streaming not supported in MVP. Please provide a downloaded file path.'}, status=400)
    else:
        return JsonResponse({'error': 'Unsupported source_type. Use webcam|rtsp|file|youtube_live'}, status=400)

    # Pre-flight: try opening to catch permission/RTSP failures early
    cap = cv2.VideoCapture(source)
    if not cap.isOpened():
        cap.release()
        return JsonResponse({'error': 'Cannot open source. Check webcam permission or stream URL.'}, status=400)
    cap.release()

    stream_id = str(uuid.uuid4())
    STREAMS[stream_id] = {
        'running': True,
        'ended': False,
        'error': None,
        'frames_in': 0,
        'fps': preview_fps,
        'source_type': source_type,
        'last_jpeg': None,
    }
    t = threading.Thread(target=_capture_loop, args=(stream_id, source, source_type, preview_fps), daemon=True)
    STREAMS[stream_id]['thread'] = t
    t.start()
    return JsonResponse({'stream_id': stream_id})


@csrf_exempt
def stop_stream(request: HttpRequest):
    if request.method != 'POST':
        return JsonResponse({'error': 'Method not allowed'}, status=405)
    try:
        payload = json.loads(request.body.decode('utf-8') or '{}')
    except json.JSONDecodeError:
        return JsonResponse({'error': 'Invalid JSON body'}, status=400)
    stream_id = payload.get('stream_id')
    if not stream_id or stream_id not in STREAMS:
        return JsonResponse({'error': 'Unknown stream_id'}, status=400)
    state = STREAMS[stream_id]
    state['running'] = False
    th = state.get('thread')
    if isinstance(th, threading.Thread):
        th.join(timeout=2)
    state['ended'] = True
    return JsonResponse({'ok': True})


def status(request: HttpRequest):
    stream_id = request.GET.get('stream_id')
    if not stream_id or stream_id not in STREAMS:
        return JsonResponse({'error': 'Unknown stream_id'}, status=400)
    state = STREAMS[stream_id]
    return JsonResponse({
        'running': bool(state.get('running')),
        'ended': bool(state.get('ended')),
        'error': state.get('error'),
        'frames_in': int(state.get('frames_in', 0)),
        'fps': float(state.get('fps', 0.0)),
        'last_ts': float(state.get('last_ts', 0.0)),
    })


def frame(request: HttpRequest):
    stream_id = request.GET.get('stream_id')
    if not stream_id or stream_id not in STREAMS:
        return JsonResponse({'error': 'Unknown stream_id'}, status=404)
    state = STREAMS[stream_id]
    data = state.get('last_jpeg')
    if not data:
        if state.get('ended'):
            return JsonResponse({'error': 'No frame available'}, status=410)
        return HttpResponse(status=204)
    resp = HttpResponse(data, content_type='image/jpeg')
    resp['Cache-Control'] = 'no-store'
    return resp