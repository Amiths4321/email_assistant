# email_ai.py
import os
import sys
import requests
from dotenv import load_dotenv

load_dotenv()

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
RAG_PATH = os.path.join(
    os.path.dirname(os.path.abspath(__file__)), "..", "rag_system"
)
sys.path.insert(0, RAG_PATH)

OLLAMA_HOST  = os.getenv("OLLAMA_HOST",  "http://10.22.39.192:11434")
OLLAMA_MODEL = os.getenv("OLLAMA_MODEL", "qwen2.5vl:latest")

CATEGORIES = [
    "Urgent", "Work", "HR", "Finance",
    "Personal", "Newsletter", "Spam", "Other"
]


def call_llm(prompt: str, max_tokens: int = 1024) -> str:
    """Call Qwen on remote GPU."""
    resp = requests.post(
        f"{OLLAMA_HOST}/api/generate",
        json={
            "model":   OLLAMA_MODEL,
            "prompt":  prompt,
            "stream":  False,
            "options": {"temperature": 0.1, "num_predict": max_tokens}
        },
        timeout=120
    )
    resp.raise_for_status()
    return resp.json()["response"].strip()


# ── Categorise ────────────────────────────────────────────────────────────────

def categorise_email(subject: str, snippet: str) -> str:
    """Classify email into one category."""
    prompt = f"""Classify this email into exactly ONE category.

Categories:
- Urgent: requires immediate action or response
- Work: professional work-related communication
- HR: human resources, leave, payroll, policies
- Finance: invoices, payments, receipts, banking
- Personal: from friends, family, personal matters
- Newsletter: marketing, subscriptions, announcements
- Spam: unwanted, promotional, suspicious
- Other: does not fit above categories

Email Subject: {subject}
Email Snippet: {snippet[:300]}

Respond with ONLY the category name. Nothing else."""

    result = call_llm(prompt, max_tokens=10)

    # Clean and validate
    for cat in CATEGORIES:
        if cat.lower() in result.lower():
            return cat
    return "Other"


def categorise_batch(emails: list[dict]) -> list[dict]:
    """Categorise multiple emails."""
    for e in emails:
        e["category"] = categorise_email(e["subject"], e["snippet"])
    return emails


# ── Summarise ─────────────────────────────────────────────────────────────────

def summarise_email(email: dict) -> dict:
    """
    Summarise an email and extract structured info.
    Returns { summary, action_items, key_info, sentiment }
    """
    prompt = f"""Analyse this email and extract:

FROM: {email['sender']}
SUBJECT: {email['subject']}
DATE: {email['date']}
BODY:
{email['body'][:2000]}

Provide:
1. SUMMARY: 2-3 sentence summary of the email
2. ACTION ITEMS: bullet list of any actions required (or "None")
3. KEY INFO: important dates, names, numbers mentioned
4. SENTIMENT: Positive / Neutral / Negative / Urgent
5. REPLY NEEDED: Yes / No

Format your response with these exact headings."""

    response = call_llm(prompt, max_tokens=512)

    # Parse sections
    sections   = {}
    current    = None
    lines      = response.split("\n")
    for line in lines:
        line = line.strip()
        if line.startswith("1. SUMMARY"):
            current = "summary"
            sections[current] = []
        elif line.startswith("2. ACTION"):
            current = "action_items"
            sections[current] = []
        elif line.startswith("3. KEY"):
            current = "key_info"
            sections[current] = []
        elif line.startswith("4. SENTIMENT"):
            current = "sentiment"
            sections[current] = []
        elif line.startswith("5. REPLY"):
            current = "reply_needed"
            sections[current] = []
        elif current and line:
            sections[current].append(line)

    def join(key):
        return "\n".join(sections.get(key, [])).strip()

    return {
        "summary":      join("summary") or response[:200],
        "action_items": join("action_items") or "None",
        "key_info":     join("key_info")     or "None",
        "sentiment":    join("sentiment")    or "Neutral",
        "reply_needed": join("reply_needed") or "Unknown"
    }


# ── Draft reply ───────────────────────────────────────────────────────────────

def draft_reply(
    email:       dict,
    instruction: str = "",
    use_rag:     bool = True
) -> str:
    """
    Draft a reply to an email.
    instruction: optional guidance e.g. "decline politely" or "agree and confirm"
    """
    # Get RAG context if relevant
    rag_context = ""
    if use_rag:
        try:
            from rag import get_collection, embed_texts
            query      = f"{email['subject']} {email['snippet']}"
            qvec       = embed_texts([query])[0]
            collection = get_collection()
            if collection.count() > 0:
                results = collection.query(
                    query_embeddings=[qvec],
                    n_results=2,
                    include=["documents"]
                )
                rag_context = "\n".join(results["documents"][0])
        except Exception:
            pass

    prompt = f"""You are drafting a professional email reply.

ORIGINAL EMAIL:
From: {email['sender']}
Subject: {email['subject']}
Date: {email['date']}
Body:
{email['body'][:1500]}

{f"REPLY INSTRUCTION: {instruction}" if instruction else ""}

{f"RELEVANT COMPANY CONTEXT:{chr(10)}{rag_context}" if rag_context else ""}

Write a professional, concise reply email.
- Start with appropriate greeting
- Address all points raised in the original email
- Keep it brief and professional
- End with appropriate sign-off
- Do NOT include subject line — just the body

REPLY:"""

    return call_llm(prompt, max_tokens=1024)


# ── Smart inbox ───────────────────────────────────────────────────────────────

def get_inbox_summary(emails: list[dict]) -> str:
    """Generate a natural language summary of the inbox."""
    if not emails:
        return "Your inbox is empty."

    counts = {}
    for e in emails:
        cat = e.get("category", "Other")
        counts[cat] = counts.get(cat, 0) + 1

    urgent   = [e for e in emails if e.get("category") == "Urgent"]
    subjects = [f"- {e['subject'][:60]} (from {e['sender'][:30]})"
                for e in emails[:5]]

    prompt = f"""You are an AI email assistant giving a friendly inbox briefing.

INBOX STATS:
Total emails: {len(emails)}
By category: {counts}

URGENT EMAILS: {len(urgent)}
{chr(10).join(f"- {e['subject']}" for e in urgent[:3]) if urgent else "None"}

RECENT EMAILS:
{chr(10).join(subjects)}

Give a brief, friendly 3-4 sentence inbox briefing.
Highlight what needs attention first."""

    return call_llm(prompt, max_tokens=256)