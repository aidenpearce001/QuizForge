import re

def parse_ditectrev_readme(content: str) -> list[dict]:
    """Parse Ditectrev README.md format.

    Format:
    ### Question text
    - [x] Correct answer
    - [ ] Wrong answer
    """
    questions = []
    # Split by ### headers (questions)
    blocks = re.split(r'^### ', content, flags=re.MULTILINE)

    for block in blocks[1:]:  # Skip content before first ###
        lines = block.strip().split('\n')
        if not lines:
            continue

        question_text = lines[0].strip()
        if not question_text:
            continue

        # Skip "Back to Top" links and non-question headers
        if "Back to Top" in question_text or "Table of Contents" in question_text:
            continue

        choices = []
        for line in lines[1:]:
            line = line.strip()
            correct_match = re.match(r'^- \[x\]\s*(.+)', line)
            wrong_match = re.match(r'^- \[ \]\s*(.+)', line)
            if correct_match:
                choices.append({"text": correct_match.group(1).strip().rstrip('.'), "is_correct": True})
            elif wrong_match:
                choices.append({"text": wrong_match.group(1).strip().rstrip('.'), "is_correct": False})

        if len(choices) >= 2:
            correct_count = sum(1 for c in choices if c["is_correct"])
            if correct_count > 1:
                q_type = "multiple"
            else:
                q_type = "single"

            questions.append({
                "question_text": question_text,
                "question_type": q_type,
                "choices": choices,
                "explanation": None,
            })

    return questions
