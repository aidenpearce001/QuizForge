import re

def parse_kananinirav_exam(content: str) -> list[dict]:
    """Parse kananinirav practice exam format.

    Format:
    1. Question text
        - A. Choice A
        - B. Choice B
        <details><summary>Answer</summary>
          Correct answer: A
        </details>
    """
    questions = []
    # Split by numbered questions
    blocks = re.split(r'^\d+\.\s+', content, flags=re.MULTILINE)

    for block in blocks[1:]:  # Skip content before first question
        lines = block.strip().split('\n')
        if not lines:
            continue

        question_text = lines[0].strip()

        choices = []
        choice_map = {}  # letter -> index
        for line in lines[1:]:
            line = line.strip()
            choice_match = re.match(r'^-\s+([A-F])\.\s+(.+)', line)
            if choice_match:
                letter = choice_match.group(1)
                text = choice_match.group(2).strip().rstrip('.')
                choice_map[letter] = len(choices)
                choices.append({"text": text, "is_correct": False})

        # Find correct answer in <details>
        full_block = '\n'.join(lines)
        answer_match = re.search(r'Correct answer:\s*([A-F,\s]+)', full_block, re.IGNORECASE)
        if answer_match and choices:
            correct_letters = [l.strip() for l in answer_match.group(1).split(',')]
            for letter in correct_letters:
                if letter in choice_map:
                    choices[choice_map[letter]]["is_correct"] = True

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
