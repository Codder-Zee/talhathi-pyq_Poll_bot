import os
import random
import re
import requests

BOT_TOKEN = os.getenv("BOT_TOKEN")
CHANNEL_ID = os.getenv("CHANNEL_ID")

# 📂 Files che paths (.txt)
FILES = ["pyq_data/pyq.txt", "pyq_data/Marathi.txt", "pyq_data/English.txt"]
BATCH_SIZE = int(os.getenv("BATCH_SIZE", "10"))  # eg. 10 pyqs randomly selection


def parse_questions(text):
    questions = []

    # 🔍 Strick Pattern: Jo kontyahi line breaking vr ghabrat nahi.
    # Z: optional ahe pan to Q: chya agdi vrch pahije.
    pattern = re.compile(
        r'(?:^|\n)Z:\s*(.*?)\s*\n\s*Q:\s*(.*?)\s*\n\s*A:\s*(.*?)\s*\n\s*B:\s*(.*?)\s*\n\s*C:\s*(.*?)\s*\n\s*D:\s*(.*?)(?=\n\s*(?:Z:|Q:)|$)',
        re.DOTALL
    )

    matches = pattern.findall(text)
    
    for match in matches:
        z_text = match[0].strip()
        raw_q = match[1].strip()
        opt_a = match[2].strip()
        opt_b = match[3].strip()
        opt_c = match[4].strip()
        opt_d = match[5].strip()

        # Strict Capital verification - bhighad kitihi aso, aapan check karnar
        # ki tags original string madhe standard hotya ka
        options = [opt_a, opt_b, opt_c, opt_d]
        correct = 0

        cleaned_options = []
        for idx, opt in enumerate(options):
            is_correct = "*" in opt
            clean_opt = opt.replace("*", "").strip()
            cleaned_options.append(clean_opt)
            if is_correct:
                correct = idx

        if len(cleaned_options) == 4:
            if z_text:
                poll_q = f"[{z_text}]\n\n➤ {raw_q}"
            else:
                poll_q = f"➤ {raw_q}"

            questions.append({
                "poll": poll_q,
                "options": cleaned_options,
                "correct": correct
            })

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

# 🔄 Loop for 3 files
for file_path in FILES:
    if os.path.exists(file_path): 
        with open(file_path, "r", encoding="utf-8") as f:
            file_questions = parse_questions(f.read())
            all_questions.extend(file_questions) 
            print(f"Loaded {len(file_questions)} questions from {file_path}")
    else:
        print(f"⚠️ Warning: File not found -> {file_path}")

print("TOTAL QUESTIONS AVAILABLE (ALL FILES):", len(all_questions))

if not all_questions:
    print("❌ No questions found in any of the files")
    exit()

# 🔀 Random Selection from ALL 3 FILES COMBINED
selected = random.sample(all_questions, k=min(BATCH_SIZE, len(all_questions)))

for q in selected:
    send_poll(q["poll"], q["options"], q["correct"])
            
