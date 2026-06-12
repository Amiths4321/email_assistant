# AI Email Assistant

A production-ready AI email assistant built as **Project 12** in the AI Solution Architecture learning series. Connects to any email account via IMAP, reads your inbox, categorises emails with AI, summarises long threads, and drafts professional replies — all powered by Qwen2.5-VL on a remote GPU.

---

## Where this fits in the AI development lifecycle

```
1-11. All previous projects    ✅  RAG, agents, voice, multimodal, streaming
12.   AI Email Assistant       ← this project (email automation)
13.   CI/CD for AI (MLOps)     Upcoming
14.   Docker + AWS             Upcoming
```

---

## What this project does

```
Connect to inbox (IMAP)
        ↓
Fetch last N emails (headers + body)
        ↓
AI categorises each email → Work / Urgent / HR / Finance / Personal / Newsletter / Spam
        ↓
Select an email → AI summarises in seconds
        ↓
One click → AI drafts a professional reply
        ↓
You review, edit, and copy to your email client
```

---

## Safety — what the AI never does

| Action | Status |
|---|---|
| Read emails | ✅ Yes — read only |
| Categorise emails | ✅ Yes — labels only |
| Summarise emails | ✅ Yes — no changes |
| Draft replies | ✅ Yes — text only, you copy manually |
| Send emails | ❌ Never automatic |
| Delete emails | ❌ Never |
| Mark as read | ❌ Never |
| Modify inbox | ❌ Never |

IMAP is a read-only protocol. Nothing in your inbox is ever changed.

---

## Features

- **IMAP connection** — works with Gmail, Yahoo, Outlook, any IMAP provider
- **AI categorisation** — 8 categories: Urgent, Work, HR, Finance, Personal, Newsletter, Spam, Other
- **Inbox briefing** — AI summarises your inbox in 3-4 sentences on load
- **Email summariser** — summary, action items, key info, sentiment, reply needed flag
- **Reply drafter** — drafts contextual replies using email thread + RAG knowledge base
- **Category filter** — view emails by category with colour coding
- **Edit before copy** — all drafts are editable before you copy to your email client

---

## Project Structure

```
email_assistant/
│
├── email_app.py         # Streamlit UI — main entry point
├── email_reader.py      # IMAP connection and email fetching
├── email_ai.py          # categorise, summarise, draft with Qwen
│
├── .env                 # email credentials — never commit this
└── requirements.txt
```

---

## Prerequisites

- Python 3.9+
- Virtual environment activated
- Ollama running on remote GPU at `http://10.22.39.192:11434`
- Model `qwen2.5vl:latest` pulled on the remote GPU
- An email account with IMAP enabled and an app password

---

## Installation

```powershell
cd email_assistant

# Activate venv
C:\Dev\venv\Scripts\Activate.ps1

# Install dependencies
pip install -r requirements.txt
```

### `requirements.txt`

```
streamlit
requests
python-dotenv
# imaplib and email are built into Python — no install needed
```

---

## Email Provider Setup

### Gmail

```
Step 1: Enable IMAP
  Gmail → Settings (gear icon) → See all settings
  → Forwarding and POP/IMAP → Enable IMAP → Save Changes

Step 2: Create App Password (required — normal password will not work)
  myaccount.google.com → Security
  → 2-Step Verification (must be ON first)
  → Search "App passwords" at the top
  → Select app: Mail → Select device: Windows
  → Copy the 16-character password
```

### Yahoo Mail

```
Step 1: Enable IMAP
  Yahoo Mail → Settings → More Settings → Mailboxes
  → Your account → IMAP → Enabled

Step 2: Create App Password
  Yahoo Account Security → Generate app password
  → Select app: Other app → name it "AI Assistant"
  → Copy the generated password
```

### Outlook / Hotmail

```
IMAP is enabled by default.
Use your normal Outlook password.
(Microsoft accounts with 2FA need an app password too)
```

---

## Configuration — `.env`

```
# Gmail
EMAIL_ADDRESS=your_email@gmail.com
EMAIL_PASSWORD=your_16_char_app_password
IMAP_SERVER=imap.gmail.com
IMAP_PORT=993

# Yahoo Mail
# EMAIL_ADDRESS=your_email@yahoo.com
# EMAIL_PASSWORD=your_yahoo_app_password
# IMAP_SERVER=imap.mail.yahoo.com
# IMAP_PORT=993

# Outlook
# EMAIL_ADDRESS=your_email@outlook.com
# EMAIL_PASSWORD=your_password
# IMAP_SERVER=imap-mail.outlook.com
# IMAP_PORT=993

# Ollama
OLLAMA_HOST=http://10.22.39.192:11434
OLLAMA_MODEL=qwen2.5vl:latest
```

---

## Running the App

```powershell
# Always run from the project root
cd "C:\Users\amith\Desktop\Confidential\Misc Projects\P2\email_assistant"

# Activate venv
C:\Dev\venv\Scripts\Activate.ps1

# Launch
streamlit run email_app.py
```

Open `http://localhost:8501` in your browser.

---

## How to Use

### Step 1 — Fetch inbox
- Set how many emails to fetch (5-50)
- Toggle "Unread only" if needed
- Click **Fetch inbox**
- AI automatically categorises all emails

### Step 2 — Browse inbox
- Emails shown with colour-coded category icons
- 🔴 Urgent · 🔵 Work · 🟣 HR · 🟡 Finance · 🟢 Personal · ⚪ Newsletter · ⛔ Spam
- Use category filter dropdown to focus on one type
- Read the AI inbox briefing at the top

### Step 3 — Select an email
Click any email in the left panel. Three tabs appear on the right:

**📧 Email tab** — full email body

**📋 Summary tab** — click Generate summary to get:
- 2-3 sentence summary
- Action items (bulleted list)
- Key info (dates, names, numbers)
- Sentiment (Positive / Neutral / Negative / Urgent)
- Reply needed (Yes / No)

**✍️ Draft reply tab**:
- Optional: type an instruction like "decline politely" or "ask for more time"
- Toggle RAG to use TechCorp knowledge base for company context
- Click **Draft reply**
- Edit the draft in the text area
- Copy manually to your email client

---

## Email Categories

| Category | What goes here |
|---|---|
| Urgent | Requires immediate action or response |
| Work | Professional work communication |
| HR | Leave, payroll, policies, appraisals |
| Finance | Invoices, payments, receipts, banking |
| Personal | Friends, family, personal matters |
| Newsletter | Marketing, subscriptions, announcements |
| Spam | Unwanted, promotional, suspicious |
| Other | Does not fit above |

---

## Architecture — How It Works

### Email fetching pipeline

```
imaplib.IMAP4_SSL connects to mail server over port 993 (SSL)
        ↓
mail.login(email, app_password)
        ↓
mail.select("INBOX")
        ↓
mail.search(None, "ALL")  → list of email IDs
        ↓
mail.fetch(id, "(RFC822)")  → raw email bytes per ID
        ↓
email.message_from_bytes()  → parse headers + body
        ↓
Return list of dicts: { id, subject, sender, date, body, snippet }
```

### AI categorisation pipeline

```
For each email:
  subject + snippet (200 chars)
        ↓
  Qwen reads: "Classify into: Urgent/Work/HR/Finance/Personal/Newsletter/Spam/Other"
        ↓
  Returns single category word
        ↓
  Added to email dict as "category"
```

### Draft reply pipeline

```
Selected email (full body)
        ↓
RAG search: find relevant TechCorp chunks for context
        ↓
Prompt: "Draft a professional reply to this email.
         Consider company context: {rag_chunks}
         Instruction: {user_instruction}"
        ↓
Qwen generates reply text
        ↓
Shown in editable text area
        ↓
You copy to your email client manually
```

---

## Using RAG Context in Replies

When **Use TechCorp knowledge base** is toggled on, the reply drafter searches your ChromaDB index for relevant company information before drafting.

Example: Someone emails asking about TechCorp's leave policy. The drafter:
1. Searches ChromaDB for "leave policy"
2. Finds the relevant chunk from `hr_policy.txt`
3. Uses that information in the draft reply

This makes replies accurate for company-specific topics without the AI guessing.

To use this feature, make sure your rag_system is indexed:
```powershell
cd ..\rag_system
python ingest.py
```

---

## Common Errors

| Error | Cause | Fix |
|---|---|---|
| `IMAP4.error: b'[AUTHENTICATIONFAILED]'` | Wrong password or app password not created | Use App Password, not your real password |
| `Connection refused` | IMAP not enabled on account | Enable IMAP in email settings |
| `SSL: CERTIFICATE_VERIFY_FAILED` | SSL issue on Windows | `pip install --upgrade certifi` |
| `imaplib.abort` | Connection timeout | Reduce email fetch limit, try again |
| `No emails returned` | Wrong search criteria | Try with `unread_only=False` |
| `Ollama connection error` | Remote GPU not reachable | Check `curl http://10.22.39.192:11434/api/tags` |
| Empty body extracted | HTML-only email | Normal — some newsletters have no plain text part |

---

## Extending the Project

### Add SMTP sending (with confirmation)

```python
# Add to email_reader.py
import smtplib
from email.mime.text import MIMEText

def send_email(to: str, subject: str, body: str) -> bool:
    """Send email — only call after explicit user confirmation."""
    msg              = MIMEText(body)
    msg["Subject"]   = subject
    msg["From"]      = EMAIL_ADDRESS
    msg["To"]        = to

    with smtplib.SMTP_SSL("smtp.gmail.com", 465) as server:
        server.login(EMAIL_ADDRESS, EMAIL_PASSWORD)
        server.send_message(msg)
    return True
```

Add a "Send" button in the UI that:
1. Shows a confirmation dialog with the full email
2. Requires the user to type "CONFIRM" before sending
3. Only then calls `send_email()`

### Add email search

```python
def search_emails(query: str) -> list[dict]:
    """Search inbox by subject or sender."""
    mail = connect()
    mail.select("INBOX")
    _, data = mail.search(None, f'SUBJECT "{query}"')
    # ... fetch and return matching emails
```

### Add attachment handling

```python
def get_attachments(msg) -> list[dict]:
    """Extract attachments from email."""
    attachments = []
    for part in msg.walk():
        if part.get_content_disposition() == "attachment":
            filename = part.get_filename()
            data     = part.get_payload(decode=True)
            attachments.append({"filename": filename, "data": data})
    return attachments
```

---

## Part of a Larger Project Series

| # | Project | Core skill learned |
|---|---|---|
| 1 | Problem Definition Validator | Define before building |
| 2 | Data Collection & Cleaning | Ingest, clean, mask PII |
| 3 | Chunking Strategies Comparator | Fixed, sentence, paragraph, semantic |
| 4 | PDF Document Analyser | Dynamic RAG, page references |
| 5 | AI Data Analyst | Code execution, text-to-SQL, charts |
| 6 | Multi-Agent Research System | Agent specialisation, orchestration |
| 7 | Production AI SaaS | Auth, database, rate limiting, deployment |
| 8 | Multimodal AI | Image + text, OCR, vision agents |
| 9 | Voice AI Assistant | Whisper STT, pyttsx3 TTS |
| 10 | Knowledge Graph AI | GraphRAG, entity extraction, NetworkX |
| 11 | Streaming Chat | SSE, st.write_stream, real-time tokens |
| 12 | **AI Email Assistant** | **IMAP, email automation, reply drafting** |
| 13 | CI/CD for AI (MLOps) | GitHub Actions, quality gates |
| 14 | Docker + AWS | Containers, cloud deployment |

---

## Author

Built as part of an AI Solution Architecture learning project.
Model: `qwen2.5vl:latest` via Ollama on remote GPU `10.22.39.192:11434`
Email protocol: IMAP over SSL (port 993) — read only
