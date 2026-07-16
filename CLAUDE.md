# dampinfo-website

Statische, responsive informatiepagina over verdampen vs. roken van cannabis (THC/CBD), beschikbaar in het Nederlands, Engels, Duits, Frans, Spaans, Italiaans, Pools en Portugees.

## Bestanden

- `index.html` — de volledige pagina: HTML + CSS inline, geen build-stap, geen dependencies. Bevat een i18n-systeem: elementen hebben `data-i18n`/`data-i18n-alt` attributen, een JS `translations`-object (onderaan `<body>`) bevat de teksten per taalcode (`nl`/`en`/`de`/`fr`/`es`/`it`/`pl`/`pt`, zie ook de `supported`-array), en `applyLanguage()` past dit toe. Taalkeuze staat rechtsboven in de header (`#langSelect`, vlag + taalnaam), wordt onthouden via `localStorage` en anders bepaald via `navigator.language`.
- `schema_verdamper_bong_{nl,en,de,fr,es,it,pl,pt}.svg` — schematische afbeelding (heater → verdamping → waterfiltratie/bong) per taal (de tekst staat in de SVG zelf gebrand, dus elke taal heeft een eigen bestand). Geladen als `<img id="schemaImg">` in de "Zo werkt een verdamper"-sectie; `applyLanguage()` wisselt `src` naar `schema_verdamper_bong_<lang>.svg`.
- `uitleg.md` — achtergrond/uitleg over de pagina-inhoud, niet meegecommit (staat in `.gitignore`).

## Vertalingen aanpassen/uitbreiden

Voeg je een nieuwe sectie of tekst toe aan `index.html`: geef het element een `data-i18n="key"` attribuut en voeg diezelfde `key` toe aan **alle** taalblokken in het `translations`-object. Voeg je een nieuwe taal toe: nieuw blok in `translations`, toevoegen aan de `supported`-array, nieuwe `<option>` in `#langSelect`, en een nieuwe `schema_verdamper_bong_<lang>.svg` met vertaalde labels (zelfde lay-out/coördinaten, alleen tekst wijzigen).

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

## Publiceren

Wijzigingen aan `index.html` of de svg: gewoon committen en pushen naar `main`, GitHub Pages bouwt automatisch opnieuw.
