import os
import random
import requests

BOT_TOKEN = os.getenv("BOT_TOKEN")
CHANNEL_ID = os.getenv("CHANNEL_ID")

# 📂 फाईल्सची नावे बरोबर केली आहेत (.txt)
FILES = ["pyq_data/pyq.txt", "pyq_data/Marathi.txt", "pyq_data/English.txt"]
BATCH_SIZE = int(os.getenv("BATCH_SIZE", "1"))  # eg. 10 morning / 10 evening


def parse_questions(text):
    lines = [l.rstrip() for l in text.splitlines() if l.strip()]
    questions = []

    i = 0
    while i < len(lines):
        z_line = ""
        if lines[i].startswith("Z:"):
            z_line = lines[i][2:].strip()
            i += 1

        if i >= len(lines) or not lines[i].startswith("Q:"):
            i += 1
            continue

        raw_q = lines[i][2:].strip()
        i += 1

        options = []
        correct = 0

        for _ in range(4):
            if i >= len(lines):
                break
            line = lines[i]
            if "*" in line:
                correct = len(options)
                options.append(line[3:].replace("*", "").strip())
            else:
                options.append(line[3:].strip())
            i += 1

        if len(options) == 4:
            if z_line:
                poll_q = f"[{z_line}]\n\u200b\n➤ {raw_q}"
            else:
                poll_q = f"➤ {raw_q}"

            questions.append(
                {"poll": poll_q, "options": options, "correct": correct}
            )

    return questions


def send_poll(q, options, correct):
    url = f"https://api.telegram.org/bot{BOT_TOKEN}/sendPoll"
    payload = {
        "chat_id": CHANNEL_ID,
        "question": q,
        "options": options,
        "type": "quiz",
        "correct_option_id": correct,
        "is_anonymous": True,
    }
    r = requests.post(url, json=payload)
    print(r.text)


# ================= MAIN =================

all_questions = []

# 🔄 तिन्ही फाइल्स एक-एक करून वाचण्यासाठी लूप
for file_path in FILES:
    if os.path.exists(file_path):  # फाइल अस्तित्वात आहे की नाही हे चेक करणे
        with open(file_path, "r", encoding="utf-8") as f:
            file_questions = parse_questions(f.read())
            all_questions.extend(
                file_questions
            )  # सर्व प्रश्न एकाच लिस्टमध्ये एकत्र केले
            print(f"Loaded {len(file_questions)} questions from {file_path}")
    else:
        print(f"⚠️ Warning: File not found -> {file_path}")

print("TOTAL QUESTIONS AVAILABLE (ALL FILES):", len(all_questions))

if not all_questions:
    print("❌ No questions found in any of the files")
    exit()

# 🔀 तिन्ही फाइल्सच्या एकत्र केलेल्या प्रश्नांमधून RANDOM selection
selected = random.sample(all_questions, k=min(BATCH_SIZE, len(all_questions)))

for q in selected:
    send_poll(q["poll"], q["options"], q["correct"])
    
