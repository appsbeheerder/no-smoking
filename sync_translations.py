#!/usr/bin/env python3
"""
sync_translations.py

Lokale tool: propageert tekstwijzigingen in de NL-taal (in index.html en
schema_verdamper_bong_nl.svg) naar de overige talen die al in het bestand
staan, via de DeepL API.

Gebruik:
    python sync_translations.py

Werkwijze:
    1. Pas de Nederlandse tekst aan in index.html (translations.nl) en/of
       schema_verdamper_bong_nl.svg, zoals je altijd al deed.
    2. Draai dit script.
    3. Het script vergelijkt de huidige NL-tekst met de vorige keer dat
       het script draaide (state in .sync_state/), vertaalt alleen wat
       gewijzigd of nieuw is, en toont een overzicht.
    4. Je moet dit overzicht expliciet bevestigen (y) voordat er iets
       wordt weggeschreven. Voor het schrijven wordt altijd eerst een
       timestamped backup gemaakt van elk bestand dat wijzigt.

Buiten scope: het toevoegen van een compleet nieuwe taal (nieuw blok,
nieuwe <option>, nieuw SVG-bestand) doet dit script niet — dat blijft
een keer handmatig (of via Claude Code) werk.

Vereist: een DeepL API key, via omgevingsvariabele DEEPL_API_KEY of in
een lokaal bestand deepl_api_key.txt (beide NIET commiten; staan al in
.gitignore).
"""

import json
import os
import re
import shutil
import sys
import urllib.error
import urllib.parse
import urllib.request
from datetime import datetime

ROOT = os.path.dirname(os.path.abspath(__file__))
INDEX_HTML = os.path.join(ROOT, "index.html")
STATE_DIR = os.path.join(ROOT, ".sync_state")
BACKUP_DIR = os.path.join(ROOT, "backups")
NL_SNAPSHOT_JSON = os.path.join(STATE_DIR, "nl_html_snapshot.json")
NL_SVG_SNAPSHOT = os.path.join(STATE_DIR, "nl_svg_snapshot.txt")

SOURCE_LANG = "nl"

# Onze taalcode -> DeepL doeltaalcode. Alleen talen die al als blok in
# index.html staan worden daadwerkelijk gebruikt.
DEEPL_TARGET = {
    "en": "EN-GB",
    "de": "DE",
    "fr": "FR",
    "es": "ES",
    "it": "IT",
    "pl": "PL",
    "pt": "PT-PT",
    "bg": "BG",
    "hr": "HR",
    "cs": "CS",
    "da": "DA",
    "et": "ET",
    "fi": "FI",
    "el": "EL",
    "hu": "HU",
    "lv": "LV",
    "lt": "LT",
    "ro": "RO",
    "sk": "SK",
    "sl": "SL",
    "sv": "SV",
    # DeepL biedt (voor zover bekend) geen Iers of Maltees -- die talen
    # kunnen niet via dit script gesynchroniseerd worden.
}


def fail(msg):
    print("FOUT: " + msg, file=sys.stderr)
    sys.exit(1)


def load_api_key():
    key = os.environ.get("DEEPL_API_KEY")
    if key:
        return key.strip()
    key_file = os.path.join(ROOT, "deepl_api_key.txt")
    if os.path.exists(key_file):
        with open(key_file, encoding="utf-8") as fh:
            return fh.read().strip()
    fail(
        "Geen DeepL API key gevonden.\n"
        "  Zet de omgevingsvariabele DEEPL_API_KEY, of\n"
        "  maak een bestand 'deepl_api_key.txt' in deze map met alleen de key erin.\n"
        "  Key aanmaken kan gratis op https://www.deepl.com/pro-api"
    )


def deepl_translate(api_key, texts, target_lang, source_lang=SOURCE_LANG):
    if not texts:
        return []
    is_free = api_key.strip().endswith(":fx")
    base = (
        "https://api-free.deepl.com/v2/translate"
        if is_free
        else "https://api.deepl.com/v2/translate"
    )
    data = [
        ("auth_key", api_key),
        ("source_lang", source_lang.upper()),
        ("target_lang", target_lang),
        ("tag_handling", "html"),
        ("preserve_formatting", "1"),
    ]
    for t in texts:
        data.append(("text", t))
    encoded = urllib.parse.urlencode(data).encode("utf-8")
    req = urllib.request.Request(base, data=encoded, method="POST")
    try:
        with urllib.request.urlopen(req, timeout=30) as resp:
            result = json.loads(resp.read().decode("utf-8"))
    except urllib.error.HTTPError as e:
        body = e.read().decode("utf-8", errors="replace")
        fail(f"DeepL API fout ({e.code}) voor doeltaal {target_lang}: {body}")
    return [t["text"] for t in result["translations"]]


# ---------------------------------------------------------------------------
# HTML translations-object parsing
# ---------------------------------------------------------------------------

BLOCK_RE = re.compile(r"^    (\w{2}): \{\n(.*?)\n    \}(,?)$", re.DOTALL | re.MULTILINE)
KV_RE = re.compile(r'^(\s*)"((?:[^"\\]|\\.)+)":\s*"((?:[^"\\]|\\.)*)"(,?)\s*$')


def unescape(s):
    return s.replace('\\"', '"').replace("\\\\", "\\")


def escape(s):
    return s.replace("\\", "\\\\").replace('"', '\\"')


def parse_html_blocks(html_text):
    """Geeft dict[lang] = {'start','end','comma','body','order','values'}"""
    blocks = {}
    for m in BLOCK_RE.finditer(html_text):
        lang, body, comma = m.group(1), m.group(2), m.group(3)
        order = []
        values = {}
        for line in body.split("\n"):
            kv = KV_RE.match(line)
            if kv:
                key, val = kv.group(2), unescape(kv.group(3))
                order.append(key)
                values[key] = val
        blocks[lang] = {
            "start": m.start(),
            "end": m.end(),
            "comma": comma,
            "body": body,
            "order": order,
            "values": values,
            "full_match": m.group(0),
        }
    return blocks


def set_value_in_block(block, key, new_value):
    """Retourneert een nieuwe body-string met key toegevoegd/bijgewerkt."""
    body = block["body"]
    lines = body.split("\n")
    for i, line in enumerate(lines):
        kv = KV_RE.match(line)
        if kv and kv.group(2) == key:
            indent = kv.group(1)
            comma = kv.group(4)
            lines[i] = f'{indent}"{key}": "{escape(new_value)}"{comma}'
            return "\n".join(lines)
    # nieuwe key: invoegen direct na de openingsregel (eerste regel van body)
    indent = "      "
    new_line = f'{indent}"{key}": "{escape(new_value)}",'
    lines.insert(0, new_line)
    return "\n".join(lines)


# ---------------------------------------------------------------------------
# SVG parsing
# ---------------------------------------------------------------------------

TEXT_LINE_RE = re.compile(r"^(.*<text[^>]*>)([^<]*)(</text>.*)$")


def svg_path(lang):
    return os.path.join(ROOT, f"schema_verdamper_bong_{lang}.svg")


def read_lines(path):
    with open(path, encoding="utf-8") as fh:
        return fh.read().split("\n")


# ---------------------------------------------------------------------------
# State
# ---------------------------------------------------------------------------


def load_snapshot(path):
    if not os.path.exists(path):
        return None
    with open(path, encoding="utf-8") as fh:
        return json.load(fh)


def save_snapshot(path, data):
    os.makedirs(STATE_DIR, exist_ok=True)
    with open(path, "w", encoding="utf-8") as fh:
        json.dump(data, fh, ensure_ascii=False, indent=2)


def backup_file(path):
    if not os.path.exists(path):
        return
    os.makedirs(BACKUP_DIR, exist_ok=True)
    ts = datetime.now().strftime("%Y%m%d-%H%M%S")
    name = os.path.basename(path)
    dest = os.path.join(BACKUP_DIR, f"{name}.{ts}.bak")
    shutil.copy2(path, dest)
    print(f"  backup: {dest}")


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------


def main():
    if not os.path.exists(INDEX_HTML):
        fail(f"{INDEX_HTML} niet gevonden")

    html_text = open(INDEX_HTML, encoding="utf-8").read()
    blocks = parse_html_blocks(html_text)
    if "nl" not in blocks:
        fail("Kon geen 'nl' taalblok vinden in index.html")

    target_langs = [l for l in blocks.keys() if l != "nl"]
    unsupported = [l for l in target_langs if l not in DEEPL_TARGET]
    if unsupported:
        print(
            f"Let op: taal/talen zonder DeepL-ondersteuning worden overgeslagen: {', '.join(unsupported)}"
        )
        target_langs = [l for l in target_langs if l in DEEPL_TARGET]

    # ---- HTML diff t.o.v. snapshot ----
    nl_values = blocks["nl"]["values"]
    baseline = load_snapshot(NL_SNAPSHOT_JSON)

    html_changed_keys = []
    if baseline is None:
        print("Geen eerdere staat gevonden (.sync_state ontbreekt) — dit is de eerste run.")
        print("De huidige NL-tekst wordt als uitgangspunt vastgelegd; er wordt nu niets vertaald.")
    else:
        for key, val in nl_values.items():
            if baseline.get(key) != val:
                html_changed_keys.append(key)
        removed = [k for k in baseline if k not in nl_values]
        if removed:
            print("Let op: deze keys bestaan niet meer in NL, maar zijn niet automatisch verwijderd uit de andere talen:")
            for k in removed:
                print(f"  - {k}")

    # ---- SVG diff t.o.v. snapshot ----
    nl_svg_file = svg_path("nl")
    svg_changed_lines = {}  # line_index -> (old_text, new_text)
    if os.path.exists(nl_svg_file):
        current_nl_svg = read_lines(nl_svg_file)
        baseline_svg = None
        if os.path.exists(NL_SVG_SNAPSHOT):
            baseline_svg = open(NL_SVG_SNAPSHOT, encoding="utf-8").read().split("\n")

        if baseline_svg is None:
            pass  # eerste run, wordt hieronder alleen vastgelegd
        elif len(baseline_svg) != len(current_nl_svg):
            print(
                "Let op: het aantal regels in schema_verdamper_bong_nl.svg is veranderd "
                "(structurele wijziging, niet alleen tekst) — SVG-sync wordt overgeslagen. "
                "Structuurwijzigingen (kleur/dikte/vorm) moeten nog steeds handmatig naar de "
                "andere taalbestanden gekopieerd worden."
            )
        else:
            for i, (old_line, new_line) in enumerate(zip(baseline_svg, current_nl_svg)):
                if old_line == new_line:
                    continue
                old_m = TEXT_LINE_RE.match(old_line)
                new_m = TEXT_LINE_RE.match(new_line)
                if new_m and old_m and old_m.group(2) != new_m.group(2):
                    svg_changed_lines[i] = (old_m.group(2), new_m.group(2))
                elif new_m and not old_m:
                    svg_changed_lines[i] = ("", new_m.group(2))
                # attribute-only wijzigingen (geen <text>-inhoud verschil) worden genegeerd
    else:
        print(f"Waarschuwing: {nl_svg_file} niet gevonden, SVG-sync overgeslagen.")
        current_nl_svg = None

    if not html_changed_keys and not svg_changed_lines:
        if baseline is not None:
            print("Geen wijzigingen in NL-tekst gevonden sinds de vorige run. Niets te doen.")
        # snapshot toch (opnieuw) vastleggen zodat een eerste run 'm initialiseert
        save_snapshot(NL_SNAPSHOT_JSON, nl_values)
        if current_nl_svg is not None:
            os.makedirs(STATE_DIR, exist_ok=True)
            with open(NL_SVG_SNAPSHOT, "w", encoding="utf-8") as fh:
                fh.write("\n".join(current_nl_svg))
        return

    print(f"\nGewijzigde/nieuwe NL-teksten in index.html: {len(html_changed_keys)}")
    print(f"Gewijzigde/nieuwe NL-teksten in schema svg: {len(svg_changed_lines)}")
    print(f"Doeltalen: {', '.join(target_langs)}\n")

    api_key = load_api_key()

    # ---- Vertalen ----
    html_translations = {}  # lang -> {key: new_value}
    for lang in target_langs:
        if not html_changed_keys:
            continue
        texts = [nl_values[k] for k in html_changed_keys]
        translated = deepl_translate(api_key, texts, DEEPL_TARGET[lang])
        html_translations[lang] = dict(zip(html_changed_keys, translated))

    svg_translations = {}  # lang -> {line_index: new_text}
    if svg_changed_lines:
        line_indices = sorted(svg_changed_lines.keys())
        texts = [svg_changed_lines[i][1] for i in line_indices]
        for lang in target_langs:
            if not os.path.exists(svg_path(lang)):
                continue
            translated = deepl_translate(api_key, texts, DEEPL_TARGET[lang])
            svg_translations[lang] = dict(zip(line_indices, translated))

    # ---- Review ----
    print("=" * 70)
    print("VOORGESTELDE WIJZIGINGEN")
    print("=" * 70)
    for lang in target_langs:
        lang_html = html_translations.get(lang, {})
        lang_svg = svg_translations.get(lang, {})
        if not lang_html and not lang_svg:
            continue
        print(f"\n--- {lang} ---")
        for key, new_val in lang_html.items():
            old_val = blocks.get(lang, {}).get("values", {}).get(key)
            tag = "[NIEUW]" if old_val is None else "[GEWIJZIGD]"
            print(f"  {tag} {key}")
            if old_val is not None:
                print(f"    oud:    {old_val}")
            print(f"    nieuw:  {new_val}")
        for line_idx, new_val in lang_svg.items():
            print(f"  [SVG regel {line_idx + 1}] -> {new_val}")

    print("\n" + "=" * 70)
    answer = input("Doorvoeren naar index.html en de SVG's? Typ 'y' om te bevestigen: ").strip().lower()
    if answer not in ("y", "yes", "j", "ja"):
        print("Geannuleerd. Er is niets gewijzigd.")
        return

    # ---- Backups ----
    print("\nBackups maken...")
    backup_file(INDEX_HTML)
    for lang in target_langs:
        if lang in svg_translations:
            backup_file(svg_path(lang))

    # ---- HTML wegschrijven ----
    if html_translations:
        new_html = html_text
        # her-parse elke keer na wijziging om posities correct te houden
        for lang in target_langs:
            lang_updates = html_translations.get(lang)
            if not lang_updates:
                continue
            blocks = parse_html_blocks(new_html)
            block = blocks[lang]
            new_body = block["body"]
            temp_block = dict(block)
            temp_block["body"] = new_body
            for key, new_val in lang_updates.items():
                temp_block["body"] = set_value_in_block(temp_block, key, new_val)
            replacement = f"    {lang}: {{\n{temp_block['body']}\n    }}{block['comma']}"
            new_html = new_html[: block["start"]] + replacement + new_html[block["end"] :]
        with open(INDEX_HTML, "w", encoding="utf-8") as fh:
            fh.write(new_html)
        print("index.html bijgewerkt.")

    # ---- SVG's wegschrijven ----
    for lang, updates in svg_translations.items():
        path = svg_path(lang)
        lines = read_lines(path)
        for line_idx, new_text in updates.items():
            m = TEXT_LINE_RE.match(lines[line_idx])
            if not m:
                print(f"  WAARSCHUWING: regel {line_idx + 1} in {path} heeft niet meer het verwachte formaat, overgeslagen.")
                continue
            lines[line_idx] = m.group(1) + new_text + m.group(3)
        with open(path, "w", encoding="utf-8") as fh:
            fh.write("\n".join(lines))
        print(f"{os.path.basename(path)} bijgewerkt.")

    # ---- State updaten ----
    save_snapshot(NL_SNAPSHOT_JSON, nl_values)
    if current_nl_svg is not None:
        os.makedirs(STATE_DIR, exist_ok=True)
        with open(NL_SVG_SNAPSHOT, "w", encoding="utf-8") as fh:
            fh.write("\n".join(current_nl_svg))

    print("\nKlaar. Controleer de wijzigingen (bv. lokaal bekijken) en commit/push zoals gebruikelijk.")


if __name__ == "__main__":
    main()
