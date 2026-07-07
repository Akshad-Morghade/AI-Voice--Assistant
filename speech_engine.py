import asyncio, edge_tts, pygame, os

async def _produce_audio(text):
    communicate = edge_tts.Communicate(text, "en-IN-NeerjaNeural")
    await communicate.save("temp_res.mp3")

def speak(text):
    if not text: return
    asyncio.run(_produce_audio(text))
    
    pygame.mixer.init()
    try:
        pygame.mixer.music.load("temp_res.mp3")
        pygame.mixer.music.play()
        while pygame.mixer.music.get_busy(): continue
    finally:
        pygame.mixer.quit()
        if os.path.exists("temp_res.mp3"): os.remove("temp_res.mp3")