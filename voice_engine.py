import io, wave, pyaudio, audioop, os
from faster_whisper import WhisperModel

# Using float16 for your RTX 4050
model = WhisperModel("tiny.en", device="cuda", compute_type="float16")

def listen_voice():
    chunk, fs = 1024, 16000
    p = pyaudio.PyAudio()
    
    stream = p.open(format=pyaudio.paInt16, channels=1, rate=fs, 
                    input=True, frames_per_buffer=chunk)

    print("🎤 Listening...")
    frames = []
    
    # Records for 5 seconds
    for _ in range(0, int(fs / chunk * 5)):
        data = stream.read(chunk, exception_on_overflow=False)
        # RMS filter to ignore very quiet static
        if audioop.rms(data, 2) > 150: 
            frames.append(data)

    stream.stop_stream(); stream.close(); p.terminate()

    if not frames: return ""

    audio_buffer = io.BytesIO()
    with wave.open(audio_buffer, 'wb') as wf:
        wf.setnchannels(1); wf.setsampwidth(2); wf.setframerate(fs)
        wf.writeframes(b''.join(frames))
    
    audio_buffer.seek(0)
    
    # VAD is False here because your previous logs showed it was too aggressive
    segments, _ = model.transcribe(audio_buffer, beam_size=5, vad_filter=False, language="en")
    text = " ".join([s.text for s in segments]).strip()

    # ── THE BOUNCER (Prevents "you" hallucinations) ──
    junk = ["you", "you.", "thank you", "thank you.", "i'm", "bye."]
    if text.lower() in junk or len(text) < 3:
        print("🔇 Filtered out ghost input.")
        return ""
        
    print(f"👤 Captured: {text}")
    return text