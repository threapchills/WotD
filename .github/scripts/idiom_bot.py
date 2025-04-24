import os, json, datetime, base64, pathlib, requests, openai, time

# --- config ---------------------------------------------------
openai.api_key = os.environ["OPENAI_API_KEY"]

# spreadsheet is optional; we'll read idioms.json and add if missing
JSON_PATH = pathlib.Path("idioms/idioms.json")

# ---- work out current week number (Week 1 = 8 Apr 2025) ------
today        = datetime.date.today()
week_1       = datetime.date(2025, 4, 8)
week_num     = ((today - week_1).days // 7) + 1

# ---- read idiom list ----------------------------------------
data = json.loads(JSON_PATH.read_text())
idiom_entry = next((d for d in data if d["week"] == week_num), None)
if not idiom_entry:
    raise SystemExit(f"Week {week_num} not found in idioms.json")

idiom = idiom_entry["idiom"]
file_name = f"week{week_num}.png"
dst_path  = pathlib.Path("idioms/images") / file_name

# skip if image already exists (reruns are idempotent)
if dst_path.exists():
    print("PNG already present, nothing to do.")
    raise SystemExit

# ---- call gpt-image-1 ---------------------------------------
prompt = f"An illustration of a literal interpretation of the phrase: {idiom}. No text."
resp   = openai.images.generate(
            model="gpt-image-1",
            prompt=prompt,
            size="1024x1024")

img_b64 = resp.data[0].b64_json
dst_path.parent.mkdir(parents=True, exist_ok=True)
dst_path.write_bytes(base64.b64decode(img_b64))
print(f"Saved {dst_path}")

# ---- commit via git CLI -------------------------------------
from subprocess import run, check_call
run(["git", "config", "user.name", "idiom-bot"], check=True)
run(["git", "config", "user.email", "bot@example.com"], check=True)
run(["git", "add", str(dst_path)], check=True)
json_dump = json.dumps(data, indent=2)
JSON_PATH.write_text(json_dump)        # (file unchanged but keeps add +0 −0 clean)
run(["git", "add", str(JSON_PATH)], check=True)
msg = f"auto: add image for week {week_num}"
run(["git", "commit", "-m", msg], check=True)
run(["git", "push", f"https://x-access-token:{os.environ['GH_TOKEN']}@github.com/threapchills/WotD.git", "HEAD:main"], check=True)

# --- save PNG if generation succeeds OR skip if not verified ----
try:
    resp = openai.images.generate(
              model="gpt-image-1",
              prompt=prompt,
              size="1024x1024")
    img_b64 = resp.data[0].b64_json
    dst_path.write_bytes(base64.b64decode(img_b64))
    print(f"Saved {dst_path}")
except openai.OpenAIError as e:
    # 403 or any other model-gate → inform & exit 0
    print("⚠️  GPT-image-1 unavailable. "
          "Upload the illustration manually as "
          f"idioms/images/{file_name} and re-run.")
    raise SystemExit(0)

