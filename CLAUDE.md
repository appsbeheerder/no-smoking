# dampinfo-website

Statische, responsive informatiepagina (Nederlands) over verdampen vs. roken van cannabis (THC/CBD).

## Bestanden

- `index.html` — de volledige pagina: HTML + CSS inline, geen build-stap, geen dependencies.
- `schema_verdamper_bong.svg` — schematische afbeelding (heater → verdamping → waterfiltratie/bong), ingeladen als `<img>` in de "Zo werkt een verdamper"-sectie.
- `uitleg.md` — achtergrond/uitleg over de pagina-inhoud, niet meegecommit (staat in `.gitignore`).

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
- Temperatuurbalk in `index.html` (`.temp-bar` gradient + `.temp-marker` posities) is geschaald op een as van 50–250°C; wijzig je de grenswaarden, pas dan zowel de gradient-stops als de marker `left:%`-waarden én de `.temp-labels` samen aan — ze moeten met elkaar kloppen.

## Publiceren

Wijzigingen aan `index.html` of de svg: gewoon committen en pushen naar `main`, GitHub Pages bouwt automatisch opnieuw.
