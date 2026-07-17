# dampinfo-website

Statische, responsive informatiepagina over verdampen vs. roken van cannabis (THC/CBD), beschikbaar in 22 EU-talen: Nederlands, Engels, Duits, Frans, Spaans, Italiaans, Pools, Portugees, Bulgaars, Kroatisch, Tsjechisch, Deens, Ests, Fins, Grieks, Hongaars, Lets, Litouws, Roemeens, Slowaaks, Sloveens en Zweeds. Iers en Maltees zijn bewust niet toegevoegd (zie `handleiding.md`).

## Bestanden

- `index.html` — de volledige pagina: HTML + CSS inline, geen build-stap, geen dependencies. Bevat een i18n-systeem: elementen hebben `data-i18n`/`data-i18n-alt` attributen, een JS `translations`-object (onderaan `<body>`) bevat de teksten per taalcode (`nl`/`en`/`de`/`fr`/`es`/`it`/`pl`/`pt`/`bg`/`hr`/`cs`/`da`/`et`/`fi`/`el`/`hu`/`lv`/`lt`/`ro`/`sk`/`sl`/`sv`, zie ook de `supported`-array), en `applyLanguage()` past dit toe. Taalkeuze staat rechtsboven in de header (`#langSelect`, vlag + taalnaam), wordt onthouden via `localStorage`, kan overruled worden via `?lang=<code>` in de URL (gebruikt door de promoflyers), en anders bepaald via `navigator.language`.
- **Light/dark thema**: schakelaar (`#themeToggle`, ☀️/🌙) staat naast `#langSelect`. Zet/verwijdert `data-theme="dark"` op `<html>`, onthouden via `localStorage` (`dampinfo-theme`); een inline script vroeg in `<head>` past dit al toe vóór de eerste render (voorkomt flits van het verkeerde thema). Alle kleuren lopen via CSS-variabelen in `:root` (licht) en `[data-theme="dark"]` (donker: `--green-pale`, `--cream`, `--ink`, `--green-text`, `--red`, `--surface`, `--text-soft`, `--text-softer`, `--border-soft`, `--border-dash`, `--track-bg`, `--shadow`). `--green-dark`/`--green`/`--green-light` blijven bewust ongewijzigd tussen thema's — die worden alleen als *achtergrond* gebruikt (header, callout, figcaption), niet als tekstkleur; voor groene *tekst* (koppen, `.ok`, tocbtn) gebruik je `--green-text`. Voeg je nieuwe UI toe met kleur: gebruik altijd een bestaande of nieuwe variabele, nooit een hardgecodeerde hexkleur, anders breekt dark mode stilletjes. De schema-SVG's blijven in beide thema's altijd licht (ze staan in een neutrale `.schema-photo`-kader); die hoeven geen donkere variant.
- `schema_verdamper_bong_{nl,en,de,fr,es,it,pl,pt,bg,hr,cs,da,et,fi,el,hu,lv,lt,ro,sk,sl,sv}.svg` — schematische afbeelding (heater → verdamping → waterfiltratie/bong) per taal (de tekst staat in de SVG zelf gebrand, dus elke taal heeft een eigen bestand). Geladen als `<img id="schemaImg">` in de "Zo werkt een verdamper"-sectie; `applyLanguage()` wisselt `src` naar `schema_verdamper_bong_<lang>.svg`. Titel-`font-size` varieert licht per taal (24 als basis, kleiner voor talen met een langere vertaalde titel) zodat de titel binnen de 900px-brede canvas blijft — check dit bij nieuwe/gewijzigde titels via `element.getBBox().width` in de browser.
- `uitleg.md` — achtergrond/uitleg over de pagina-inhoud, niet meegecommit (staat in `.gitignore`).
- `handleiding.md` — handleiding voor het beheren van vertalingen en het gebruik van `sync_translations.py`.
- `sync_translations.py` — lokale tool die NL-tekstwijzigingen via de DeepL API doorzet naar de overige talen (zie `handleiding.md`).

## Vertalingen aanpassen/uitbreiden

Voeg je een nieuwe sectie of tekst toe aan `index.html`: geef het element een `data-i18n="key"` attribuut en voeg diezelfde `key` toe aan **alle** taalblokken in het `translations`-object (of draai `sync_translations.py` na het toevoegen aan het `nl`-blok). Voeg je een nieuwe taal toe: nieuw blok in `translations`, toevoegen aan de `supported`-array, nieuwe `<option>` in `#langSelect`, en een nieuwe `schema_verdamper_bong_<lang>.svg` met vertaalde labels (zelfde lay-out/coördinaten, alleen tekst wijzigen).

## Live

- Repo: https://github.com/appsbeheerder/no-smoking
- GitHub Pages (bron: `main`, root): https://appsbeheerder.github.io/no-smoking/

## Lokaal testen

```
python -m http.server 8000
```
dan http://localhost:8000/index.html openen.

## Belangrijke feiten die in de pagina verwerkt zijn

- THC verdampt rond 180°C, CBD rond 210°C.
- Boven 230°C verbrandt het plantmateriaal (niet meer alleen verdampen).
- Roken: ~20% werkzame stof ingeademd, 80% verloren. Verdampen: omgekeerd (~80% ingeademd).
- Temperatuurbalk in `index.html` (`.temp-bar` gradient + `.temp-marker` posities) is geschaald op een as van 150–250°C, met 3 `.temp-labels` (150/200/250°C) voor voldoende ruimte tussen de getallen op kleine schermen (`.temp-scale` heeft `max-width:560px` en extra padding onder 600px om overloop te voorkomen); wijzig je de grenswaarden, pas dan zowel de gradient-stops als de marker `left:%`-waarden én de `.temp-labels` samen aan — ze moeten met elkaar kloppen.

## Vertalingen automatisch bijwerken (sync_translations.py)

`sync_translations.py` is een lokaal Python-script (geen dependencies buiten de standaardbibliotheek) dat tekstwijzigingen in de NL-versie (`translations.nl` in `index.html`, en `schema_verdamper_bong_nl.svg`) via de DeepL API doorzet naar de overige talen die al als blok/bestand bestaan. Gebruik: eerst NL-tekst aanpassen zoals gebruikelijk, dan `python sync_translations.py` draaien; het script toont een reviewoverzicht dat je expliciet moet bevestigen (`y`), en maakt altijd eerst een timestamped backup in `backups/` voordat het iets overschrijft. Vereist een DeepL API key via env var `DEEPL_API_KEY` of een lokaal (gitignored) bestand `deepl_api_key.txt`. Detecteert wijzigingen door de huidige NL-tekst te vergelijken met een snapshot in `.sync_state/` (ook gitignored); bij de eerste run wordt alleen die baseline vastgelegd, zonder te vertalen. Het script voegt géén nieuwe taal toe (nieuw blok, `<option>`, SVG-bestand) — dat blijft handmatig werk.

## Publiceren

Wijzigingen aan `index.html` of de svg: gewoon committen en pushen naar `main`, GitHub Pages bouwt automatisch opnieuw.
