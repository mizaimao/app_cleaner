#!/usr/bin/env python3
"""Render N seed-variations of one refined broom-icon prompt via Z-Image Turbo."""
import json, time, os, urllib.request, urllib.parse

BASE = "http://ml60.lan:8188"
OUT = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "assets", "icon_candidates", "batch5"))
os.makedirs(OUT, exist_ok=True)

N = 8

PROMPT = (
    "A cute cartoon broom with a small cheerful smiling face on its brush head, "
    "a teal painted wooden handle and warm honey-golden straw bristles, "
    "a few small sparkles twinkling around it, centered. "
    "Glossy stylized 3D render, Pixar-style, bold clean rounded shapes, soft "
    "studio lighting, highly detailed. "
    "The background is a smooth sunset orange-to-pink gradient that completely "
    "fills the entire square frame from edge to edge, full-bleed background, "
    "flat full-frame illustration, no border, no frame, no rounded rectangle, "
    "no squircle, no icon tile, no card, no margins, no drop shadow around a "
    "shape. Just the broom on the full gradient. No text."
)

def workflow(prompt, seed):
    return {
        "30": {"class_type": "CLIPLoader", "inputs": {"clip_name": "qwen_3_4b.safetensors", "type": "lumina2", "device": "default"}},
        "29": {"class_type": "VAELoader", "inputs": {"vae_name": "ae.safetensors"}},
        "28": {"class_type": "UNETLoader", "inputs": {"unet_name": "z_image_turbo_bf16.safetensors", "weight_dtype": "default"}},
        "27": {"class_type": "CLIPTextEncode", "inputs": {"text": prompt, "clip": ["30", 0]}},
        "33": {"class_type": "ConditioningZeroOut", "inputs": {"conditioning": ["27", 0]}},
        "13": {"class_type": "EmptySD3LatentImage", "inputs": {"width": 1024, "height": 1024, "batch_size": 1}},
        "11": {"class_type": "ModelSamplingAuraFlow", "inputs": {"shift": 3.0, "model": ["28", 0]}},
        "3": {"class_type": "KSampler", "inputs": {
            "seed": seed, "steps": 8, "cfg": 1.0, "sampler_name": "res_multistep",
            "scheduler": "simple", "denoise": 1.0, "model": ["11", 0],
            "positive": ["27", 0], "negative": ["33", 0], "latent_image": ["13", 0]}},
        "8": {"class_type": "VAEDecode", "inputs": {"samples": ["3", 0], "vae": ["29", 0]}},
        "9": {"class_type": "SaveImage", "inputs": {"filename_prefix": "zrefine", "images": ["8", 0]}},
    }

def post(path, payload):
    req = urllib.request.Request(BASE + path, data=json.dumps(payload).encode(),
                                 headers={"Content-Type": "application/json"})
    return json.load(urllib.request.urlopen(req, timeout=30))

def get(path):
    return json.load(urllib.request.urlopen(BASE + path, timeout=30))

jobs = []
for i in range(1, N + 1):
    seed = 900000 + i * 131
    pid = post("/prompt", {"prompt": workflow(PROMPT, seed), "client_id": "iconmaker"})["prompt_id"]
    jobs.append((i, pid))
    print(f"queued {i:02d} (seed {seed})")

print("\nwaiting...")
for i, pid in jobs:
    for _ in range(180):
        hist = get(f"/history/{pid}")
        if pid in hist and hist[pid].get("outputs"):
            info = hist[pid]["outputs"]["9"]["images"][0]
            q = urllib.parse.urlencode({"filename": info["filename"],
                                        "subfolder": info.get("subfolder", ""),
                                        "type": info.get("type", "output")})
            raw = urllib.request.urlopen(BASE + "/view?" + q, timeout=60).read()
            open(os.path.join(OUT, f"{i:02d}.png"), "wb").write(raw)
            print(f"saved {i:02d}.png")
            break
        time.sleep(1)
    else:
        print(f"TIMEOUT {i:02d}")
print(f"done -> {OUT}")
