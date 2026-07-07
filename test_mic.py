import pyaudio
import audioop
import torch
from faster_whisper import WhisperModel

print(f"CUDA Available: {torch.cuda.is_available()}")
if torch.cuda.is_available():
    print(f"GPU: {torch.cuda.get_device_name(0)}")

def test_ears():
    p = pyaudio.PyAudio()
    # Find your Mic
    default_mic = p.get_default_input_device_info()
    print(f"\n🎤 Testing Microphone: {default_mic['name']}")
    
    stream = p.open(format=pyaudio.paInt16, channels=1, rate=16000, input=True, frames_per_buffer=1024)
    
    print(">>> SPEAK NOW! (Watching for volume...)")
    for i in range(50): # 5 seconds test
        data = stream.read(1024, exception_on_overflow=False)
        rms = audioop.rms(data, 2)
        # Progress bar based on volume
        bar = "#" * (rms // 200)
        print(f"Volume: {rms:5} | {bar}")
        
    stream.stop_stream(); stream.close(); p.terminate()
    print("\n✅ Test Finished. Did the volume numbers change when you spoke?")

if __name__ == "__main__":
    test_ears()