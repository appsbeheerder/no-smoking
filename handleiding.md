# Handleiding: talen beheren op dampinfo-website

## Wat doet index.html?

`index.html` is de volledige website: één statisch HTML-bestand met alle CSS
en JavaScript erin, zonder build-stap en zonder externe dependencies. De
pagina legt uit hoe verdampen (vaporizen) van cannabis (THC/CBD) verschilt
van roken — temperaturen, efficiëntie, de werking van een verdamper met
waterfiltratie (bong), en de voordelen. De taalkeuze staat rechtsboven in de
header en wordt onthouden via `localStorage`.

De pagina ondersteunt alle officiële EU-talen **behalve Iers en Maltees**
(die zijn bewust niet toegevoegd — te kleine doelgroep voor deze site, en
Iers/Maltees worden ook niet door de vertaal-API ondersteund):

| Code | Taal | Code | Taal |
|------|------|------|------|
| nl | Nederlands | hu | Hongaars |
| en | Engels | lv | Lets |
| de | Duits | lt | Litouws |
| fr | Frans | pl | Pools |
| es | Spaans | pt | Portugees |
| it | Italiaans | ro | Roemeens |
| bg | Bulgaars | sk | Slowaaks |
| hr | Kroatisch | sl | Sloveens |
| cs | Tsjechisch | sv | Zweeds |
| da | Deens | el | Grieks |
| et | Ests | fi | Fins |

## Hoe de vertalingen zijn opgebouwd

Elk stukje tekst op de pagina heeft een `data-i18n="key"` attribuut (of
`data-i18n-alt` voor `alt`-teksten van afbeeldingen). Onderaan `index.html`
staat een JavaScript-object `translations`, met per taalcode (`nl`, `en`,
`de`, …) een blok van dezelfde ~83 keys, elk met de vertaalde tekst. De
functie `applyLanguage(lang)` loopt alle elementen met `data-i18n` af en zet
de tekst op basis van de gekozen taal.

Het schema-plaatje ("Zo werkt een verdamper") is een aparte afbeelding per
taal: `schema_verdamper_bong_<taalcode>.svg`. Dat kan niet via het
`translations`-object, omdat de tekst in een SVG is "ingebakken" (getekend),
niet los van de opmaak. Daarom bestaat er van elke taal een eigen
SVG-bestand met dezelfde opmaak/coördinaten, maar vertaalde tekstlabels.

## Werken met vertalingen: de basisregel

**Je bewerkt altijd eerst de Nederlandse tekst** — in `index.html` (het
`nl:`-blok in `translations`) en/of in `schema_verdamper_bong_nl.svg`. Dat is
de brontaal. Daarna zorgt `sync_translations.py` ervoor dat diezelfde
wijziging in alle andere talen doorgevoerd wordt.

Bewerk dus nooit rechtstreeks de tekst van een andere taal (bijvoorbeeld het
`de:`-blok) als het om een inhoudelijke correctie gaat — die wijziging wordt
dan namelijk niet meegenomen als "brontekst" en raakt bij een volgende sync
niet gesynchroniseerd met de andere talen. Directe taalspecifieke fixes
(bijvoorbeeld een tikfout die alleen in het Duits staat) kun je natuurlijk
wel gewoon los aanpassen.

## sync_translations.py gebruiken

### Wat het wel en niet vertaalt

Het script vertaalt **niet steeds de hele site opnieuw**. Het onthoudt (in de
lokale map `.sync_state/`, niet in git) hoe de Nederlandse tekst eruitzag na
de laatste keer dat je het script draaide. Bij elke nieuwe run vergelijkt het
de huidige Nederlandse tekst met die laatste bekende versie, en vertaalt
**alleen de teksten die je hebt gewijzigd of nieuw hebt toegevoegd**. Ongewijzigde
teksten in de andere taalblokken blijven precies zoals ze waren — het script
overschrijft dus nooit handmatige verbeteringen die je ooit in bijvoorbeeld
het Franse blok hebt gemaakt, tenzij de bijbehorende Nederlandse tekst ook
daadwerkelijk is aangepast.

Bij de allereerste keer dat je het script draait (of nadat de map
`.sync_state/` is verwijderd) is er nog geen "vorige versie" om mee te
vergelijken. Dan legt het script alleen de huidige Nederlandse tekst vast als
nieuw ijkpunt, zonder iets te vertalen.

### API key instellen

Het script gebruikt de DeepL API om te vertalen. Dat vereist een eigen,
losse API key (dit is *niet* hetzelfde als een Claude/Anthropic-abonnement):

1. Ga naar https://www.deepl.com/pro-api en maak een (gratis) account/key aan.
2. Zet de key op een van deze twee manieren beschikbaar voor het script:
   - **Omgevingsvariabele** (per sessie, niet opgeslagen):
     ```
     set DEEPL_API_KEY=jouw-key-hier
     ```
     (op macOS/Linux/Git Bash: `export DEEPL_API_KEY=jouw-key-hier`)
   - **Lokaal bestand** (blijvend, alleen op je eigen pc):
     maak een bestand `deepl_api_key.txt` in dezelfde map als `index.html`,
     met alleen de key erin.

   Beide manieren staan al in `.gitignore` — de key komt dus nooit in git
   terecht.

### Draaien

```
python sync_translations.py
```

Het script:

1. Leest de huidige NL-tekst uit `index.html` en `schema_verdamper_bong_nl.svg`.
2. Vergelijkt die met de vorige bekende versie en bepaalt wat gewijzigd/nieuw is.
3. Vertaalt alleen die wijzigingen naar alle talen die al in het bestand
   staan (op Iers/Maltees na — die worden niet door DeepL ondersteund).
4. Toont een overzicht: per taal, per key, "oud → nieuw".
5. Vraagt om expliciete bevestiging (typ `y`) voordat er iets wordt
   weggeschreven. Antwoord je iets anders, dan gebeurt er niets.
6. Maakt bij bevestiging **altijd eerst een backup** van elk bestand dat gaat
   wijzigen, in de map `backups/` (met tijdstempel in de bestandsnaam).
7. Schrijft de wijzigingen weg naar `index.html` en de betreffende SVG's, en
   legt de nieuwe NL-tekst vast als ijkpunt voor de volgende keer.

Na een geslaagde run: gewoon zoals gebruikelijk controleren (bijvoorbeeld
lokaal bekijken met `python -m http.server`) en dan committen/pushen.

### Wat het script niet doet

- **Geen nieuwe taal toevoegen.** Een taal die nog niet als blok in
  `translations` en als eigen SVG-bestand bestaat, wordt door het script niet
  aangemaakt. Dat blijft eenmalig werk (nieuw blok, nieuwe `<option>` in de
  taalkiezer, nieuw SVG-bestand) — de huidige 22 talen zijn zo toegevoegd.
- **Geen structurele SVG-wijzigingen.** Alleen de tekst ín een `<text>`-element
  wordt gesynchroniseerd. Wijzig je kleuren, lijndikte of vormen in de
  Nederlandse SVG (zoals contrastverbeteringen), dan moet je die
  stijlwijziging nog steeds zelf (of via Claude Code) naar de andere 21
  SVG-bestanden kopiëren.
- **Geen verwijderde teksten.** Haal je een key weg uit het Nederlandse blok,
  dan meldt het script dat die key niet meer bestaat, maar verwijdert 'm niet
  automatisch uit de andere talen — dat moet je bewust zelf doen.
