import os, json, requests, datetime, base64, pathlib, openai

sheet_url = os.environ["SHEET_URL"]
openai.api_key = os.environ["OPENAI_API_KEY"]

# --- work out our week number (Week 1 starts 2025‑04‑08) ----
today       = datetime.date.today()
start_cycle = datetime.date(2025, 4, 6)
week_num    = ((today - start_cycle).days // 7) + 1

# --- fetch idiom text from the Google Sheet -----------------
rows  = requests.get(sheet_url, timeout=30).json()
idiom = next(r["Idiom"] for r in rows if int(r["Week"]) == week_num)

# --- generate a literal illustration with GPT‑4o -------------
prompt = f"Create a whimsical literal illustration of the idiom: “{idiom}” No text or typography - only picture. Warm sepia tones."
img_b64 = openai.images.generate(
            model="gpt-image-1",
            prompt=prompt,
            size="1024x1024").data[0].b64_json

# --- save PNG ------------------------------------------------
img_path = pathlib.Path(f"idioms/images/week{week_num}.png")
img_path.parent.mkdir(parents=True, exist_ok=True)
img_path.write_bytes(base64.b64decode(img_b64))

# --- append/update idioms.json -------------------------------
json_path = pathlib.Path("idioms/idioms.json")
data = json.loads(json_path.read_text()) if json_path.exists() else []
data = [d for d in data if d["week"] != week_num]  # avoid duplicates
data.append({"week": week_num, "idiom": idiom,
             "image": f"images/week{week_num}.png"})
data.sort(key=lambda d: d["week"])
json_path.write_text(json.dumps(data, indent=2))
