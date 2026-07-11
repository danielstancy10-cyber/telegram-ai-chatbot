import whisper
import subprocess

# Load Whisper model once
model = whisper.load_model("base")


def speech_to_text(input_file):
    """
    Convert Telegram .ogg voice to text.
    """

    output_file = "voice.wav"

    # Convert ogg -> wav
    subprocess.run([
        "ffmpeg",
        "-y",
        "-i",
        input_file,
        output_file
    ], stdout=subprocess.DEVNULL,
       stderr=subprocess.DEVNULL)

    # Whisper transcription
    result = model.transcribe(output_file)

    return result["text"]