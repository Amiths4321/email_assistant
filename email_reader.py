# email_reader.py
import os
import imaplib
import email
from email.header import decode_header
from email.utils  import parsedate_to_datetime
from dotenv       import load_dotenv
from pathlib      import Path

load_dotenv()

EMAIL_ADDRESS = os.getenv("EMAIL_ADDRESS")
EMAIL_PASSWORD = os.getenv("EMAIL_PASSWORD")
IMAP_SERVER   = os.getenv("IMAP_SERVER",  "imap.gmail.com")
IMAP_PORT     = int(os.getenv("IMAP_PORT", 993))


def connect() -> imaplib.IMAP4_SSL:
    """Connect to IMAP server and login."""
    mail = imaplib.IMAP4_SSL(IMAP_SERVER, IMAP_PORT)
    mail.login(EMAIL_ADDRESS, EMAIL_PASSWORD)
    return mail


def decode_str(value) -> str:
    """Decode email header value safely."""
    if value is None:
        return ""
    decoded_parts = decode_header(value)
    result        = []
    for part, charset in decoded_parts:
        if isinstance(part, bytes):
            try:
                result.append(part.decode(charset or "utf-8", errors="replace"))
            except Exception:
                result.append(part.decode("utf-8", errors="replace"))
        else:
            result.append(str(part))
    return " ".join(result)


def get_body(msg) -> str:
    """Extract plain text body from email message."""
    body = ""
    if msg.is_multipart():
        for part in msg.walk():
            content_type = part.get_content_type()
            disposition  = str(part.get("Content-Disposition", ""))

            if content_type == "text/plain" and "attachment" not in disposition:
                try:
                    charset = part.get_content_charset() or "utf-8"
                    body    = part.get_payload(decode=True).decode(charset, errors="replace")
                    break
                except Exception:
                    pass
    else:
        try:
            charset = msg.get_content_charset() or "utf-8"
            body    = msg.get_payload(decode=True).decode(charset, errors="replace")
        except Exception:
            pass

    return body.strip()


def fetch_emails(
    folder:   str = "INBOX",
    limit:    int = 20,
    unread_only: bool = False
) -> list[dict]:
    """
    Fetch recent emails from the specified folder.
    Returns list of email dicts.
    """
    mail    = connect()
    emails  = []

    try:
        mail.select(folder)

        # Search criteria
        criteria = "UNSEEN" if unread_only else "ALL"
        _, data  = mail.search(None, criteria)
        ids      = data[0].split()

        # Get latest N emails
        ids = ids[-limit:][::-1]   # most recent first

        for email_id in ids:
            try:
                _, msg_data = mail.fetch(email_id, "(RFC822)")
                raw_email   = msg_data[0][1]
                msg         = email.message_from_bytes(raw_email)

                # Parse fields
                subject = decode_str(msg.get("Subject", "(No subject)"))
                sender  = decode_str(msg.get("From",    ""))
                to      = decode_str(msg.get("To",      ""))
                date    = msg.get("Date", "")
                body    = get_body(msg)

                # Parse date
                try:
                    dt = parsedate_to_datetime(date)
                    date_str = dt.strftime("%Y-%m-%d %H:%M")
                except Exception:
                    date_str = date[:20] if date else ""

                emails.append({
                    "id":      email_id.decode(),
                    "subject": subject,
                    "sender":  sender,
                    "to":      to,
                    "date":    date_str,
                    "body":    body,
                    "snippet": body[:200].replace("\n", " ")
                })

            except Exception as e:
                print(f"Error fetching email {email_id}: {e}")
                continue

    finally:
        mail.logout()

    return emails


def get_folders() -> list[str]:
    """List all folders/labels in the mailbox."""
    mail    = connect()
    _, data = mail.list()
    mail.logout()

    folders = []
    for item in data:
        if item:
            parts = item.decode().split('"/"')
            if parts:
                folder = parts[-1].strip().strip('"')
                folders.append(folder)
    return folders