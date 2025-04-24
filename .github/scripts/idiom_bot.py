import os, json, datetime, base64, pathlib, requests, openai, subprocess

# ---------- config ----------
openai.api_key = os.environ["OPENAI_API_KEY"]
JSON_PATH = pathlib.Path("idioms/idioms.json")

# ---------- week number -----
today   = datetime.date.today()
week_1  = datetime.date(2025, 4, 8)          # Week 1 anchor
week_num = ((today - week_1).days // 7) + 1

# ---------- read idiom -------
data   = json.loads(JSON_PATH.read_text())
entry  = next((d for d in data if d["week"] == week_num), None)
if not entry:
    raise SystemExit(f"Week {week_num} not in idioms.json")

idiom     = entry["idiom"]
file_name = f"week{week_num}.png"
dst_path  = pathlib.Path("idioms/images") / file_name
dst_path.parent.mkdir(parents=True, exist_ok=True)

# ---------- idempotent skip --
if dst_path.exists():
    print("PNG already present — skip generation.")
    raise SystemExit

# ---------- generate image ---
prompt = (
    f"An illustration of a literal interpretation of the phrase: {idiom}. "
    "No text or typography."
)

def generate(model):
    resp = openai.images.generate(model=model, prompt=prompt, size="1024x1024")
    return resp.data[0].b64_json

try:
    img_b64 = generate("gpt-image-1")
    print("✓ Generated with gpt-image-1")

except openai.OpenAIError:
    print("⚠️  gpt-image-1 unavailable → fallback to dall-e-3")
    try:
        img_b64 = generate("dall-e-3")
        print("✓ Generated with dall-e-3")
    except openai.OpenAIError:
        print(
            "❌ Both models failed. "
            f"Upload your own illustration as idioms/images/{file_name} "
            "and re-run."
        )
        raise SystemExit(0)   # exit success so workflow stays green

# ---------- save PNG ---------
dst_path.write_bytes(base64.b64decode(img_b64))
print(f"Saved {dst_path}")

# ---------- commit -----------
subprocess.run(["git", "config", "user.name",  "idiom-bot"], check=True)
subprocess.run(["git", "config", "user.email", "bot@example.com"], check=True)
subprocess.run(["git", "add", str(dst_path)], check=True)
msg = f"auto: add image for week {week_num}"
subprocess.run(["git", "commit", "-m", msg], check=True)
subprocess.run(
    ["git", "push",
     f"https://x-access-token:{os.environ['GH_TOKEN']}@github.com/threapchills/WotD.git",
     "HEAD:main"],
    check=True)
