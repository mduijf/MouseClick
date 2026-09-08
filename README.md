# Yellowspot MouseClick

**Versie:** V1.0  
**Platform:** Windows  

Yellowspot MouseClick is een eenvoudige Windows-applicatie waarmee je muisklikken kunt plannen op instelbare **tijdstippen** en **schermposities**. Handig voor repetitieve taken, geplande acties of automatisering zonder complexe scripts.

---

## Download

De nieuwste versie staat in de map [`dist/`](dist/):

| Bestand | Beschrijving |
|---------|--------------|
| `YellowspotMouseClick-v1.0.exe` | Uitvoerbaar programma |
| `version.txt` | Huidige versie (bijv. `V1.0`) |
| `clicks.json` | Optioneel voorbeeldbestand met instellingen |

Je hebt alleen de `.exe` nodig om te starten. `clicks.json` is niet verplicht — de app maakt dit bestand zelf aan zodra je klikken opslaat.

---

## Snel starten

1. Start **`YellowspotMouseClick-v1.0.exe`**
2. Stel timing, positie en type klik in
3. Klik op **+ Toevoegen**
4. Druk op **▶ START**
5. Minimaliseer het venster — de app blijft op de achtergrond draaien

---

## Gebruikershandleiding

### Timing

Er zijn twee modi:

| Modus | Veld | Voorbeeld | Uitleg |
|-------|------|-----------|--------|
| **Vertraging** | Seconden | `5` | Wacht 5 seconden, voer dan de klik uit |
| **Kloktijd** | Tijdstip (`uu:mm:ss`) | `14:30:00` | Wacht tot 14:30 uur, voer dan de klik uit |

**Kloktijd:** Is het tijdstip vandaag al voorbij, dan wacht de app tot morgen op datzelfde moment.

### Positie

- Vul **X** en **Y** handmatig in (schermcoördinaten in pixels)
- Of klik op **Huidige positie** om de huidige muiscoördinaat over te nemen

### Type klik

- Standaard: enkele klik
- Vink **Dubbelklik** aan voor een dubbelklik op dezelfde positie

In de lijst zie je het verschil:
- `3s → klik (500, 400)` — enkele klik
- `3s → 2x (500, 400)` — dubbelklik

### Geplande klikken

- Meerdere klikken worden **van boven naar beneden** uitgevoerd
- Selecteer een regel en klik **Verwijder geselecteerd** om te wissen
- Instellingen worden automatisch opgeslagen in `clicks.json` naast de `.exe`

### Herhalen

- Vink **Herhalen** aan om de hele reeks klikken te herhalen
- Stel **Pauze (sec)** in voor de wachttijd tussen rondes

---

## Op de achtergrond draaien

### Minimaliseren → systeemvak

- Minimaliseer het venster na **START**
- De app verdwijnt naar het **systeemvak** (icoon naast de klok, geel **Y**)
- **Dubbelklik** op het icoon → venster weer open
- **Rechtsklik** → **Openen** of **Afsluiten**

### Belangrijk

| Actie | Gevolg |
|-------|--------|
| Minimaliseren | ✅ App blijft draaien |
| Venster sluiten (✕) | ❌ App stopt |
| PC in slaapstand | ⏸ Timers pauzeren |

Als er nog klikken lopen en je probeert af te sluiten, krijg je een **waarschuwing**.

---

## clicks.json

Het configuratiebestand staat automatisch naast de `.exe`:

```json
{
  "clicks": [
    {
      "mode": "delay",
      "delay": 3,
      "x": 500,
      "y": 400,
      "double": false
    },
    {
      "mode": "clock",
      "time": "14:30:00",
      "x": 800,
      "y": 300,
      "double": true
    }
  ],
  "repeat": false,
  "pause": "5"
}
```

| Veld | Betekenis |
|------|-----------|
| `mode` | `"delay"` of `"clock"` |
| `delay` | Seconden wachten (alleen bij `delay`) |
| `time` | Tijdstip `HH:MM:SS` (alleen bij `clock`) |
| `x`, `y` | Schermpositie |
| `double` | `true` = dubbelklik, `false` = enkele klik |
| `repeat` | Hele reeks herhalen |
| `pause` | Pauze tussen rondes (seconden) |

---

## Ontwikkelaars

### Vereisten

- Windows 10/11
- Python 3.10+ (alleen voor bouwen vanuit broncode)

### Lokaal draaien

```bat
pip install pystray Pillow
python main.py
```

### .exe bouwen

```bat
build.bat
```

Output in `dist/`:
- `YellowspotMouseClick-v{versie}.exe`
- `version.txt`

### Versiebeheer

De versie staat in [`version.py`](version.py):

```python
__version__ = "1.0"  # wordt getoond als V1.0
```

**Bij elke wijziging** het versienummer verhogen:

```bash
python bump_version.py          # patch: 1.0 → 1.1
python bump_version.py minor    # minor: 1.0 → 1.1.0
python bump_version.py major    # major: 1.0 → 2.0.0
```

Daarna committen en pushen — GitHub Actions bouwt automatisch een nieuwe `.exe`.

### Projectstructuur

```
MouseClick/
├── main.py              # App + gebruikersinterface
├── mouse_click.py       # Windows muisklik-API
├── tray.py              # Systeemvak-icoon
├── version.py           # Versienummer (bron)
├── bump_version.py      # Versie verhogen
├── build.bat            # Lokaal .exe bouwen
├── MouseClick.spec      # PyInstaller-configuratie
├── clicks.json          # Voorbeeldconfiguratie
└── dist/                # Gebouwde releases
    ├── YellowspotMouseClick-v1.0.exe
    └── version.txt
```

---

## GitHub Actions

Bij elke push naar `main` wordt automatisch een Windows-build gemaakt. Download de `.exe` via:

**GitHub → Actions → Build Windows exe → Artifacts**

Of direct uit de [`dist/`](dist/) map in deze repository.

---

## Veelgestelde vragen

**Moet clicks.json naast de exe staan?**  
Nee. De app werkt zonder. Het bestand wordt automatisch aangemaakt wanneer je klikken toevoegt.

**Kan ik het venster vergroten?**  
Ja, het venster is vergrootbaar. De knoppen onderaan blijven altijd zichtbaar.

**Werkt dit op Mac?**  
Nee, alleen Windows. De app gebruikt de Windows `user32`-API voor muissimulatie.

---

## Licentie

Intern Yellowspot-project.
