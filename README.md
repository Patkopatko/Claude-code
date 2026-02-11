# Email Payment Notification Checker

Script, ktory kazdy den skontroluje tvoj email a ak najde spravu o platbe (faktura, potvrdenie, subscription...), posle ti push notifikaciu na mobil.

## Ako to funguje

1. Pripoji sa na tvoj email cez IMAP (Gmail, Outlook, ...)
2. Precita emaily za poslednych 24 hodin
3. Analyzuje predmet, odosielatela a telo emailu na klucove slova (SK/CZ/EN)
4. Ak najde platobny email, posle push notifikaciu cez [ntfy.sh](https://ntfy.sh)

## Instalacia

### 1. Nainštaluj závislosti

```bash
pip install -r requirements.txt
```

### 2. Nastav ntfy.sh na mobile

- Stiahni appku **ntfy** z [Google Play](https://play.google.com/store/apps/details?id=io.heckel.ntfy) alebo [App Store](https://apps.apple.com/app/ntfy/id1625396347)
- V appke klikni "+" a pridaj topic, napr. `moje-platby-xyz123`
- Zapni notifikacie pre tento topic

### 3. Nastav konfiguraciu

```bash
cp .env.example .env
```

Uprav `.env` subor:

```
IMAP_SERVER=imap.gmail.com
EMAIL_USER=tvoj@gmail.com
EMAIL_PASS=tvoje-app-heslo
NTFY_TOPIC=moje-platby-xyz123
```

**Pre Gmail:** Musis pouzit App Password – vygeneruj ho na https://myaccount.google.com/apppasswords

### 4. Otestuj

```bash
python3 email_payment_checker.py --dry-run
```

### 5. Nastav denne spustanie (cron)

```bash
crontab -e
```

Pridaj riadok (spusti kazdy den o 8:00):

```
0 8 * * * cd /cesta/k/projektu && /usr/bin/python3 email_payment_checker.py
```

## Pouzitie

```bash
# Normalny beh – skontroluje a posle notifikacie
python3 email_payment_checker.py

# Testovaci beh – neodosiela notifikacie
python3 email_payment_checker.py --dry-run
```

## Detekovane typy emailov

Script rozpoznava platobne emaily na zaklade:
- **Klucovych slov** (platba, faktura, invoice, receipt, subscription, ...)
- **Znamych odosielatelov** (PayPal, Stripe, Apple, Google, Netflix, Spotify, ...)
- **Penaznych sum** v tele emailu (9.99€, $19.99, 100 CZK, ...)

Jazyky: slovencina, cestina, anglictina.
