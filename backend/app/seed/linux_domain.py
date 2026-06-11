"""
Seed script: create 'Linux Fundamentals & DevOps Culture' domain under a new
'Cloud & DevOps Foundations' subject, then generate ~200 questions via LLM
strictly based on Session 09 slide content.
"""
import asyncio
import json
import httpx
from sqlalchemy import select
from app.database import async_session
from app.models.subject import Subject
from app.models.domain import Domain
from app.models.question import Question
from app.config import settings

OPENROUTER_URL = "https://openrouter.ai/api/v1/chat/completions"
MODEL = "google/gemini-2.0-flash-001"

SUBJECT_NAME = "Cloud & DevOps Foundations"
DOMAIN_NAME  = "Linux Fundamentals & DevOps Culture"

# ── Slide content chunks ────────────────────────────────────────────────────
# Each entry: (topic_label, slide_text, n_questions)

TOPICS = [
    (
        "Why Linux & Linux Distributions",
        """\
Why Linux?
- Over 90% of production servers worldwide run Linux.
- 100% of containers run Linux — Docker, Kubernetes, ECS all use the Linux kernel.
- Major CI/CD platforms (GitHub Actions, GitLab, Jenkins) default to Linux runners.
- On AWS, Amazon Linux, Ubuntu, and RHEL dominate EC2.
- Terraform, Ansible, Docker are designed Linux-first.
- "If you cannot navigate a Linux terminal, you cannot do DevOps."

Linux Distributions:
- Ubuntu: most popular, beginner-friendly, huge community, apt package manager.
- CentOS / RHEL / Rocky Linux: enterprise, stable, long support cycles, yum/dnf.
- Amazon Linux 2023: optimized for AWS, free on EC2, dnf package manager.
- Alpine Linux: ultra-lightweight (~5MB), perfect for Docker containers, apk.
- Debian: rock-solid stability; Ubuntu is based on Debian.
- Choosing: Enterprise = RHEL. AWS = Amazon Linux. Containers = Alpine. Learning = Ubuntu.
- FPT Cloud uses Amazon Linux for EC2. VNG runs Alpine-based containers for ZaloPay (10x smaller images).""",
        20,
    ),
    (
        "Linux Filesystem Hierarchy",
        """\
Linux Filesystem Hierarchy Standard (FHS):
- / : root of everything, the top-level directory.
- /home : user home directories (/home/ubuntu, /home/ec2-user).
- /etc : configuration files (nginx.conf, ssh/sshd_config, hosts).
- /var : variable data — logs (/var/log), web files (/var/www).
- /tmp : temporary files, cleared on reboot.
- /opt : optional / third-party software installations.
- /usr : user programs, binaries, libraries.
- /bin, /sbin : essential system binaries (ls, cp, mount).
Analogy: / = root of a tree, /home = your desk, /etc = filing cabinet,
/var/log = security camera footage, /tmp = whiteboard.""",
        18,
    ),
    (
        "Navigation & File Commands",
        """\
Essential navigation and file commands:
- pwd: print working directory (where am I?).
- ls -la: list all files with details (permissions, owner, size, date).
- cd /path: change directory. cd .. = up, cd ~ = home, cd - = previous directory.
- mkdir -p dir1/dir2: create nested directories.
- cp -r source dest: copy files/directories recursively.
- mv old new: move or rename files.
- rm -rf dir: remove directory and contents. DANGEROUS — no recycle bin!
- find . -name "*.log": search for files by name pattern.
- WATCH OUT: rm -rf has NO undo. Always use ls before rm to verify. Horror story: rm -rf / destroyed a production server.""",
        18,
    ),
    (
        "Text Processing — cat, grep, awk, sed",
        """\
Text processing commands:
- cat file.txt: display entire file content.
- head -20 / tail -20: first/last 20 lines.
- tail -f /var/log/syslog: follow log in real-time (essential for debugging!).
- grep "ERROR" app.log: search for pattern in file.
- grep -r "TODO" .: recursive search in all files.
- wc -l file.txt: count lines in file.
- awk '{print $1, $3}' file.txt: extract columns 1 and 3.
- sed 's/old/new/g' file.txt: find and replace text globally.
- DevOps tip: grep is the #1 most-used command. Example: cat access.log | grep "500" | wc -l.""",
        18,
    ),
    (
        "Pipes & Redirects",
        """\
Pipes and redirection:
- | (pipe): send output of one command as input to another.
- Example: ps aux | grep nginx — find nginx processes.
- Example: cat access.log | grep "POST" | grep "500" | wc -l — count POST 500 errors.
- > : redirect output to file (overwrite). >> : append to file.
- 2>&1 : redirect stderr to stdout (capture all output).
- tee: write to both file AND screen simultaneously. Example: command | tee output.log.
- Unix Philosophy: small tools that do one thing well, combined via pipes.
- SSH brute-force detection: cat /var/log/auth.log | grep 'Failed password' | awk '{print $11}' | sort | uniq -c | sort -rn.""",
        15,
    ),
    (
        "Process Management",
        """\
Process management commands:
- ps aux: list all running processes (PID, CPU%, MEM%, command).
- top / htop: real-time process monitor (htop is prettier/interactive).
- kill PID: gracefully stop a process (sends SIGTERM signal).
- kill -9 PID: force kill (SIGKILL) — last resort only.
- systemctl start/stop/restart/status nginx: manage system services.
- systemctl enable nginx: start service on boot automatically.
- journalctl -u nginx -f: follow service logs in real-time.
- nohup command &: run process in background, survives logout.
- DevOps debugging flow: 'Nginx not responding' → systemctl status nginx → journalctl -u nginx → find error → fix → systemctl restart nginx.""",
        18,
    ),
    (
        "Networking Commands",
        """\
Linux networking commands:
- ip addr / ifconfig: show network interfaces and IP addresses.
- ping google.com: test connectivity (uses ICMP protocol).
- curl -I https://example.com: HTTP request, show headers only.
- curl -X POST -d '{"key":"value"}' URL: send POST request with JSON body.
- wget https://example.com/file.zip: download files from the internet.
- ss -tlnp / netstat -tlnp: show listening ports and owning process.
- dig example.com: DNS lookup — what IP does this domain resolve to?
- traceroute google.com: trace network path, show number of hops.
- Tiki debugging pattern: ss -tlnp (port listening?) → curl localhost:8080 (app responding?) → check AWS Security Group (firewall open?).""",
        18,
    ),
    (
        "Package Management",
        """\
Linux package management:
- Debian/Ubuntu: apt update && apt install nginx.
- RHEL/CentOS/Amazon Linux: yum install nginx or dnf install nginx.
- Alpine Linux: apk add nginx — lightweight, used in Docker containers.
- apt list --installed: list all installed packages.
- apt remove nginx: uninstall a package. apt upgrade: upgrade all packages.
- Key rule: always run apt update BEFORE apt install (refresh package index).
- Security: unattended-upgrades for automatic security patches.
- Best practice: pin versions in production — apt install nginx=1.24.0-1.
- DevOps relevance: Dockerfiles use these constantly. FROM ubuntu:22.04 → RUN apt update && apt install -y nginx.""",
        15,
    ),
    (
        "Users, Permissions & SSH",
        """\
Linux users and permissions:
- whoami: show current user. sudo: run command as root (superuser do).
- useradd / userdel: create/delete user accounts.
- chmod 755 file: set permissions — owner=rwx (7), group=rx (5), others=rx (5).
- read=4, write=2, execute=1. chmod +x script.sh makes file executable.
- chown user:group file: change file ownership.
- Permission format: rwxrwxrwx = owner | group | others (9 bits).
- SSH keys: ssh-keygen generates key pair; ssh-copy-id copies public key to server.
- chmod 600 ~/.ssh/id_rsa: private key must be readable only by owner.
- NEVER use password auth in production — always SSH keys.
- NEVER login as root directly — use sudo for individual commands.""",
        18,
    ),
    (
        "Bash Scripting",
        """\
Bash scripting fundamentals:
- #!/bin/bash: shebang line — tells OS which interpreter to use (must be first line).
- Variables: NAME="world" → echo "Hello $NAME" (no spaces around =).
- Conditionals: if [ -f file.txt ]; then echo "exists"; fi.
- Loops: for i in 1 2 3; do echo $i; done.
- Functions: function greet() { echo "Hello $1"; } ($1 = first argument).
- Exit codes: $? = last command exit code. 0 = success, non-zero = error/failure.
- Command substitution: TODAY=$(date +%Y-%m-%d).
- Best practice: set -euo pipefail (exit on error, undefined vars, pipe failures).
- CI/CD relevance: pipeline steps check $? to decide pass/fail.
- Pattern: command || echo 'FAILED' && exit 1.""",
        18,
    ),
    (
        "Cron Jobs",
        """\
Linux cron job scheduling:
- cron: Linux task scheduler that runs commands on a recurring schedule.
- crontab -e: edit your cron jobs. crontab -l: list current cron jobs.
- Format: minute  hour  day-of-month  month  day-of-week  command.
- */5 * * * * /home/user/health_check.sh — run every 5 minutes.
- 0 2 * * * /home/user/backup.sh — daily at 2:00 AM.
- 0 9 * * 1-5 /home/user/report.sh — weekdays (Mon–Fri) at 9:00 AM.
- Tip: use crontab.guru website to build and verify cron expressions.
- Gotcha: cron runs in minimal environment — always use full absolute paths.
- Cron concept reappears in DevOps: Kubernetes CronJobs, AWS EventBridge scheduled rules, CI/CD scheduled builds.""",
        14,
    ),
    (
        "Vim & Nano Text Editors",
        """\
Terminal text editors:
- You must edit files on servers with no GUI — editors are essential.
- Nano: simple beginner editor. nano file.txt → edit → Ctrl+O to save → Ctrl+X to exit.
- Vim: powerful, steep learning curve. vim file.txt.
- Vim has modes: Normal mode (navigate), Insert mode (press i to enter), Command mode (:).
- Vim essentials: i = enter insert mode, Esc = return to normal mode, :wq = save and quit, :q! = quit without saving.
- Vim navigation in normal mode: h/j/k/l (left/down/up/right), dd = delete line, yy = copy line, p = paste.
- Recommendation: learn Nano first, then Vim when comfortable.
- Classic interview question: "How do you exit Vim?" Answer: Esc then :q!""",
        14,
    ),
    (
        "DevOps Culture — Evolution & CAMS",
        """\
DevOps culture and evolution:
- Waterfall (1970s): Requirements → Design → Build → Test → Deploy. Sequential and slow.
- Agile (2001): Iterative sprints, faster feedback, but Dev and Ops still separated.
- DevOps (2009): Break the wall between Dev and Ops — 'you build it, you run it'.
- Platform Engineering (2020s): Internal Developer Platform — self-service infrastructure.
- Each evolution reduces the feedback loop time.
- DevOps is NOT a tool — it's a CULTURE of collaboration and automation.

CAMS Framework (coined by Damon Edwards and John Willis):
- Culture: collaboration between Dev, Ops, QA, Security. No blame, shared ownership.
- Automation: automate everything — builds, tests, deployments, infrastructure, monitoring.
- Measurement: measure deployment frequency, lead time, MTTR, change failure rate.
- Sharing: share knowledge, tools, responsibilities. Blameless postmortems.
- Without Culture, tools are useless. DevOps is 80% culture, 20% tools.
- DORA metrics (Google): Deployment Frequency, Lead Time for Changes, MTTR, Change Failure Rate.""",
        22,
    ),
    (
        "DevOps vs SRE vs Platform Engineering & Three Ways",
        """\
DevOps vs SRE vs Platform Engineering:
- DevOps: culture + practices for Dev and Ops collaboration.
- SRE (Site Reliability Engineering): Google's implementation of DevOps. Focuses on SLOs, error budgets, toil reduction, on-call, postmortems.
- Platform Engineering: build an Internal Developer Platform (IDP). Focuses on self-service, golden paths, developer experience.
- Relationship: DevOps = philosophy. SRE = practice. Platform Engineering = product. They are complementary.
- Analogy: DevOps = everyone should cook. Platform Engineering = build a great kitchen. SRE = head chef ensuring quality.

The Three Ways (from 'The Phoenix Project' by Gene Kim):
- First Way — FLOW: optimize left-to-right flow (Dev → Ops → Customer). Small batch sizes, reduce WIP, make work visible, automate.
- Second Way — FEEDBACK: fast right-to-left feedback loops. Monitoring, alerting, testing in pipeline, fast rollback.
- Third Way — CONTINUOUS LEARNING: experimentation and repetition. Blameless postmortems, chaos engineering.""",
        18,
    ),
    (
        "Git & Branching Strategies",
        """\
Git version control:
- Git = distributed version control — tracks every change to your code.
- Every developer has a FULL copy of the repository (distributed, not centralized).
- Core concepts: repository, commit, branch, merge, remote.
- git init: create new repo. git add: stage changes. git commit: snapshot.
- git log --oneline: view history. git diff: see changes.
- git push / git pull: sync with remote (GitHub, GitLab, Bitbucket).

Branching strategies:
- GitFlow: main + develop + feature/* + release/* + hotfix/*. Complex, good for scheduled releases, popular in enterprise.
- Trunk-Based Development: everyone commits to main, short-lived branches (<1 day). Simple, fast, requires strong CI/CD. Used by Google, Facebook.
- GitHub Flow: main + feature branches + Pull Requests. Simple, PR-based review, good for continuous deployment. Most popular.
- Key principle: the longer a branch lives, the harder the merge.
- Recommendation for beginners: start with GitHub Flow.

Pull Requests (PRs):
- PR = request to merge changes, triggers code review.
- Workflow: create branch → commit → push → open PR → review → merge.
- Good PR: small (<400 lines), clear description, linked to issue.
- Merge strategies: merge commit, squash merge, rebase merge.
- Google: every line of code is reviewed before merge — code review catches 60% of bugs.""",
        22,
    ),
]


# ── LLM question generation ─────────────────────────────────────────────────

def build_prompt(topic: str, content: str, n: int) -> str:
    return f"""You are creating a quiz for a university DevOps course. Generate exactly {n} multiple-choice questions about "{topic}" based ONLY on the slide content below. Do NOT add information not in the slides.

SLIDE CONTENT:
{content}

Rules:
- Questions must be simple and factual — directly answerable from the slide text above.
- Mix of: definitions, command syntax, which-tool-for-what, true/false style, "what happens when".
- 70% single-answer, 30% multiple-answer questions.
- Each question: 4 choices for single, 4-5 choices for multiple.
- No trick questions. No ambiguity.

Return ONLY a JSON array, no other text:
[
  {{
    "question": "question text here",
    "type": "single",
    "choices": [
      {{"text": "answer A", "is_correct": false}},
      {{"text": "answer B", "is_correct": true}},
      {{"text": "answer C", "is_correct": false}},
      {{"text": "answer D", "is_correct": false}}
    ],
    "explanation": "one sentence explanation of why the correct answer is right"
  }}
]

For multiple-answer questions use "type": "multiple" and mark 2+ choices as is_correct: true.
Generate exactly {n} questions."""


async def generate_questions(client: httpx.AsyncClient, topic: str, content: str, n: int) -> list:
    prompt = build_prompt(topic, content, n)
    for attempt in range(3):
        try:
            if attempt > 0:
                wait = 15 * attempt
                print(f"    retry {attempt} (waiting {wait}s)...", end=" ", flush=True)
                await asyncio.sleep(wait)
            resp = await client.post(
                OPENROUTER_URL,
                headers={
                    "Authorization": f"Bearer {settings.openrouter_api_key}",
                    "Content-Type": "application/json",
                },
                json={
                    "model": MODEL,
                    "messages": [{"role": "user", "content": prompt}],
                    "temperature": 0.7,
                },
                timeout=180,
            )
            resp.raise_for_status()
            raw = resp.json()["choices"][0]["message"]["content"].strip()
            if raw.startswith("```"):
                raw = raw.split("\n", 1)[1].rsplit("```", 1)[0]
            questions = json.loads(raw)
            return questions if isinstance(questions, list) else []
        except Exception as e:
            print(f"    LLM error (attempt {attempt+1}): {e}")
    return []


# ── Main ─────────────────────────────────────────────────────────────────────

async def main():
    if not settings.openrouter_api_key:
        print("ERROR: OPENROUTER_API_KEY not set")
        return

    async with async_session() as db:

        # ── Fetch instructor user ──────────────────────────────────────────
        from app.models.user import User
        instr_res = await db.execute(select(User).where(User.role == "instructor").limit(1))
        instructor = instr_res.scalar_one_or_none()
        if not instructor:
            print("ERROR: No instructor user found")
            return

        # ── Find or create subject ─────────────────────────────────────────
        subj_res = await db.execute(select(Subject).where(Subject.name == SUBJECT_NAME))
        subject = subj_res.scalar_one_or_none()
        if not subject:
            subject = Subject(name=SUBJECT_NAME, created_by=instructor.id)
            db.add(subject)
            await db.flush()
            print(f"Created subject: {SUBJECT_NAME}")
        else:
            print(f"Using existing subject: {SUBJECT_NAME}")

        # ── Find or create domain ──────────────────────────────────────────
        dom_res = await db.execute(
            select(Domain).where(Domain.name == DOMAIN_NAME, Domain.subject_id == subject.id)
        )
        domain = dom_res.scalar_one_or_none()
        if not domain:
            domain = Domain(name=DOMAIN_NAME, subject_id=subject.id)
            db.add(domain)
            await db.flush()
            print(f"Created domain: {DOMAIN_NAME}")
        else:
            print(f"Using existing domain: {DOMAIN_NAME}")

        await db.commit()

        # ── Generate questions per topic ───────────────────────────────────
        total_target = sum(n for _, _, n in TOPICS)
        print(f"\nGenerating ~{total_target} questions across {len(TOPICS)} topics...\n")

        all_added = 0

        # Only run topics that are missing questions (skip already-seeded ones)
        existing_res = await db.execute(
            select(Question.question_text).where(Question.domain_id == domain.id)
        )
        existing_texts = {r[0][:60] for r in existing_res.fetchall()}
        print(f"  ({len(existing_texts)} questions already in domain)\n")

        async with httpx.AsyncClient(timeout=180) as client:
            for i, (topic, content, n) in enumerate(TOPICS, 1):
                print(f"  [{i:02d}/{len(TOPICS)}] {topic} ({n} questions)...", end=" ", flush=True)
                await asyncio.sleep(3)  # avoid rate limits

                questions = await generate_questions(client, topic, content, n)
                if not questions:
                    print("SKIPPED (no response)")
                    continue

                added = 0
                for q in questions:
                    try:
                        question_text = q.get("question", "").strip()
                        q_type = q.get("type", "single")
                        choices = q.get("choices", [])
                        explanation = q.get("explanation", "").strip() or None

                        if not question_text or not choices:
                            continue

                        # Skip if already seeded (dedup by first 60 chars)
                        if question_text[:60] in existing_texts:
                            continue

                        # Validate: at least one correct answer
                        has_correct = any(c.get("is_correct") for c in choices)
                        if not has_correct:
                            continue

                        db.add(Question(
                            domain_id=domain.id,
                            source="seed",
                            question_text=question_text,
                            question_type=q_type if q_type in ("single", "multiple") else "single",
                            choices=[{"text": c["text"], "is_correct": bool(c.get("is_correct"))} for c in choices],
                            explanation=explanation,
                            for_exam=False,
                        ))
                        added += 1
                    except Exception as e:
                        print(f"\n    Error adding question: {e}")

                await db.commit()
                all_added += added
                print(f"added {added}")

        print(f"\n{'─'*50}")
        print(f"Done! Total questions added: {all_added}")
        print(f"Subject:  {SUBJECT_NAME}")
        print(f"Domain:   {DOMAIN_NAME}")


if __name__ == "__main__":
    asyncio.run(main())
