# Quiz-Ping Palette-lösare

Gissar vilken Tibia Bestiary-varelse som matchar de 5 färgrutorna i
Quiz-Pings `:: palette`-kommando på Discord.

## Snabbstart

Öppna `index.html` i valfri webbläsare. Ladda upp en skärmdump av
palette-meddelandet (eller mata in färgerna manuellt), klicka
**Gissa varelse**.

Testat mot de 9 kända facit vi hade (Swampling, Blood Priest, Courage
Leech, Bandit, Pig, Fire Devil, Death Priest, Iron Servant Replica,
Crypt Warrior): **6/9 rätt på första plats, 8/9 bland topp 3.** Notera
att detta är mot en databas med bara dessa 9 — med alla ~819
Bestiary-varelser i databasen blir förstaplats-träffsäkerheten
sannolikt lägre, men topplistan (topp 10–20) bör fortfarande snäva in
det rejält.

## Hur matchningen funkar

1. **Databas** (`data/creatures_db.json`): för varje monster, 5
   representativa färger — beräknade genom k-means-klustring (k=5) på
   monstrets sprite. Klustringen körs på **unika** färgtripplar (inte
   pixelvägt), utan filtrering av svart, och bara på spritens första
   bildruta. Ordnat efter klusterstorlek (störst = mest framträdande).
2. **Extraktion från skärmdump**: bilden delas i 5 lika breda
   vertikala fält, och medianfärgen i den centrala 40%-regionen av
   varje fält plockas ut (undviker kant-/kompressionsbrus).
3. **Matchning**: jämför inputfärgerna mot varje monsters 5 färger med
   **alla möjliga positionstilldelningar** (5! = 120 permutationer) och
   tar den som ger lägst total färgdistans. Vi testade positions-låst
   jämförelse (ruta 1 mot ruta 1 osv) men den var betydligt sämre —
   Quiz-Pings egen ordning verkar inte vara tillförlitlig att lita på.

## Skala upp databasen

Just nu innehåller `data/creatures_db.json` bara de 9 monster vi
redan hade facit för. För att täcka alla Bestiary-varelser:

```bash
pip install requests pillow scikit-learn numpy

# 1) Ladda ner sprites (testa med --limit 20 först)
python scripts/scrape_creatures.py --outdir sprites/ --limit 20

# När det ser bra ut, kör utan --limit för alla ~819:
python scripts/scrape_creatures.py --outdir sprites/

# 2) Bygg databasen från de nedladdade sprites
python scripts/build_palette_db.py --input sprites/ --output data/creatures_db.json
```

`scripts/scrape_creatures.py` är en enkel mall (MediaWiki-API mot
TibiaWiki, hittar infobox-bilden på varje varelses sida). Om du redan
har bättre nedladdningslogik från itemleta-projektet, återanvänd
gärna den istället — samma princip.

Efter ny `creatures_db.json`, uppdatera `CREATURE_DB`-konstanten i
`index.html` (leta efter `const CREATURE_DB = ...`) med det nya
innehållet, så det fungerar utan att behöva servera filen separat.

## Nästa steg att fundera på

- **Fler facit** = bättre kalibrering. Om algoritmen missar ofta när
  databasen växer, spara (skärmdump, facit)-par och vi kan justera
  klustringsparametrarna (k, svart-tröskel, viktning) mot fler
  exempel.
- **Distinkta paletter**: ju fler monster i databasen, desto större
  risk att flera har snarlika färgprofiler (t.ex. flera bruna
  humanoida varelser). Topp-10-listan blir viktigare än exakt
  förstaplats när databasen växer.
- **Deploy**: samma GitHub Pages-upplägg som dina andra Tibia-verktyg
  funkar rakt av — `index.html` är helt fristående (ingen server
  behövs, databasen är inbäddad).
