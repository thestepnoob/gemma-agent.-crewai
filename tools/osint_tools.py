"""
OSINT-Toolkit – Open Source Intelligence Funktionen
Alle Funktionen nutzen ausschließlich öffentlich zugängliche Daten.
Keine API-Keys erforderlich.
"""

import os
import re
import ssl
import json
import time
import socket
import hashlib
import datetime
import random
import requests
from concurrent.futures import ThreadPoolExecutor, as_completed
from typing import Optional

# ============================================================
# Hilfsfunktionen
# ============================================================

# Verschiedene User-Agents um Blocking zu vermeiden
_USER_AGENTS = [
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/125.0.0.0 Safari/537.36",
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/17.5 Safari/605.1.15",
    "Mozilla/5.0 (X11; Linux x86_64; rv:128.0) Gecko/20100101 Firefox/128.0",
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36 Edg/124.0.0.0",
]

def _get_headers():
    """Gibt zufällige HTTP-Headers zurück."""
    return {
        "User-Agent": random.choice(_USER_AGENTS),
        "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
        "Accept-Language": "de-DE,de;q=0.9,en-US;q=0.8,en;q=0.7",
    }

def _safe_request(url, timeout=8, **kwargs):
    """Sichere HTTP-Anfrage mit Fehlerbehandlung und SSL-Warnung-Unterdrückung."""
    import urllib3
    urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)
    try:
        resp = requests.get(
            url, headers=_get_headers(), timeout=timeout,
            verify=False, allow_redirects=True, **kwargs
        )
        return resp
    except Exception:
        return None


# ============================================================
# PERSONEN-OSINT
# ============================================================

def _check_single_platform(args):
    """Prüft ob ein Benutzername auf einer einzelnen Plattform existiert.
    Wird parallel in einem ThreadPool ausgeführt.
    """
    platform_name, url = args
    try:
        resp = _safe_request(url, timeout=6)
        if resp is None:
            return (platform_name, url, "error")

        if resp.status_code == 404:
            return (platform_name, url, "not_found")
        elif resp.status_code == 200:
            # Einige Plattformen geben 200 zurück auch wenn der User nicht existiert
            body_lower = resp.text[:5000].lower()
            not_found_indicators = [
                "page not found", "user not found", "this page doesn't exist",
                "sorry, nobody on reddit goes by that name",
                "this account doesn't exist", "couldn't find",
                "no user found", "the page you were looking for doesn't exist",
                "hmm...this page doesn't exist",
                "diese seite ist leider nicht verfügbar",
                "nothing here", "404", "user does not exist",
            ]
            if any(ind in body_lower for ind in not_found_indicators):
                return (platform_name, url, "not_found")
            return (platform_name, url, "found")
        elif resp.status_code in (301, 302):
            return (platform_name, url, "found")
        elif resp.status_code == 429:
            return (platform_name, url, "rate_limited")
        else:
            return (platform_name, url, "not_found")
    except Exception:
        return (platform_name, url, "error")


def username_search(username: str) -> str:
    """Sucht einen Benutzernamen parallel auf 30+ Plattformen."""
    # Plattform-URLs mit dem Benutzernamen
    platforms = {
        "GitHub": f"https://github.com/{username}",
        "Reddit": f"https://www.reddit.com/user/{username}",
        "Twitter/X": f"https://x.com/{username}",
        "Instagram": f"https://www.instagram.com/{username}/",
        "TikTok": f"https://www.tiktok.com/@{username}",
        "YouTube": f"https://www.youtube.com/@{username}",
        "Twitch": f"https://www.twitch.tv/{username}",
        "Steam": f"https://steamcommunity.com/id/{username}",
        "Pinterest": f"https://www.pinterest.com/{username}/",
        "Tumblr": f"https://{username}.tumblr.com",
        "Medium": f"https://medium.com/@{username}",
        "DeviantArt": f"https://www.deviantart.com/{username}",
        "Flickr": f"https://www.flickr.com/people/{username}",
        "SoundCloud": f"https://soundcloud.com/{username}",
        "Spotify": f"https://open.spotify.com/user/{username}",
        "LinkedIn": f"https://www.linkedin.com/in/{username}",
        "GitLab": f"https://gitlab.com/{username}",
        "Bitbucket": f"https://bitbucket.org/{username}/",
        "Docker Hub": f"https://hub.docker.com/u/{username}",
        "npm": f"https://www.npmjs.com/~{username}",
        "PyPI": f"https://pypi.org/user/{username}/",
        "HackerNews": f"https://news.ycombinator.com/user?id={username}",
        "Keybase": f"https://keybase.io/{username}",
        "About.me": f"https://about.me/{username}",
        "Gravatar": f"https://en.gravatar.com/{username}",
        "Replit": f"https://replit.com/@{username}",
        "Patreon": f"https://www.patreon.com/{username}",
        "Chess.com": f"https://www.chess.com/member/{username}",
        "Lichess": f"https://lichess.org/@/{username}",
        "Telegram": f"https://t.me/{username}",
        "VK": f"https://vk.com/{username}",
        "Mastodon (social)": f"https://mastodon.social/@{username}",
        "Letterboxd": f"https://letterboxd.com/{username}",
        "Linktree": f"https://linktr.ee/{username}",
    }

    found = []
    not_found_count = 0
    errors = []
    rate_limited = []

    # Parallele Abfragen mit ThreadPool (max 10 gleichzeitig)
    with ThreadPoolExecutor(max_workers=10) as executor:
        futures = {
            executor.submit(_check_single_platform, (name, url)): name
            for name, url in platforms.items()
        }
        for future in as_completed(futures):
            try:
                platform, url, status = future.result(timeout=12)
                if status == "found":
                    found.append(f"✅ **{platform}:** {url}")
                elif status == "not_found":
                    not_found_count += 1
                elif status == "rate_limited":
                    rate_limited.append(platform)
                else:
                    errors.append(platform)
            except Exception:
                errors.append(futures[future])

    # Report zusammenbauen
    report = [f"🔍 **OSINT Benutzername-Suche: `{username}`**"]
    report.append(f"📊 {len(platforms)} Plattformen geprüft\n")

    if found:
        report.append(f"**✅ Gefunden auf {len(found)} Plattformen:**")
        # Sortiert ausgeben
        for entry in sorted(found):
            report.append(entry)
    else:
        report.append("Keine Profile gefunden.")

    report.append(f"\n❌ Nicht gefunden: {not_found_count} Plattformen")
    if rate_limited:
        report.append(f"⏱️ Rate-Limited: {', '.join(rate_limited)}")
    if errors:
        report.append(f"⚠️ Fehler/Timeout: {', '.join(errors)}")

    return "\n".join(report)


def email_recon(email: str) -> str:
    """Analysiert eine E-Mail-Adresse umfassend."""
    report = [f"📧 **OSINT E-Mail-Analyse: `{email}`**\n"]

    # Format-Validierung
    email_regex = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
    if not re.match(email_regex, email):
        report.append("❌ **Format:** Ungültiges E-Mail-Format")
        return "\n".join(report)
    report.append("✅ **Format:** Gültig")

    # Domain extrahieren
    domain = email.split("@")[1]
    report.append(f"🌐 **Domain:** {domain}")

    # Bekannte Provider erkennen (ohne DNS)
    known_providers = {
        "gmail.com": "Google Gmail",
        "googlemail.com": "Google Gmail",
        "outlook.com": "Microsoft Outlook",
        "hotmail.com": "Microsoft Hotmail",
        "live.com": "Microsoft Live",
        "yahoo.com": "Yahoo Mail",
        "protonmail.com": "ProtonMail",
        "proton.me": "Proton Mail",
        "icloud.com": "Apple iCloud",
        "me.com": "Apple iCloud",
        "aol.com": "AOL Mail",
        "zoho.com": "Zoho Mail",
        "gmx.de": "GMX",
        "gmx.net": "GMX",
        "web.de": "WEB.DE",
        "t-online.de": "T-Online (Telekom)",
        "freenet.de": "freenet",
        "posteo.de": "Posteo",
        "mailbox.org": "Mailbox.org",
        "tutanota.com": "Tutanota",
        "tuta.io": "Tuta",
    }
    provider = known_providers.get(domain.lower())
    if provider:
        report.append(f"📌 **Bekannter Provider:** {provider}")

    # MX Records prüfen
    try:
        import dns.resolver
        mx_records = dns.resolver.resolve(domain, 'MX')
        mx_list = sorted([(r.preference, str(r.exchange).rstrip('.')) for r in mx_records])
        report.append("\n📬 **MX-Records (Mailserver):**")
        for pref, mx in mx_list:
            report.append(f"  - Priorität {pref}: `{mx}`")

        # Provider aus MX erkennen falls nicht schon bekannt
        if not provider:
            mx_str = " ".join([mx for _, mx in mx_list]).lower()
            if "google" in mx_str or "gmail" in mx_str:
                report.append("📌 **E-Mail-Provider (via MX):** Google Workspace")
            elif "outlook" in mx_str or "microsoft" in mx_str:
                report.append("📌 **E-Mail-Provider (via MX):** Microsoft 365")
            elif "protonmail" in mx_str or "proton" in mx_str:
                report.append("📌 **E-Mail-Provider (via MX):** ProtonMail")
            elif "zoho" in mx_str:
                report.append("📌 **E-Mail-Provider (via MX):** Zoho Mail")
    except Exception as e:
        report.append(f"⚠️ MX-Lookup fehlgeschlagen: {str(e)}")

    # Gravatar Check (MD5-Hash der E-Mail)
    try:
        email_hash = hashlib.md5(email.lower().strip().encode()).hexdigest()
        gravatar_url = f"https://www.gravatar.com/avatar/{email_hash}?d=404"
        resp = _safe_request(gravatar_url, timeout=5)
        if resp and resp.status_code == 200:
            report.append(f"\n🖼️ **Gravatar:** Profil gefunden → https://gravatar.com/{email_hash}")
        else:
            report.append("\n🖼️ **Gravatar:** Kein Profil")
    except Exception:
        pass

    # Domain-WHOIS
    try:
        import whois
        w = whois.whois(domain)
        if w.creation_date:
            cd = w.creation_date
            if isinstance(cd, list):
                cd = cd[0]
            report.append(f"\n📅 **Domain registriert seit:** {cd.strftime('%d.%m.%Y')}")
            report.append(f"📋 **Registrar:** {w.registrar or 'Unbekannt'}")
    except Exception:
        pass

    # Hinweis auf Breach-Check
    report.append("\n💡 **Tipp:** Für Breach-Checks kannst du manuell https://haveibeenpwned.com nutzen.")

    return "\n".join(report)


def phone_lookup(phone: str) -> str:
    """Analysiert eine Telefonnummer umfassend."""
    import phonenumbers
    from phonenumbers import geocoder, carrier, timezone

    report = [f"📱 **OSINT Telefonnummer-Analyse: `{phone}`**\n"]

    try:
        # Parsen – ohne Prefix als deutsche Nummer interpretieren
        if not phone.startswith("+"):
            parsed = phonenumbers.parse(phone, "DE")
        else:
            parsed = phonenumbers.parse(phone)

        # Validierung
        is_valid = phonenumbers.is_valid_number(parsed)
        report.append(f"{'✅' if is_valid else '❌'} **Gültig:** {'Ja' if is_valid else 'Nein'}")

        # Formatierte Nummern
        report.append(f"🔢 **International:** `{phonenumbers.format_number(parsed, phonenumbers.PhoneNumberFormat.INTERNATIONAL)}`")
        report.append(f"🔢 **E.164:** `{phonenumbers.format_number(parsed, phonenumbers.PhoneNumberFormat.E164)}`")
        report.append(f"🔢 **National:** `{phonenumbers.format_number(parsed, phonenumbers.PhoneNumberFormat.NATIONAL)}`")

        # Ländercode
        report.append(f"🌍 **Ländercode:** +{parsed.country_code}")

        # Geolokation / Region
        location = geocoder.description_for_number(parsed, "de")
        if location:
            report.append(f"📍 **Region:** {location}")

        # Carrier / Anbieter
        carrier_name = carrier.name_for_number(parsed, "de")
        if carrier_name:
            report.append(f"📡 **Carrier/Anbieter:** {carrier_name}")

        # Nummerntyp
        num_type = phonenumbers.number_type(parsed)
        type_map = {
            phonenumbers.PhoneNumberType.MOBILE: "📱 Mobilfunk",
            phonenumbers.PhoneNumberType.FIXED_LINE: "☎️ Festnetz",
            phonenumbers.PhoneNumberType.FIXED_LINE_OR_MOBILE: "📞 Festnetz oder Mobil",
            phonenumbers.PhoneNumberType.VOIP: "🌐 VoIP",
            phonenumbers.PhoneNumberType.TOLL_FREE: "🆓 Gebührenfrei",
            phonenumbers.PhoneNumberType.PREMIUM_RATE: "💰 Mehrwertnummer",
            phonenumbers.PhoneNumberType.PERSONAL_NUMBER: "👤 Persönliche Nummer",
            phonenumbers.PhoneNumberType.PAGER: "📟 Pager",
            phonenumbers.PhoneNumberType.SHARED_COST: "💸 Shared Cost",
        }
        type_str = type_map.get(num_type, "❓ Unbekannt")
        report.append(f"📋 **Nummerntyp:** {type_str}")

        # Zeitzonen
        tz_list = timezone.time_zones_for_number(parsed)
        if tz_list:
            report.append(f"🕐 **Zeitzonen:** {', '.join(tz_list)}")

        # Mögliches Land
        region_code = phonenumbers.region_code_for_number(parsed)
        if region_code:
            report.append(f"🏳️ **Regionscode (ISO):** {region_code}")

    except phonenumbers.NumberParseException as e:
        report.append(f"❌ Konnte die Nummer nicht parsen: {str(e)}")
        report.append("💡 **Tipp:** Gib die Nummer im internationalen Format an, z.B. `+49 171 1234567`")
    except Exception as e:
        report.append(f"⚠️ Fehler: {str(e)}")

    return "\n".join(report)


# ============================================================
# INFRASTRUKTUR-OSINT
# ============================================================

def domain_recon(domain: str) -> str:
    """Vollständige Domain-Aufklärung: WHOIS, DNS, HTTP-Header, Security."""
    import dns.resolver

    # Domain bereinigen
    domain = domain.replace("https://", "").replace("http://", "").split("/")[0].strip()

    report = [f"🌐 **OSINT Domain-Aufklärung: `{domain}`**\n"]

    # === WHOIS ===
    try:
        import whois
        w = whois.whois(domain)
        report.append("📋 **WHOIS-Informationen:**")
        if w.registrar:
            report.append(f"  - Registrar: {w.registrar}")
        if w.creation_date:
            cd = w.creation_date
            if isinstance(cd, list):
                cd = cd[0]
            report.append(f"  - Registriert: {cd.strftime('%d.%m.%Y')}")
        if w.expiration_date:
            ed = w.expiration_date
            if isinstance(ed, list):
                ed = ed[0]
            report.append(f"  - Ablaufdatum: {ed.strftime('%d.%m.%Y')}")
            # Ablauf-Warnung
            days_left = (ed - datetime.datetime.now()).days
            if days_left < 0:
                report.append(f"  ❌ **DOMAIN ABGELAUFEN** seit {abs(days_left)} Tagen!")
            elif days_left < 30:
                report.append(f"  ⚠️ Läuft in {days_left} Tagen ab!")
        if w.name_servers:
            ns = w.name_servers if isinstance(w.name_servers, list) else [w.name_servers]
            ns_unique = sorted(set(n.lower() for n in ns if n))
            report.append(f"  - Nameserver: {', '.join(ns_unique)}")
        if w.org:
            report.append(f"  - Organisation: {w.org}")
        if w.country:
            report.append(f"  - Land: {w.country}")
        if w.emails:
            emails = w.emails if isinstance(w.emails, list) else [w.emails]
            report.append(f"  - Kontakt-E-Mails: {', '.join(emails)}")
    except Exception as e:
        report.append(f"⚠️ WHOIS fehlgeschlagen: {str(e)}")

    # === DNS Records ===
    report.append("\n📡 **DNS-Records:**")
    record_types = ['A', 'AAAA', 'MX', 'NS', 'TXT', 'SOA', 'CNAME']
    for rtype in record_types:
        try:
            answers = dns.resolver.resolve(domain, rtype)
            records = [str(rdata).rstrip('.') for rdata in answers]
            if records:
                # TXT Records können lang sein – kürzen
                if rtype == 'TXT':
                    display = [r[:100] + ('...' if len(r) > 100 else '') for r in records[:3]]
                else:
                    display = records[:5]
                report.append(f"  **{rtype}:** {', '.join(display)}")
        except (dns.resolver.NoAnswer, dns.resolver.NXDOMAIN, dns.resolver.NoNameservers):
            pass
        except Exception:
            pass

    # === HTTP-Header-Analyse ===
    report.append("\n🔒 **HTTP-Header & Security:**")
    for protocol in ["https", "http"]:
        try:
            resp = _safe_request(f"{protocol}://{domain}", timeout=10)
            if resp:
                report.append(f"  **Protokoll:** {protocol.upper()} (Status {resp.status_code})")

                # Server-Info
                server = resp.headers.get('Server')
                if server:
                    report.append(f"  🖥️ Server: `{server}`")
                powered = resp.headers.get('X-Powered-By')
                if powered:
                    report.append(f"  ⚙️ X-Powered-By: `{powered}`")

                # Security Headers prüfen
                sec_headers = {
                    'Strict-Transport-Security': 'HSTS',
                    'Content-Security-Policy': 'CSP',
                    'X-Frame-Options': 'X-Frame-Options',
                    'X-Content-Type-Options': 'X-Content-Type-Options',
                    'X-XSS-Protection': 'XSS-Protection',
                    'Referrer-Policy': 'Referrer-Policy',
                    'Permissions-Policy': 'Permissions-Policy',
                }
                present = 0
                for header, name in sec_headers.items():
                    val = resp.headers.get(header)
                    if val:
                        report.append(f"  ✅ {name}")
                        present += 1
                    else:
                        report.append(f"  ❌ {name}")

                score = int((present / len(sec_headers)) * 100)
                report.append(f"\n  📊 **Security-Header-Score:** {score}% ({present}/{len(sec_headers)})")
                break
        except Exception:
            continue

    return "\n".join(report)


def ip_lookup(ip: str) -> str:
    """Analysiert eine IP-Adresse: Geolokation, ISP, ASN, Reverse DNS."""
    report = [f"🔍 **OSINT IP-Analyse: `{ip}`**\n"]

    # IP-Validierung
    is_valid_ip = False
    try:
        socket.inet_aton(ip)
        is_valid_ip = True
        report.append("📋 **Typ:** IPv4")
    except socket.error:
        try:
            socket.inet_pton(socket.AF_INET6, ip)
            is_valid_ip = True
            report.append("📋 **Typ:** IPv6")
        except socket.error:
            pass

    if not is_valid_ip:
        report.append("❌ Ungültige IP-Adresse")
        return "\n".join(report)

    # Private IP Check
    private_ranges = [
        (r"^10\.", "Klasse A privat"),
        (r"^172\.(1[6-9]|2[0-9]|3[01])\.", "Klasse B privat"),
        (r"^192\.168\.", "Klasse C privat"),
        (r"^127\.", "Loopback"),
        (r"^0\.", "Dieses Netzwerk"),
    ]
    for pattern, desc in private_ranges:
        if re.match(pattern, ip):
            report.append(f"🏠 **Private IP-Adresse** ({desc})")
            report.append("ℹ️ Geolokation nicht verfügbar für private IPs.")
            return "\n".join(report)

    # Geolokation via ip-api.com (kostenlos, kein API-Key nötig)
    try:
        resp = _safe_request(
            f"http://ip-api.com/json/{ip}?fields=status,message,country,countryCode,region,regionName,city,zip,lat,lon,timezone,isp,org,as,asname,reverse,mobile,proxy,hosting,query",
            timeout=10
        )
        if resp and resp.status_code == 200:
            data = resp.json()
            if data.get("status") == "success":
                report.append("📍 **Geolokation:**")
                report.append(f"  - Land: {data.get('country', '?')} ({data.get('countryCode', '?')})")
                report.append(f"  - Region: {data.get('regionName', '?')}")
                report.append(f"  - Stadt: {data.get('city', '?')}")
                report.append(f"  - PLZ: {data.get('zip', '?')}")
                lat, lon = data.get('lat', '?'), data.get('lon', '?')
                report.append(f"  - Koordinaten: {lat}, {lon}")
                if lat != '?' and lon != '?':
                    report.append(f"  - 🗺️ Karte: https://www.google.com/maps?q={lat},{lon}")
                report.append(f"  - Zeitzone: {data.get('timezone', '?')}")

                report.append("\n🏢 **Netzwerk-Info:**")
                report.append(f"  - ISP: {data.get('isp', '?')}")
                report.append(f"  - Organisation: {data.get('org', '?')}")
                report.append(f"  - ASN: `{data.get('as', '?')}`")
                report.append(f"  - AS Name: {data.get('asname', '?')}")

                report.append("\n🔧 **Eigenschaften:**")
                report.append(f"  - Reverse DNS: `{data.get('reverse', 'Kein Eintrag') or 'Kein Eintrag'}`")
                report.append(f"  - Mobilfunk: {'📱 Ja' if data.get('mobile') else 'Nein'}")
                report.append(f"  - Proxy/VPN: {'⚠️ Ja' if data.get('proxy') else '✅ Nein'}")
                report.append(f"  - Hosting/Datacenter: {'🖥️ Ja' if data.get('hosting') else 'Nein'}")
            else:
                report.append(f"⚠️ ip-api Fehler: {data.get('message', 'Unbekannt')}")
    except Exception as e:
        report.append(f"⚠️ Geolokation fehlgeschlagen: {str(e)}")

    # Eigener Reverse DNS Lookup
    try:
        hostname = socket.gethostbyaddr(ip)
        report.append(f"\n🔄 **Reverse DNS (System):** `{hostname[0]}`")
        if hostname[1]:
            report.append(f"  - Aliase: {', '.join(hostname[1])}")
    except socket.herror:
        pass
    except Exception:
        pass

    return "\n".join(report)


def ssl_analysis(domain: str) -> str:
    """Analysiert das SSL/TLS-Zertifikat einer Domain im Detail."""
    domain = domain.replace("https://", "").replace("http://", "").split("/")[0].strip()

    report = [f"🔒 **OSINT SSL/TLS-Analyse: `{domain}`**\n"]

    try:
        context = ssl.create_default_context()
        conn = context.wrap_socket(socket.socket(socket.AF_INET), server_hostname=domain)
        conn.settimeout(10)
        conn.connect((domain, 443))

        cert = conn.getpeercert()
        cert_bin = conn.getpeercert(binary_form=True)
        cipher = conn.cipher()
        version = conn.version()

        conn.close()

        # Verbindungsinfos
        report.append(f"🔐 **TLS-Version:** {version}")
        if cipher:
            report.append(f"🔑 **Cipher Suite:** `{cipher[0]}`")
            report.append(f"📏 **Schlüssellänge:** {cipher[2]} Bit")

        # Subject
        subject = dict(x[0] for x in cert.get('subject', []))
        report.append(f"\n📜 **Zertifikat-Subject:**")
        if subject.get('commonName'):
            report.append(f"  - Common Name: `{subject['commonName']}`")
        if subject.get('organizationName'):
            report.append(f"  - Organisation: {subject['organizationName']}")
        if subject.get('countryName'):
            report.append(f"  - Land: {subject['countryName']}")

        # Issuer (Aussteller)
        issuer = dict(x[0] for x in cert.get('issuer', []))
        report.append(f"\n🏛️ **Aussteller (CA):**")
        report.append(f"  - Organisation: {issuer.get('organizationName', '?')}")
        report.append(f"  - Common Name: {issuer.get('commonName', '?')}")

        # Zertifikatstyp erkennen
        org = issuer.get('organizationName', '').lower()
        if "let's encrypt" in org:
            report.append("  📌 Typ: **Let's Encrypt** (kostenlos, DV)")
        elif "digicert" in org:
            report.append("  📌 Typ: **DigiCert** (kommerziell)")
        elif "comodo" in org or "sectigo" in org:
            report.append("  📌 Typ: **Sectigo/Comodo** (kommerziell)")
        elif "globalsign" in org:
            report.append("  📌 Typ: **GlobalSign** (kommerziell)")

        # Gültigkeit
        not_before = cert.get('notBefore', '?')
        not_after = cert.get('notAfter', '?')
        report.append(f"\n📅 **Gültigkeit:**")
        report.append(f"  - Von: {not_before}")
        report.append(f"  - Bis: {not_after}")

        try:
            expiry = datetime.datetime.strptime(not_after, "%b %d %H:%M:%S %Y %Z")
            days_left = (expiry - datetime.datetime.utcnow()).days
            if days_left < 0:
                report.append(f"  ❌ **ABGELAUFEN** seit {abs(days_left)} Tagen!")
            elif days_left < 30:
                report.append(f"  ⚠️ Läuft in **{days_left} Tagen** ab!")
            elif days_left < 90:
                report.append(f"  🟡 Noch {days_left} Tage gültig")
            else:
                report.append(f"  ✅ Noch **{days_left} Tage** gültig")
        except Exception:
            pass

        # Subject Alternative Names (SANs)
        san_list = [v for _, v in cert.get('subjectAltName', [])]
        if san_list:
            report.append(f"\n🌐 **Alternative Namen (SAN):** {len(san_list)} Einträge")
            for san in san_list[:15]:
                report.append(f"  - `{san}`")
            if len(san_list) > 15:
                report.append(f"  ... und {len(san_list) - 15} weitere")

        # SHA-256 Fingerprint
        cert_hash = hashlib.sha256(cert_bin).hexdigest()
        report.append(f"\n🔏 **SHA-256 Fingerprint:**")
        # Formatiert mit Doppelpunkten
        formatted = ':'.join(cert_hash[i:i+2].upper() for i in range(0, len(cert_hash), 2))
        report.append(f"  `{formatted}`")

    except ssl.SSLError as e:
        report.append(f"❌ **SSL-Fehler:** {str(e)}")
    except socket.timeout:
        report.append("❌ Timeout beim Verbindungsaufbau (Port 443)")
    except ConnectionRefusedError:
        report.append("❌ Verbindung verweigert – Port 443 nicht erreichbar")
    except socket.gaierror:
        report.append("❌ Domain konnte nicht aufgelöst werden")
    except Exception as e:
        report.append(f"⚠️ Fehler: {str(e)}")

    return "\n".join(report)


def subdomain_enum(domain: str) -> str:
    """Findet Subdomains via Certificate Transparency Logs und DNS-Bruteforce."""
    import dns.resolver

    domain = domain.replace("https://", "").replace("http://", "").split("/")[0].strip()
    report = [f"🗺️ **OSINT Subdomain-Enumeration: `{domain}`**\n"]

    subdomains = set()

    # Methode 1: crt.sh (Certificate Transparency Logs)
    report.append("📜 **Quelle 1: Certificate Transparency (crt.sh)**")
    try:
        resp = _safe_request(f"https://crt.sh/?q=%.{domain}&output=json", timeout=20)
        if resp and resp.status_code == 200:
            crt_data = resp.json()
            for entry in crt_data:
                name = entry.get("name_value", "")
                for sub in name.split("\n"):
                    sub = sub.strip().lower().rstrip(".")
                    # Wildcards und ungültige Einträge filtern
                    if sub.startswith("*"):
                        continue
                    if sub.endswith(f".{domain}") or sub == domain:
                        subdomains.add(sub)
            report.append(f"  ✅ {len(subdomains)} einzigartige Subdomains gefunden")
        else:
            report.append("  ⚠️ crt.sh nicht erreichbar oder keine Daten")
    except json.JSONDecodeError:
        report.append("  ⚠️ crt.sh hat ungültige Daten zurückgegeben")
    except Exception as e:
        report.append(f"  ⚠️ Fehler: {str(e)}")

    # Methode 2: DNS Bruteforce mit gängigen Prefixen
    common_prefixes = [
        "www", "mail", "ftp", "smtp", "pop", "pop3", "imap", "webmail",
        "admin", "blog", "dev", "staging", "test", "api", "app",
        "cdn", "static", "media", "img", "images", "assets",
        "ns1", "ns2", "ns3", "dns", "dns1", "dns2",
        "mx", "mx1", "mx2", "vpn", "remote", "rdp",
        "shop", "store", "portal", "login", "auth", "sso", "id",
        "docs", "doc", "wiki", "help", "support", "status", "monitor",
        "git", "gitlab", "jenkins", "ci", "cd", "build",
        "db", "database", "mysql", "postgres", "redis", "mongo",
        "cloud", "aws", "azure", "gcp", "s3", "storage",
        "beta", "alpha", "preview", "demo", "sandbox",
        "m", "mobile", "wap",
        "autodiscover", "autoconfig",
        "cpanel", "whm", "webhost",
        "grafana", "kibana", "prometheus",
    ]

    report.append("\n🔨 **Quelle 2: DNS-Bruteforce (80+ Prefixe)**")
    dns_found = 0

    def _check_subdomain(prefix):
        """Prüft ob eine Subdomain per DNS auflösbar ist."""
        sub = f"{prefix}.{domain}"
        try:
            dns.resolver.resolve(sub, 'A')
            return sub
        except Exception:
            return None

    # Parallel prüfen
    with ThreadPoolExecutor(max_workers=15) as executor:
        futures = {executor.submit(_check_subdomain, p): p for p in common_prefixes}
        for future in as_completed(futures):
            result = future.result()
            if result:
                subdomains.add(result)
                dns_found += 1

    report.append(f"  ✅ {dns_found} zusätzlich per DNS bestätigt")

    # Ergebnisse mit IP-Auflösung
    report.append(f"\n📊 **Gesamt: {len(subdomains)} Subdomains gefunden:**")
    if subdomains:
        for sub in sorted(subdomains):
            try:
                ips = [str(r) for r in dns.resolver.resolve(sub, 'A')]
                report.append(f"  - `{sub}` → {', '.join(ips)}")
            except Exception:
                report.append(f"  - `{sub}` → (A-Record nicht auflösbar)")
    else:
        report.append("  Keine Subdomains gefunden.")

    return "\n".join(report)


def tech_stack(domain: str) -> str:
    """Erkennt den Technologie-Stack einer Website."""
    from bs4 import BeautifulSoup

    domain = domain.replace("https://", "").replace("http://", "").split("/")[0].strip()
    report = [f"⚙️ **OSINT Tech-Stack-Analyse: `{domain}`**\n"]

    resp = None
    for protocol in ["https", "http"]:
        resp = _safe_request(f"{protocol}://{domain}", timeout=12)
        if resp and resp.status_code == 200:
            break

    if not resp or resp.status_code != 200:
        report.append("❌ Website nicht erreichbar")
        return "\n".join(report)

    soup = BeautifulSoup(resp.text, 'html.parser')
    html_text = resp.text

    # === Server & Infrastruktur ===
    report.append("🖥️ **Server & Infrastruktur:**")
    server = resp.headers.get('Server', '')
    if server:
        report.append(f"  - Server: `{server}`")
    powered_by = resp.headers.get('X-Powered-By', '')
    if powered_by:
        report.append(f"  - X-Powered-By: `{powered_by}`")
    via = resp.headers.get('Via', '')
    if via:
        report.append(f"  - Via: `{via}`")

    # === CDN / Hosting ===
    cdn_list = []
    headers_str = str(resp.headers).lower()
    cdn_checks = {
        "Cloudflare": lambda: 'cf-ray' in resp.headers or 'cloudflare' in headers_str,
        "AWS CloudFront": lambda: 'cloudfront' in headers_str or 'x-amz' in headers_str,
        "Akamai": lambda: 'akamai' in headers_str,
        "Fastly": lambda: 'fastly' in headers_str or 'x-served-by' in resp.headers,
        "Vercel": lambda: 'x-vercel' in headers_str or 'vercel' in headers_str,
        "Netlify": lambda: 'netlify' in headers_str,
        "GitHub Pages": lambda: 'github' in headers_str,
        "Heroku": lambda: 'heroku' in headers_str,
        "Google Cloud": lambda: 'gws' in server.lower() or 'google' in headers_str,
    }
    for name, check in cdn_checks.items():
        try:
            if check():
                cdn_list.append(name)
        except Exception:
            pass
    if cdn_list:
        report.append(f"\n🌍 **CDN / Hosting:** {', '.join(cdn_list)}")

    # === CMS ===
    cms_detected = []
    cms_checks = {
        "WordPress": lambda: 'wp-content' in html_text or 'wp-includes' in html_text,
        "Joomla": lambda: '/media/jui/' in html_text or bool(soup.find('meta', attrs={'name': 'generator', 'content': re.compile(r'Joomla', re.I)})),
        "Drupal": lambda: 'drupal.js' in html_text or 'Drupal.settings' in html_text,
        "Shopify": lambda: 'cdn.shopify.com' in html_text or 'Shopify.theme' in html_text,
        "Wix": lambda: 'wix.com' in html_text or 'X-Wix' in str(resp.headers),
        "Squarespace": lambda: 'squarespace.com' in html_text,
        "Ghost": lambda: bool(soup.find('meta', attrs={'name': 'generator', 'content': re.compile(r'Ghost', re.I)})),
        "Magento": lambda: 'mage/' in html_text.lower() or 'magento' in html_text.lower(),
        "PrestaShop": lambda: 'prestashop' in html_text.lower(),
        "Typo3": lambda: 'typo3' in html_text.lower(),
        "Hugo": lambda: bool(soup.find('meta', attrs={'name': 'generator', 'content': re.compile(r'Hugo', re.I)})),
    }
    for name, check in cms_checks.items():
        try:
            if check():
                cms_detected.append(name)
        except Exception:
            pass
    if cms_detected:
        report.append(f"\n📦 **CMS:** {', '.join(cms_detected)}")

    # === Frontend-Frameworks ===
    frameworks = []
    html_lower = html_text.lower()
    fw_checks = {
        "React": ["__react", "reactdom", "__next_data__", "_next/static", "react.production"],
        "Vue.js": ["vue.js", "vue.min.js", "__vue__", "vue-router", "vuex"],
        "Angular": ["ng-version", "ng-app", "angular.min.js", "angular.js"],
        "Svelte": ["__svelte", "svelte"],
        "Next.js": ["_next/static", "__next_data__", "next/dist"],
        "Nuxt.js": ["__nuxt", "_nuxt/"],
        "Gatsby": ["gatsby"],
        "jQuery": ["jquery.min.js", "jquery.js", "jquery-"],
        "Bootstrap": ["bootstrap.min.css", "bootstrap.css", "bootstrap.bundle"],
        "Tailwind CSS": ["tailwindcss", "tailwind.min.css"],
        "Foundation": ["foundation.min.css", "foundation.css"],
        "Bulma": ["bulma.min.css", "bulma.css", "bulma/"],
        "Alpine.js": ["x-data", "alpine.js", "alpinejs"],
        "HTMX": ["htmx.org", "hx-get", "hx-post"],
    }
    for name, patterns in fw_checks.items():
        for pattern in patterns:
            if pattern in html_lower:
                frameworks.append(name)
                break
    if frameworks:
        report.append(f"\n💻 **Frontend:** {', '.join(frameworks)}")

    # === Analytics & Tracking ===
    analytics = []
    analytics_checks = {
        "Google Analytics": ["google-analytics.com", "gtag(", "ga.js", "analytics.js"],
        "Google Tag Manager": ["googletagmanager.com", "gtm.js"],
        "Facebook Pixel": ["facebook.com/tr", "fbq(", "connect.facebook.net"],
        "Hotjar": ["hotjar.com", "hj("],
        "Plausible": ["plausible.io"],
        "Matomo": ["matomo", "piwik"],
        "Clarity (Microsoft)": ["clarity.ms"],
        "Segment": ["segment.com", "analytics.js"],
        "Mixpanel": ["mixpanel.com", "mixpanel.init"],
    }
    for name, patterns in analytics_checks.items():
        for pattern in patterns:
            if pattern in html_lower:
                analytics.append(name)
                break
    if analytics:
        report.append(f"\n📊 **Analytics & Tracking:** {', '.join(analytics)}")

    # === Security Headers Score ===
    sec_headers = [
        'Strict-Transport-Security', 'Content-Security-Policy',
        'X-Frame-Options', 'X-Content-Type-Options',
        'Referrer-Policy', 'Permissions-Policy',
    ]
    present = sum(1 for h in sec_headers if resp.headers.get(h))
    score = int((present / len(sec_headers)) * 100)
    report.append(f"\n🛡️ **Security-Header-Score:** {score}% ({present}/{len(sec_headers)})")

    # === Meta-Generator ===
    gen = soup.find('meta', attrs={'name': 'generator'})
    if gen and gen.get('content'):
        report.append(f"\n🏷️ **Generator-Tag:** `{gen['content']}`")

    return "\n".join(report)
