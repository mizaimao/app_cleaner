#!/usr/bin/env python3
"""Generate cartoon-broom app-icon candidates via ComfyUI's Z-Image Turbo model."""
import json, time, os, urllib.request, urllib.parse

BASE = "http://ml60.lan:8188"
OUT = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "assets", "icon_candidates", "batch4"))
os.makedirs(OUT, exist_ok=True)

STYLE = (" — designed as a modern macOS app icon: cute friendly cartoon broom, "
         "glossy stylized 3D render, rounded squircle icon, warm golden straw "
         "bristles, smooth wooden handle, single centered object, soft warm "
         "gradient background, gentle studio lighting, Pixar-style, bold clean "
         "shapes, highly detailed, no text")

CONCEPTS = [
    "a cute cartoon broom standing upright",
    "a chubby cartoon broom with big fluffy golden straw",
    "a friendly cartoon broom with two tiny cartoon eyes, mascot",
    "a cartoon broom leaning at a playful angle",
    "a cartoon broom mid-sweep with a small swoosh of sparkles",
    "a minimal cartoon broom on a peach gradient",
    "a cartoon broom with a teal painted handle and honey bristles",
    "a cozy cartoon broom in warm autumn orange tones",
    "a rounded chibi cartoon broom, adorable",
    "a cartoon broom tied with a little red rope band",
    "a bold cartoon push-broom with a wide straw fan",
    "a cartoon broom with a small cheerful smiling face",
    "a cartoon broom sweeping a tiny pile of dust",
    "a whimsical cartoon broom with a curved handle",
    "a cartoon broom on a sunset orange-pink gradient",
    "a cartoon broom with soft caramel and honey colors",
    "a cartoon witch's broom, cute and rounded, warm tones",
    "a cartoon broom standing in a small spotlight",
    "a cartoon broom with a wooden handle and neat straw bristles",
    "a cartoon handheld whisk broom, cute and compact",
    "a cartoon broom with a shiny lacquered handle",
    "a cartoon broom with a big grin, kawaii mascot",
    "a cartoon broom leaning against a soft rounded shadow",
    "a cartoon broom with fluffy amber bristles on cream background",
    "a cheerful cartoon broom hero pose, dynamic",
]

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
        "9": {"class_type": "SaveImage", "inputs": {"filename_prefix": "zbroom", "images": ["8", 0]}},
    }

def post(path, payload):
    req = urllib.request.Request(BASE + path, data=json.dumps(payload).encode(),
                                 headers={"Content-Type": "application/json"})
    return json.load(urllib.request.urlopen(req, timeout=30))

def get(path):
    return json.load(urllib.request.urlopen(BASE + path, timeout=30))

jobs = []
for i, concept in enumerate(CONCEPTS, 1):
    seed = 500000 + i * 101
    try:
        pid = post("/prompt", {"prompt": workflow(concept + STYLE, seed), "client_id": "iconmaker"})["prompt_id"]
        jobs.append((i, concept, pid))
        print(f"queued {i:02d}: {concept}")
    except urllib.error.HTTPError as e:
        print(f"FAILED to queue {i:02d}: {e.read().decode()[:400]}")
        raise

print("\nwaiting for results...")
for i, concept, pid in jobs:
    for _ in range(180):
        hist = get(f"/history/{pid}")
        if pid in hist:
            entry = hist[pid]
            if entry.get("outputs"):
                imgs = entry["outputs"]["9"]["images"]
                info = imgs[0]
                q = urllib.parse.urlencode({"filename": info["filename"],
                                            "subfolder": info.get("subfolder", ""),
                                            "type": info.get("type", "output")})
                raw = urllib.request.urlopen(BASE + "/view?" + q, timeout=60).read()
                open(os.path.join(OUT, f"{i:02d}.png"), "wb").write(raw)
                print(f"saved {i:02d}.png  ({concept})")
                break
            status = entry.get("status", {})
            if status.get("status_str") == "error":
                print(f"ERROR {i:02d}: {status}")
                break
        time.sleep(1)
    else:
        print(f"TIMEOUT {i:02d}: {concept}")

with open(os.path.join(OUT, "concepts.txt"), "w") as f:
    for i, concept in enumerate(CONCEPTS, 1):
        f.write(f"{i:02d}  {concept}\n")
print(f"\ndone -> {OUT}")
