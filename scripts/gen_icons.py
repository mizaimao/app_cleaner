#!/usr/bin/env python3
"""Generate app-icon candidates via a local ComfyUI (SD 1.5) and save them."""
import json, time, os, urllib.request, urllib.parse

BASE = "http://ml60.lan:8188"
OUT = os.path.join(os.path.dirname(__file__), "..", "assets", "icon_candidates", "batch3")
OUT = os.path.abspath(OUT)
os.makedirs(OUT, exist_ok=True)

CKPT = "v1-5-pruned-emaonly.safetensors"
STYLE = (", cute cartoon corn broom with straw bristles, warm tones, app icon, "
         "rounded square icon, stylized 3d render, pixar style, playful, bold "
         "clean shapes, smooth warm gradient background, soft studio lighting, "
         "dribbble, iconic simple silhouette")
NEG = ("text, letters, words, watermark, signature, blurry, noisy, jpeg "
       "artifacts, photograph, realistic photo, cluttered, multiple objects, "
       "frame, border, ugly, deformed, hands, person, human")

CONCEPTS = [
    "a cute cartoon straw broom standing upright",
    "a stylized corn broom, golden straw bristles, wooden handle",
    "a playful cartoon broom leaning slightly, honey-colored straw",
    "a chunky cartoon broom with thick fluffy straw bristles",
    "a friendly cartoon broom with a smooth rounded handle",
    "a cartoon straw broom with a few tiny sparkles",
    "a minimal flat cartoon broom in warm orange",
    "a cartoon corn broom sweeping a small dust pile",
    "a stylized broom, amber bristles, teal handle accent",
    "a bold cartoon broom with big fluffy straw",
    "a whimsical cartoon broom with a slightly curved handle",
    "a cozy cartoon broom in autumn tones",
    "a cartoon broom tied with a small rope band",
    "a rounded cute cartoon broom on a soft gradient",
    "a stylized handheld cartoon whisk broom",
    "a cartoon broom with a wooden handle and wide straw fan",
    "a cartoon broom on a warm sunset gradient background",
    "a playful cartoon broom with little motion swoosh lines",
    "a stylized broom leaning at an angle, golden hour tones",
    "a simple bold cartoon broom in a single warm color",
    "a cute cartoon broom with a small decorative bow",
    "a friendly cartoon corn broom centered on cream background",
    "a cartoon broom with a rounded chibi look",
    "a soft cartoon broom, honey and caramel colors",
    "a cheerful cartoon broom with golden straw bristles",
]

def workflow(pos, neg, seed):
    return {
        "3": {"class_type": "KSampler", "inputs": {
            "seed": seed, "steps": 26, "cfg": 7.0,
            "sampler_name": "euler_ancestral", "scheduler": "karras",
            "denoise": 1.0, "model": ["4", 0], "positive": ["6", 0],
            "negative": ["7", 0], "latent_image": ["5", 0]}},
        "4": {"class_type": "CheckpointLoaderSimple", "inputs": {"ckpt_name": CKPT}},
        "5": {"class_type": "EmptyLatentImage", "inputs": {"width": 512, "height": 512, "batch_size": 1}},
        "6": {"class_type": "CLIPTextEncode", "inputs": {"text": pos, "clip": ["4", 1]}},
        "7": {"class_type": "CLIPTextEncode", "inputs": {"text": neg, "clip": ["4", 1]}},
        "8": {"class_type": "VAEDecode", "inputs": {"samples": ["3", 0], "vae": ["4", 2]}},
        "9": {"class_type": "SaveImage", "inputs": {"filename_prefix": "appicon", "images": ["8", 0]}},
    }

def post(path, payload):
    data = json.dumps(payload).encode()
    req = urllib.request.Request(BASE + path, data=data, headers={"Content-Type": "application/json"})
    return json.load(urllib.request.urlopen(req, timeout=30))

def get(path):
    return json.load(urllib.request.urlopen(BASE + path, timeout=30))

# Queue everything first; ComfyUI processes sequentially.
jobs = []
for i, concept in enumerate(CONCEPTS, 1):
    seed = 77000 + i * 11
    wf = workflow(concept + STYLE, NEG, seed)
    pid = post("/prompt", {"prompt": wf, "client_id": "iconmaker"})["prompt_id"]
    jobs.append((i, concept, pid))
    print(f"queued {i:02d}: {concept}")

print("\nwaiting for results...")
for i, concept, pid in jobs:
    for _ in range(120):  # up to ~2 min each
        hist = get(f"/history/{pid}")
        if pid in hist and hist[pid].get("outputs"):
            imgs = hist[pid]["outputs"]["9"]["images"]
            info = imgs[0]
            q = urllib.parse.urlencode({"filename": info["filename"],
                                        "subfolder": info.get("subfolder", ""),
                                        "type": info.get("type", "output")})
            raw = urllib.request.urlopen(BASE + "/view?" + q, timeout=30).read()
            with open(os.path.join(OUT, f"{i:02d}.png"), "wb") as f:
                f.write(raw)
            print(f"saved {i:02d}.png  ({concept})")
            break
        time.sleep(1)
    else:
        print(f"TIMEOUT {i:02d}: {concept}")

with open(os.path.join(OUT, "concepts.txt"), "w") as f:
    for i, concept in enumerate(CONCEPTS, 1):
        f.write(f"{i:02d}  {concept}\n")

print(f"\ndone -> {OUT}")
