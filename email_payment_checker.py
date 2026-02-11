#!/usr/bin/env python3
"""
Email Payment Notification Checker
-----------------------------------
Prehľadáva email cez IMAP a hľadá správy o platbách/faktúrach.
Ak nájde nový platobný email, pošle push notifikáciu na mobil cez ntfy.sh.

Použitie:
    python3 email_payment_checker.py          # jednorazový beh
    python3 email_payment_checker.py --dry-run # testovací beh bez notifikácií
"""

import imaplib
import email
from email.header import decode_header
import os
import sys
import json
import logging
import argparse
import re
from datetime import datetime, timedelta
from pathlib import Path

import requests
from dotenv import load_dotenv

# Načítaj .env súbor
load_dotenv(Path(__file__).parent / ".env")

# Logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
    handlers=[
        logging.StreamHandler(),
        logging.FileHandler(Path(__file__).parent / "checker.log"),
    ],
)
log = logging.getLogger(__name__)

# ---------- Konfigurácia ----------

IMAP_SERVER = os.getenv("IMAP_SERVER", "imap.gmail.com")
IMAP_PORT = int(os.getenv("IMAP_PORT", "993"))
EMAIL_USER = os.getenv("EMAIL_USER", "")
EMAIL_PASS = os.getenv("EMAIL_PASS", "")

# ntfy.sh push notifikácie
NTFY_TOPIC = os.getenv("NTFY_TOPIC", "")
NTFY_SERVER = os.getenv("NTFY_SERVER", "https://ntfy.sh")

# Súbor na ukladanie ID už spracovaných emailov
SEEN_FILE = Path(__file__).parent / ".seen_emails.json"

# Kľúčové slová na detekciu platobných emailov (SK + EN + CZ)
PAYMENT_KEYWORDS = [
    # Slovenčina
    "platba", "zaplatenie", "faktúra", "faktura", "úhrada", "uhrada",
    "predplatné", "predplatne", "objednávka", "objednavka",
    "potvrdenie platby", "platba prijatá", "platba prijata",
    "automatická platba", "automaticka platba",
    "mesačná platba", "mesacna platba",
    "ročná platba", "rocna platba",
    "predĺženie služby", "predlzenie sluzby",
    "obnova predplatného", "obnova predplatneho",
    # Čeština
    "platba přijata", "platba prijata", "potvrzení platby",
    # Angličtina
    "payment", "invoice", "receipt", "billing", "subscription",
    "payment received", "payment confirmed", "payment successful",
    "your receipt", "order confirmation", "renewal",
    "monthly charge", "annual charge", "auto-renewal",
    "payment processed", "transaction",
]

# Odosielatelia typicky spojení s platbami
PAYMENT_SENDERS = [
    "paypal", "stripe", "apple", "google", "netflix", "spotify",
    "amazon", "microsoft", "adobe", "github", "digitalocean",
    "noreply", "billing", "payment", "invoice", "receipt",
    "faktura", "platba",
]


def load_seen_ids() -> set:
    """Načíta množinu ID už videných emailov."""
    if SEEN_FILE.exists():
        with open(SEEN_FILE, "r") as f:
            return set(json.load(f))
    return set()


def save_seen_ids(seen: set) -> None:
    """Uloží množinu ID videných emailov."""
    with open(SEEN_FILE, "w") as f:
        json.dump(list(seen), f)


def decode_mime_header(header_value: str) -> str:
    """Dekóduje MIME hlavičku emailu."""
    if not header_value:
        return ""
    parts = decode_header(header_value)
    decoded = []
    for part, charset in parts:
        if isinstance(part, bytes):
            decoded.append(part.decode(charset or "utf-8", errors="replace"))
        else:
            decoded.append(part)
    return " ".join(decoded)


def get_email_body(msg: email.message.Message) -> str:
    """Extrahuje textový obsah emailu."""
    body = ""
    if msg.is_multipart():
        for part in msg.walk():
            content_type = part.get_content_type()
            if content_type == "text/plain":
                payload = part.get_payload(decode=True)
                if payload:
                    charset = part.get_content_charset() or "utf-8"
                    body += payload.decode(charset, errors="replace")
    else:
        payload = msg.get_payload(decode=True)
        if payload:
            charset = msg.get_content_charset() or "utf-8"
            body = payload.decode(charset, errors="replace")
    return body


def is_payment_email(subject: str, sender: str, body: str) -> bool:
    """Vyhodnotí, či email hovorí o platbe."""
    text = f"{subject} {sender} {body}".lower()

    # Kontrola kľúčových slov
    keyword_matches = sum(1 for kw in PAYMENT_KEYWORDS if kw in text)

    # Kontrola odosielateľa
    sender_lower = sender.lower()
    sender_match = any(s in sender_lower for s in PAYMENT_SENDERS)

    # Kontrola súm peňazí (napr. 9.99€, $19.99, 100 CZK)
    money_pattern = r"(\d+[.,]\d{2}\s*[€$£]|[€$£]\s*\d+[.,]\d{2}|\d+[.,]\d{2}\s*(eur|usd|czk|skk)|(\d+)\s*(eur|usd|czk|skk))"
    has_money = bool(re.search(money_pattern, text, re.IGNORECASE))

    # Skóre: aspoň 2 kľúčové slová, alebo 1 kľúčové slovo + odosielateľ/suma
    if keyword_matches >= 2:
        return True
    if keyword_matches >= 1 and (sender_match or has_money):
        return True
    if sender_match and has_money:
        return True

    return False


def send_push_notification(subject: str, sender: str) -> bool:
    """Pošle push notifikáciu cez ntfy.sh."""
    if not NTFY_TOPIC:
        log.error("NTFY_TOPIC nie je nastavený! Notifikácia nebola odoslaná.")
        return False

    url = f"{NTFY_SERVER}/{NTFY_TOPIC}"
    title = "Platobný email"
    message = f"Od: {sender}\n{subject}"

    try:
        resp = requests.post(
            url,
            data=message.encode("utf-8"),
            headers={
                "Title": title,
                "Priority": "high",
                "Tags": "money_with_wings,email",
            },
            timeout=10,
        )
        if resp.status_code == 200:
            log.info(f"Notifikácia odoslaná: {subject}")
            return True
        else:
            log.error(f"Chyba pri odosielaní notifikácie: {resp.status_code}")
            return False
    except requests.RequestException as e:
        log.error(f"Chyba pri odosielaní notifikácie: {e}")
        return False


def check_emails(dry_run: bool = False) -> int:
    """Hlavná funkcia – skontroluje emaily a pošle notifikácie."""
    if not EMAIL_USER or not EMAIL_PASS:
        log.error("EMAIL_USER a EMAIL_PASS musia byť nastavené v .env súbore!")
        sys.exit(1)

    seen_ids = load_seen_ids()
    found_count = 0

    log.info(f"Pripájam sa k {IMAP_SERVER}...")

    try:
        mail = imaplib.IMAP4_SSL(IMAP_SERVER, IMAP_PORT)
        mail.login(EMAIL_USER, EMAIL_PASS)
        mail.select("INBOX")

        # Hľadaj emaily za posledných 24 hodín
        since_date = (datetime.now() - timedelta(days=1)).strftime("%d-%b-%Y")
        status, messages = mail.search(None, f'(SINCE "{since_date}")')

        if status != "OK":
            log.error("Nepodarilo sa vyhľadať emaily.")
            return 0

        email_ids = messages[0].split()
        log.info(f"Nájdených {len(email_ids)} emailov za posledných 24h.")

        for eid in email_ids:
            eid_str = eid.decode()

            if eid_str in seen_ids:
                continue

            status, data = mail.fetch(eid, "(RFC822)")
            if status != "OK":
                continue

            msg = email.message_from_bytes(data[0][1])
            subject = decode_mime_header(msg.get("Subject", ""))
            sender = decode_mime_header(msg.get("From", ""))
            body = get_email_body(msg)

            if is_payment_email(subject, sender, body):
                found_count += 1
                log.info(f"Platobný email: [{sender}] {subject}")

                if dry_run:
                    log.info("  (dry-run – notifikácia nebola odoslaná)")
                else:
                    send_push_notification(subject, sender)

            seen_ids.add(eid_str)

        mail.logout()

    except imaplib.IMAP4.error as e:
        log.error(f"IMAP chyba: {e}")
        sys.exit(1)
    except Exception as e:
        log.error(f"Neočakávaná chyba: {e}")
        sys.exit(1)

    save_seen_ids(seen_ids)
    log.info(f"Hotovo. Nájdených {found_count} platobných emailov.")
    return found_count


def main():
    parser = argparse.ArgumentParser(
        description="Kontrola emailov na platobné správy s push notifikáciami."
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Testovací beh – neodosiela notifikácie.",
    )
    args = parser.parse_args()

    check_emails(dry_run=args.dry_run)


if __name__ == "__main__":
    main()
