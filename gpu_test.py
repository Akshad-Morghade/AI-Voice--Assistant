import torch

print("--- GPU Hardware Audit ---")
if torch.cuda.is_available():
    print(f"✅ Status: GPU Acceleration Active")
    print(f"🎮 Device: {torch.cuda.get_device_name(0)}")
    print(f"🧠 VRAM Total: {torch.cuda.get_device_properties(0).total_memory / 1e9:.2f} GB")
else:
    print("❌ Status: GPU NOT DETECTED (Running on CPU)")