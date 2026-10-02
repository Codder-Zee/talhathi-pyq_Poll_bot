import os
import random
import re
import requests

BOT_TOKEN = os.getenv("BOT_TOKEN")
CHANNEL_ID = os.getenv("CHANNEL_ID")

# 📂 PYQ files
# Ya 6 files madhun sagle PYQs ekatra gheun random selection hoil.
FILES = [
    "pyq_data/Marathi.txt",
    "pyq_data/English.txt",
    "pyq_data/Science.txt",
    "pyq_data/Economy.txt",
    "pyq_data/Polity.txt",
    "pyq_data/History.txt",
]

BATCH_SIZE = int(os.getenv("BATCH_SIZE", "10"))


def parse_questions(text):
    """
    File format:

    Z: Session
    Q: Question
    A: Option A
    B: Option B
    C: Option C
    D: Option D*
    E: Explanation

    E: optional aahe.
    E: asel tar Telegram quiz madhlya 💡 explanation madhe jail.
    E: nasel tar explanation pathavla janar nahi.
    """

    questions = []

    # D ani E vegvegale capture karto.
    # E nasel tari question parse hoil.
    pattern = re.compile(
        r'(?:^|\n)Z:\s*(.*?)\s*\n'
        r'\s*Q:\s*(.*?)\s*\n'
        r'\s*A:\s*(.*?)\s*\n'
        r'\s*B:\s*(.*?)\s*\n'
        r'\s*C:\s*(.*?)\s*\n'
        r'\s*D:\s*(.*?)(?=\n\s*E:|\n\s*Z:|\Z)'
        r'(?:\n\s*E:\s*(.*?))?'
        r'(?=\n\s*Z:|\Z)',
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

        # E: optional
        explanation = match[6].strip()

        options = [opt_a, opt_b, opt_c, opt_d]
        correct = None

        cleaned_options = []

        for idx, opt in enumerate(options):
            is_correct = "*" in opt

            # Correct answer mark (*) remove karto
            clean_opt = opt.replace("*", "").strip()
            cleaned_options.append(clean_opt)

            if is_correct:
                correct = idx

        # 4 options ani correct answer donhi valid asne required
        if len(cleaned_options) == 4 and correct is not None:

            if z_text:
                poll_q = f"[{z_text}]\n\n➤ {raw_q}"
            else:
                poll_q = f"➤ {raw_q}"

            questions.append({
                "poll": poll_q,
                "options": cleaned_options,
                "correct": correct,
                "explanation": explanation
            })

    return questions


def send_poll(q, options, correct, explanation=""):
    url = f"https://api.telegram.org/bot{BOT_TOKEN}/sendPoll"

    payload = {
        "chat_id": CHANNEL_ID,
        "question": q,
        "options": options,
        "type": "quiz",
        "correct_option_id": correct,
        "is_anonymous": True,
    }

    # Telegram quiz madhla 💡 Explanation option
    # E: asel tarch explanation pathavla jail.
    if explanation:
        # Telegram sendPoll explanation chi limit 200 characters aahe.
        # Mhanun motha E: 200 characters paryant gheto.
        payload["explanation"] = explanation[:200]

    try:
        r = requests.post(url, json=payload, timeout=30)
        print(r.text)
    except requests.RequestException as e:
        print(f"❌ Telegram request error: {e}")


# ================= MAIN =================

all_questions = []

# 🔄 Saglya 6 files madhun PYQs load kara
for file_path in FILES:

    if os.path.exists(file_path):

        try:
            with open(file_path, "r", encoding="utf-8") as f:
                file_questions = parse_questions(f.read())

            all_questions.extend(file_questions)

            print(
                f"Loaded {len(file_questions)} questions "
                f"from {file_path}"
            )

        except Exception as e:
            print(f"❌ Error reading {file_path}: {e}")

    else:
        print(f"⚠️ Warning: File not found -> {file_path}")


print("========================================")
print("TOTAL QUESTIONS AVAILABLE:", len(all_questions))
print("========================================")

if not all_questions:
    print("❌ No questions found in any of the files")
    exit()


# 🔀 Saglya 6 files madhun combined random selection
selected = random.sample(
    all_questions,
    k=min(BATCH_SIZE, len(all_questions))
)

print(f"🎲 Selected {len(selected)} random PYQs")


# 📤 Telegram var quiz polls send kara
for q in selected:

    send_poll(
        q["poll"],
        q["options"],
        q["correct"],
        q["explanation"]
    )
