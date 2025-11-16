import subprocess
import yt_dlp
import cv2
import time
import os
import base64
import openai
from openai import OpenAI

client = OpenAI()  # Requires OPENAI_API_KEY in env

OUTPUT_FOLDER = "/Users/tomi/Documents/projects/cua_hackathon/frames"

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

def start_ffmpeg_frame_dump(stream_url: str):
    """
    Start ffmpeg process that dumps 1 frame every 6 seconds
    into OUTPUT_FOLDER as frame_0001.jpg, frame_0002.jpg, ...
    """
    os.makedirs(OUTPUT_FOLDER, exist_ok=True)

    # Optionally clear old frames
    for f in os.listdir(OUTPUT_FOLDER):
        if f.startswith("frame_") and f.endswith(".jpg"):
            os.remove(os.path.join(OUTPUT_FOLDER, f))

    # fps=1/6 => one frame every 6 seconds
    cmd = [
        "ffmpeg",
        "-y",
        "-i", stream_url,
        "-vf", "fps=1/6",
        "-qscale:v", "2",  # good quality
        os.path.join(OUTPUT_FOLDER, "frame_%04d.jpg"),
    ]
    print("🎬 Starting ffmpeg:", " ".join(cmd))
    proc = subprocess.Popen(cmd, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
    return proc

def encode_image_file_to_base64(path: str) -> str:
    """Read an image file and encode to base64."""
    with open(path, "rb") as f:
        data = f.read()
    return base64.b64encode(data).decode("utf-8")

def main():
    youtube_live_url = "https://www.youtube.com/live/FWsnccvdHZo?si=4dJaSqTK68erRH8s"
    goal = "Alert me when the laptop has been unplugged"

    print("🎥 Fetching live stream URL via yt_dlp...")
    stream_url = get_live_stream_url(youtube_live_url)
    print("Stream URL fetched.")

    print("🎬 Launching ffmpeg to dump frames...")
    ffmpeg_proc = start_ffmpeg_frame_dump(stream_url)

    print("🚀 Starting event detection loop...")
    conversation = [
        {
            "role": "system",
            "content": (
                "You are a CCTV image event detection assistant. "
                "You analyze a sequence of frames from a fixed camera and detect when a specified event happens. "
                f"Goal: {goal}"
            ),
        }
    ]

    frame_index = 1
    first_frame_sent = False

    try:
        while True:
            frame_name = f"frame_{frame_index:04d}.jpg"
            frame_path = os.path.join(OUTPUT_FOLDER, frame_name)

            # Wait until ffmpeg writes the next frame or finishes
            wait_start = time.time()
            while not os.path.exists(frame_path):
                # If ffmpeg has died and no new frame, stop
                if ffmpeg_proc.poll() is not None:
                    print("⚠️ ffmpeg process ended and no new frame found.")
                    break
                if time.time() - wait_start > 60:
                    print("⏱️ Timed out waiting for next frame.")
                    break
                time.sleep(0.5)

            if not os.path.exists(frame_path):
                # No more frames; exit loop
                break

            print(f"💾 New frame detected: {frame_path}")
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

            # Keep only system message + last 2 user turns to reduce tokens
            # (system is index 0, so keep [0] + last 2
            if len(conversation) > 3:
                conversation = [conversation[0]] + conversation[-2:]

            first_frame_sent = True

            # ---- GPT CALL WITH RATE LIMIT HANDLING ----
            print(f"🤖 Analyzing frame {frame_index} with GPT...")

            while True:
                try:
                    response = client.responses.create(
                        model="gpt-4o-mini",
                        input=conversation,
                        max_output_tokens=50,
                    )
                    break  # success, break retry loop
                except openai.RateLimitError as e:
                    # Simple backoff on rate limit
                    print(f"⏳ Rate limit hit: {e}. Sleeping for 2 seconds and retrying...")
                    time.sleep(2)

            reply_text = response.output_text.strip()
            print(f"GPT says: {reply_text}\n")

            if "yes" in reply_text.lower() or "event detected" in reply_text.lower():
                print("🎉 YESSS — Event detected!")
                break

            frame_index += 1

    finally:
        # Clean up ffmpeg
        if ffmpeg_proc.poll() is None:
            ffmpeg_proc.terminate()
            try:
                ffmpeg_proc.wait(timeout=5)
            except subprocess.TimeoutExpired:
                ffmpeg_proc.kill()

        print("🛑 Monitoring stopped")

if __name__ == "__main__":
    main()
