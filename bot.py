import os
import random
import requests

BOT_TOKEN = os.getenv("BOT_TOKEN")
CHANNEL_ID = os.getenv("CHANNEL_ID")

# 📂 Files che paths (.txt)
FILES = ["pyq_data/pyq.txt", "pyq_data/Marathi.txt", "pyq_data/English.txt"]
BATCH_SIZE = int(os.getenv("BATCH_SIZE", "1"))  # eg. 10 morning / 10 evening


def parse_questions(text):
    # 'Z:' chya aadhare split karne (Case-sensitive standard split)
    raw_blocks = text.split("\nZ:")
    
    # Jar file chi survat directly Z: ne jhali asel tar pahila part set karne
    if text.startswith("Z:"):
        raw_blocks[0] = text[2:]
    else:
        first_part = raw_blocks[0]
        if "Q:" in first_part:
            q_splits = first_part.split("\nQ:")
            if q_splits[0].strip().startswith("Q:"):
                raw_blocks[0] = q_splits[0][2:]
            elif len(q_splits) > 1:
                raw_blocks[0] = "EMPTY_Z\nQ:" + "\nQ:".join(q_splits[1:])

    questions = []

    for block in raw_blocks:
        block = block.strip()
        if not block:
            continue

        z_text = ""
        q_block_raw = block

        if "Q:" in block:
            parts = block.split("\nQ:", 1)
            if parts[0].strip() != "EMPTY_Z":
                z_text = parts[0].strip()
            q_block_raw = "Q:" + parts[1]
        elif block.startswith("Q:"):
            q_block_raw = block
        else:
            continue

        # Ekach Z: khali multiple Q: asu शकतात, mhanun sub-split
        sub_q_blocks = q_block_raw.split("\nQ:")
        for sub_block in sub_q_blocks:
            sub_block = sub_block.strip()
            if not sub_block or sub_block == "Q:":
                continue
                
            if not sub_block.startswith("Q:"):
                sub_block = "Q:" + sub_block

            # 🚨 STRIKT CASE-SENSITIVE CHECKING 🚨
            # Fakt '\nA:', '\nB:', '\nC:', '\nD:' asel tarach code pudhe jail
            # Jar 'a:', 'b:', 'A)' asel tar to skip karel
            if "\nA:" not in sub_block or "\nB:" not in sub_block or "\nC:" not in sub_block or "\nD:" not in sub_block:
                continue

            try:
                # Splitting strictly based on capital tags with newline
                q_and_a = sub_block.split("\nA:", 1)
                raw_q = q_and_a[0][2:].strip()  # Q: kadhun main prashna ghene

                a_and_b = q_and_a[1].split("\nB:", 1)
                opt_a = a_and_b[0].strip()

                b_and_c = a_and_b[1].split("\nC:", 1)
                opt_b = b_and_c[0].strip()

                c_and_d = b_and_c[1].split("\nD:", 1)
                opt_c = c_and_d[0].strip()
                opt_d = c_and_d[1].strip()

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
            except Exception:
                continue

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

# 🔀 Random Sample selection
selected = random.sample(all_questions, k=min(BATCH_SIZE, len(all_questions)))

for q in selected:
    send_poll(q["poll"], q["options"], q["correct"])
            
