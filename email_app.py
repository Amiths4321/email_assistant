# email_app.py
# streamlit run email_app.py

import sys, os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

import streamlit as st
from email_reader import fetch_emails
from email_ai     import (
    categorise_batch, summarise_email,
    draft_reply, get_inbox_summary, CATEGORIES
)

st.set_page_config(
    page_title="AI Email Assistant",
    page_icon="📧",
    layout="wide"
)

# ── Session state ─────────────────────────────────────────────────────────────
if "emails"         not in st.session_state: st.session_state.emails         = []
if "selected_email" not in st.session_state: st.session_state.selected_email = None
if "summaries"      not in st.session_state: st.session_state.summaries      = {}
if "drafts"         not in st.session_state: st.session_state.drafts         = {}

# ── Sidebar ───────────────────────────────────────────────────────────────────
with st.sidebar:
    st.title("📧 AI Email Assistant")
    st.caption("Read · Categorise · Summarise · Draft replies")

    st.divider()

    # Fetch settings
    limit       = st.slider("Emails to fetch", 5, 50, 20)
    unread_only = st.toggle("Unread only", value=False)

    if st.button("Fetch inbox", type="primary", use_container_width=True):
        with st.spinner("Connecting to email..."):
            try:
                emails = fetch_emails(limit=limit, unread_only=unread_only)
                st.success(f"Fetched {len(emails)} emails")
            except Exception as e:
                st.error(f"Connection failed: {str(e)}")
                emails = []

        if emails:
            with st.spinner("Categorising emails with AI..."):
                emails = categorise_batch(emails)
            st.session_state.emails = emails
            st.rerun()

    st.divider()

    # Category filter
    if st.session_state.emails:
        st.markdown("**Filter by category**")
        all_cats  = ["All"] + CATEGORIES
        selected_cat = st.selectbox("Category:", all_cats)

        # Count per category
        for cat in CATEGORIES:
            count = sum(
                1 for e in st.session_state.emails
                if e.get("category") == cat
            )
            if count:
                st.caption(f"{cat}: {count}")

# ── Main area ─────────────────────────────────────────────────────────────────
st.title("📧 AI Email Assistant")

if not st.session_state.emails:
    st.info("Click **Fetch inbox** in the sidebar to load your emails.")
    st.markdown("""
**What this assistant does:**
- 📥 Reads your inbox via IMAP
- 🏷️ Categorises each email (Work, Urgent, HR, Finance...)
- 📋 Summarises long emails in seconds
- ✍️ Drafts professional replies with one click
- 🔍 Uses your TechCorp knowledge base for context

**What it never does:**
- ❌ Never sends emails automatically
- ❌ Never deletes anything
- ❌ Never modifies your inbox
""")
    st.stop()

# Inbox summary
with st.expander("📊 Inbox briefing", expanded=True):
    with st.spinner("Generating briefing..."):
        briefing = get_inbox_summary(st.session_state.emails)
    st.markdown(briefing)

st.divider()

# Filter emails
emails = st.session_state.emails
if "selected_cat" in st.session_state and st.session_state.get("selected_cat", "All") != "All":
    emails = [e for e in emails if e.get("category") == st.session_state.selected_cat]

# ── Two column layout ─────────────────────────────────────────────────────────
col_list, col_detail = st.columns([2, 3])

with col_list:
    st.subheader(f"Inbox ({len(emails)} emails)")

    # Category filter
    filter_cat = st.selectbox(
        "Show:", ["All"] + CATEGORIES,
        key="cat_filter"
    )
    if filter_cat != "All":
        display_emails = [e for e in emails if e.get("category") == filter_cat]
    else:
        display_emails = emails

    for i, e in enumerate(display_emails):
        cat   = e.get("category", "Other")
        color = {
            "Urgent":     "🔴",
            "Work":       "🔵",
            "HR":         "🟣",
            "Finance":    "🟡",
            "Personal":   "🟢",
            "Newsletter": "⚪",
            "Spam":       "⛔",
            "Other":      "⚫"
        }.get(cat, "⚫")

        selected = st.session_state.selected_email == i
        btn_label = (
            f"{color} **{e['subject'][:35]}**\n"
            f"From: {e['sender'][:30]}\n"
            f"{e['date']} · {cat}"
        )

        if st.button(
            btn_label,
            key=f"email_{i}",
            use_container_width=True,
            type="primary" if selected else "secondary"
        ):
            st.session_state.selected_email = i
            st.rerun()

with col_detail:
    if st.session_state.selected_email is not None:
        idx   = st.session_state.selected_email
        email = display_emails[idx] if idx < len(display_emails) else None

        if email:
            st.subheader(email["subject"])
            c1, c2, c3 = st.columns(3)
            c1.caption(f"From: {email['sender']}")
            c2.caption(f"Date: {email['date']}")
            c3.caption(f"Category: {email.get('category', 'Other')}")

            tab1, tab2, tab3 = st.tabs([
                "📧 Email",
                "📋 Summary",
                "✍️ Draft reply"
            ])

            # ── Tab 1: Full email ─────────────────────────────────────────
            with tab1:
                st.text_area(
                    "Email body:",
                    email["body"][:3000],
                    height=300,
                    disabled=True
                )

            # ── Tab 2: AI Summary ─────────────────────────────────────────
            with tab2:
                email_key = email["id"]
                if email_key not in st.session_state.summaries:
                    if st.button("Generate summary", type="primary"):
                        with st.spinner("Analysing email..."):
                            summary = summarise_email(email)
                            st.session_state.summaries[email_key] = summary
                            st.rerun()
                else:
                    s = st.session_state.summaries[email_key]
                    st.markdown(f"**Summary:** {s['summary']}")
                    st.markdown(f"**Action items:** {s['action_items']}")
                    st.markdown(f"**Key info:** {s['key_info']}")

                    cols = st.columns(2)
                    cols[0].metric("Sentiment",    s["sentiment"])
                    cols[1].metric("Reply needed", s["reply_needed"])

            # ── Tab 3: Draft reply ────────────────────────────────────────
            with tab3:
                instruction = st.text_input(
                    "Reply instruction (optional):",
                    placeholder="e.g. decline politely / agree and confirm / ask for more details"
                )
                use_rag = st.toggle("Use TechCorp knowledge base", value=True)

                draft_key = f"{email['id']}_{instruction}"
                if draft_key not in st.session_state.drafts:
                    if st.button("Draft reply", type="primary"):
                        with st.spinner("Drafting reply..."):
                            draft = draft_reply(email, instruction, use_rag)
                            st.session_state.drafts[draft_key] = draft
                            st.rerun()
                else:
                    draft = st.session_state.drafts[draft_key]
                    edited = st.text_area(
                        "Draft reply (edit before sending):",
                        draft,
                        height=300
                    )

                    st.warning(
                        "⚠️ Review carefully before sending. "
                        "Copy this text into your email client to send."
                    )

                    if st.button("Copy to clipboard"):
                        st.code(edited)
                        st.info("Select all text above and copy manually.")

                    if st.button("Regenerate", type="secondary"):
                        del st.session_state.drafts[draft_key]
                        st.rerun()
    else:
        st.info("← Select an email from the list to view details")