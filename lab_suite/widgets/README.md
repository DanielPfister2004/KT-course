# lab_suite/widgets – Custom-Widget-Bibliothek für NiceGUI

Wiederverwendbare **Vue-3-Komponenten** (Options API, `.js` mit `export default { template, props, … }`). Sie werden von NiceGUI als Custom-Elemente geladen; die `.js`-Dateien sind **kein** reines Vanilla-JS, sondern echte Vue-Komponenten.

## Ordnerstruktur (Standard für neue Widgets)

```
lab_suite/widgets/
├── README.md           # Diese Datei
├── __init__.py             # Exportiert alle Widgets
├── gain_control.js / .py
├── vu_meter.js / .py
├── led.js / .py
├── plotly_graph.js / .py   # Generisches Plotly-Widget (Spektrum, Oszilloskop, Scatter, 3D)
└── image_icon_demo.js/.py
```

**Regel:** Die `.js`- (oder `.vue`-) Datei muss **im selben Ordner** wie die `.py`-Klasse liegen. NiceGUI löst `component='gain_control.js'` relativ zur Python-Datei auf.

## In Vue-/Nuxt-Apps wiederverwenden

Die Widgets sind **Vue-3-Komponenten** (Options API, String-Template). Du kannst sie in einer reinen Vue- oder Nuxt-App registrieren und nutzen:

- **Vue 3 (z. B. Vite):** Komponente importieren und global oder lokal registrieren. Wichtig: String-Templates werden zur Laufzeit kompiliert – dafür muss das Vue-Bundle den **Template-Compiler** enthalten (z. B. `vue/dist/vue.esm-bundler.js` mit `compilerOptions.isCustomElement` je nach Setup).
- **Nuxt 3:** Üblicherweise wird die **Runtime-only**-Variant von Vue genutzt; dann werden nur `.vue`-SFCs beim Build kompiliert. **Option A:** Die `.js`-Widgets in **`.vue`-Dateien** auslagern (Template in `<template>`, Rest in `<script>`) und in `components/` legen – dann funktioniert alles mit Auto-Import. **Option B:** Im Nuxt-Build den Vue-Full-Build (mit Compiler) verwenden und die `.js`-Dateien z. B. in `plugins/` oder `components/` laden und registrieren.

Die Widgets haben **keine Abhängigkeit** zu NiceGUI oder Quasar; nur Vue-API (props, computed, methods, `$emit`). Für Nuxt ist die sauberste Integration: eine `.vue`-Hülle pro Widget, die das bestehende Options-Objekt importiert und als Komponente recycelt oder das Template ins SFC übernimmt.

## Vue/Nuxt-Seite + Python-App (Sound-App steuern)

**Ja.** Du kannst eine Vue-/Nuxt-Webseite bauen, die mit der Python-App (NiceGUI/Sound-App) über eine Portnummer kommuniziert und die App darüber steuert. Einschränkung: Der **Browser kann den Python-Server nicht selbst starten**, wenn der Nutzer die Seite aufruft (Sicherheit). Es braucht also eines der folgenden Muster:

- **Variante A – Iframe + ggf. Launcher**
  - Die Python-App läuft auf einem Port (z. B. `8080`). Die Vue/Nuxt-Seite läuft auf anderem Port (z. B. `3000`).
  - Auf der Vue-Seite: **iframe** mit `src="http://localhost:8080"` (oder die URL des Python-Servers). So siehst du die komplette NiceGUI-Oberfläche in deiner Seite; Steuerung passiert im Iframe (gleiche Oberfläche wie bisher).
  - „Beim Aufruf der Seite den Python-Server starten“: Geht nur indirekt. Z. B. ein **Launcher** (eigenes kleines Backend auf demselben Rechner): Die Vue-Seite hat einen Button „Lab starten“; ein Klick ruft z. B. `POST /api/start-lab` beim Launcher auf. Der Launcher startet per `subprocess` die Python-App (z. B. `python -m labs.use_case_template --port 8080`) und antwortet mit der URL. Die Vue-Seite öffnet dann das Iframe oder leitet dorthin weiter. Die Python-App muss also vom Launcher gestartet werden, nicht vom Browser direkt.

- **Variante B – Vue-Komponenten + API zum Python-Backend**
  - Die Vue/Nuxt-Seite nutzt **unsere Widgets** (Gain, VU-Meter, LED, …) im eigenen Layout.
  - Die Python-App bietet zusätzlich eine **REST- oder WebSocket-API** (z. B. `/api/gain`, `/api/run`, …). Die Vue-Seite spricht mit dieser API (z. B. `fetch('http://localhost:8080/api/gain', { method: 'POST', body: JSON.stringify({ value: 2 }) })`).
  - So steuerst du die Sound-App aus der Vue-Seite heraus: Gain, Run, Gerätewahl etc. über HTTP/WebSocket, die Anzeige mit unseren Vue-Komponenten lokal in der Seite.

**Port-Kommunikation:** Vue (z. B. Port 3000) und Python (z. B. 8080) laufen getrennt. Von der Vue-App aus erreichst du die Python-App über die absolute URL (lokal `http://localhost:8080`, im Deployment die URL des Backends). CORS muss auf dem Python-Server für diese Origin erlaubt sein (NiceGUI/FastAPI: entsprechende CORS-Middleware).

**Zusammenfassung:** Komponente in Vue/Nuxt einbinden geht. Die Sound-App über die Seite steuern geht per Iframe (ganze NiceGUI-UI) oder per eigener API + unsere Komponenten in der Vue-Seite. Den Python-Server „beim Aufruf der Seite“ starten geht nur über einen zusätzlichen Launcher-Dienst, der den Prozess startet.

## Neues Widget anlegen

1. **`<name>.js`** anlegen: Vue-Komponente mit `template`, `props`, `data`, `methods`. Bei Änderung Wert per `this.$emit('change', value)` senden; Methoden wie `reset()` für `run_method('reset')` anbieten.
2. **`<name>.py`** anlegen: Klasse von `Element` mit `component='<name>.js'`, Props in `__init__` setzen (`self._props['...'] = ...`), Events mit `self.on('change', on_change)`.
3. In **`__init__.py`** exportieren: `from .<name> import <Klassenname>` und in `__all__` aufnehmen.

## Regel: Input/Slider – natives „change“-Event (Maus loslassen) abfangen

**Problem:** Bei `<input type="range">` (und anderen Inputs) feuert der Browser beim **Loslassen der Maus** ein natives **`change`**-Event. NiceGUI kann dieses Event an die Python-Seite weiterleiten – oft mit dem **initialen Prop-Wert** (z. B. 1.0) statt dem vom User eingestellten Wert. Dadurch wird der State nach dem Loslassen fälschlich überschrieben.

**Lösung (in der Vue-Komponente):**

- Am Input **nur** `@input` für die Wertänderung nutzen (emittieren in `onInput`).
- Das native **`change`**-Event (Maus loslassen) **abfangen und stoppen**, damit es **nicht** an NiceGUI durchgereicht wird:
  - `@change.stop="onNativeChange"` am Input,
  - in `methods`: `onNativeChange(ev) { ev.stopPropagation(); ev.preventDefault(); }`
- **Kein** `$emit` im `change`-Handler – der aktuelle Wert wurde bereits mit dem letzten `input`-Event gesendet.

**Beispiel (Auszug):**

```html
<input type="range" ... @input="onInput" @change.stop="onNativeChange" />
```

```js
methods: {
  onInput(ev) {
    const v = parseFloat(ev.target.value);
    if (!Number.isNaN(v)) { this.internalValue = v; this._emitValue(v); }
  },
  onNativeChange(ev) {
    ev.stopPropagation();
    ev.preventDefault();
  },
}
```

So kommen nur die gewollten Emits (z. B. aus `@input` und Reset-Button) in Python an; bewusst auf 1.0 gestellte Werte bleiben erhalten.

## Verwendung in einer App

```python
from nicegui import ui
from lab_suite.widgets import GainControlVue

# Wie ein normales NiceGUI-Widget
gain = GainControlVue('Gain', min_=0, max_=10, value=1, on_change=lambda e: ui.notify(f'Gain: {e.args}'))
# Reset von außen
ui.button('Reset Gain', on_click=gain.reset)

ui.run(uvicorn_reload_includes='*.py,*.js,*.vue')  # Optional: Reload bei Änderung an .js/.vue
```

## GainControlVue (Demo)

- **Props:** `label`, `min_`, `max_`, `value`
- **Event:** `change` → `e.args` ist der neue Wert (float)
- **Methode:** `reset()` setzt auf 1 und feuert `change`

## VuMeter (VU-Meter / analoge Anzeige)

- **Nur Anzeige:** Wert von außen setzen, z. B. aus Audio-Pegel oder Slider.
- **Darstellung:** Im `.js` per **SVG** (Halbkreis-Skala + rote Nadel). Kein Canvas – deklarativ im Template, Nadelwinkel per `value` → computed.
- **Props:** `value`, `min_`, `max_`, `show_value`, `width`, `height`
- **Methode:** `set_value(value)` – Anzeige aktualisieren (z. B. in Timer/Callback).

```python
from lab_suite.widgets import VuMeter
vu = VuMeter(value=0.5, min_=0, max_=1, width="120px", height="80px")
# später: vu.set_value(0.8)
```

## Plot-Widget (Plotly): generisch vs. spezialisiert

**Empfehlung: Hybrid.** Die **Steuerung** für Oszilloskop (Time-Base, Trigger, Kanal) vs. Spektrum (RBW, Span, Referenzpegel, Marker) ist sehr unterschiedlich – dafür lohnen sich **spezialisierte** Wrapper oder eigene Vue-Komponenten. Die **Darstellung** (ein Plotly-Graph) ist dagegen für alle Modi gleich.

- **Ein generisches Plot-Widget** (`PlotlyGraph`): eine Vue-Komponente, die nur **data** (Traces) und **layout** (plus optional **config**) annimmt und mit plotly.js rendert. Damit deckst du Spektrum, Time-Domain, Scatter und 3D ab; du übergibst nur die passenden Traces/Layouts.
- **Spezialisierte Widgets** = Steuerung und Defaults: z. B. in der App oder in eigenen Komponenten ein **SpectrumPanel** (PlotlyGraph + Frequenz-/Pegel-Slider, Marker, RBW) und ein **OscilloscopePanel** (PlotlyGraph + Time-Base, Trigger, Kanalauswahl). Die spezialisierten Teile bauen nur die richtigen `data`/`layout` und füttern das generische Widget – oder sie sind eigene Vue-Komponenten, die intern ein PlotlyGraph verwenden und ihre eigenen Controls anbieten.

So bleibt die Plotly-Integration an einer Stelle (ein Widget), während Oszilloskop- und Spektrum-Bedienung getrennt und passend bleiben.

## PlotlyGraph (generisches Plot-Widget)

- **Props:** `data`, `layout`, `config`, `height`, `plotly_script_url` (optional)
- **Methoden:** `update_figure(data, layout?, config?)`, `update_from_figure(fig)` (fig = go.Figure, nutzt `to_plotly_json()`)
- **NumPy:** In `data`/Traces können `x`, `y`, `z` als **numpy.ndarray** übergeben werden; das Widget konvertiert sie intern zu Listen (schnell, typisch für DSP).
- **DSP-Plot-Varianten:** Entsprechung zu Plot/PlotXY/PlotScatter/PlotHistogram/PlotSpectrum siehe `app_builder/docs/plotly_graph_widget_spec.md` (Abschnitt Datentypen und DSP-Plot-Varianten).
- **Laden von plotly.js:** Standardmäßig von **CDN** (Internet nötig). Ohne `plotly_script_url` wird `https://cdn.plot.ly/plotly-2.27.0.min.js` geladen.
- **Offline:** Plotly lokal ausliefern und URL übergeben – dann keine Internetverbindung nötig (siehe unten).

```python
import numpy as np
import plotly.graph_objects as go
from lab_suite.widgets import PlotlyGraph

# Mit NumPy (z. B. nach FFT)
freq = np.fft.rfftfreq(1024, 1.0 / 44100)
mag = np.abs(np.fft.rfft(signal))
graph = PlotlyGraph(height="400px")
graph.update_figure([{"x": freq, "y": mag, "mode": "lines"}], layout={"yaxis": {"type": "log"}})

# Oder mit go.Figure
fig = go.Figure(data=[go.Scatter(x=[1,2,3], y=[2,1,2])], layout=dict(title="Test"))
graph.update_from_figure(fig)
```

**Offline-Betrieb:** Eine gemeinsame Kopie liegt in `lab_suite/widgets/static/plotly.min.js` und wird unter `/widgets-static/` bereitgestellt (alle Apps nutzen sie; Default im Layout). Einmal ausführen: `python -m app_builder.fetch_plotly_offline`. Optional pro App: eigene Kopie unter `static/` und `plotly_script_url="/static/plotly.min.js"`.

## Led (State-gesteuerte Anzeige)

- **Erscheinung nach State:** z. B. LED-Symbol mit Farben off (grau), on (grün), warning (orange), error (rot). Gut für Status-Anzeigen.
- **Props:** `state` (String oder Zahl), `label`, `size` (px).
- **State:** `'off'`|`'on'`|`'warning'`|`'error'` oder `0`|`1`|`2`|`3`.
- **Methode:** `set_state(state)` – z. B. aus Timer oder Event.

```python
from lab_suite.widgets import Led
led = Led(state="off", label="Status", size=20)
# später: led.set_state("on")  # oder led.set_state(2) für warning
```

## Rastergrafik und SVG-Icons in Vue-Widgets

**Ja, beides ist möglich** – ohne Build-Step, nur mit dem bestehenden .js-Template.

### Rastergrafik (PNG, GIF, …)

- Im Template ein normales `<img>` verwenden, `src` per **Prop** von Python übergeben.
- Die URL kann sein:
  - **Statische Datei:** Mit `ui.add_static_files('static', 'static')` Dateien bereitstellen, dann z. B. `src="/static/logo.png"` oder die URL als Prop durchreichen.
  - **Externe URL:** z. B. `https://example.com/bild.png`.
  - **Data-URL:** Base64-kodiertes Bild (z. B. `data:image/png;base64,...`) – möglich, aber vergrößert die übertragene Datenmenge.

Beispiel im Vue-Template:  
`<img v-if="imageSrc" :src="imageSrc" :alt="imageAlt" style="max-height:32px;" />`  
Von Python: `ImageIconDemo(image_src='/static/logo.png')` (nach `add_static_files`).

### SVG / Icon-Bibliotheken

- **Inline-SVG:** SVG-Markup (z. B. von [Heroicons](https://heroicons.com/), [Feather Icons](https://feathericons.com/)) direkt ins Template kopieren – kein „Import“, nur den `<svg>…</svg>`-Code einfügen. Farbe/Größe per `fill`, `style` oder `class` steuern.
- **SVG als externe Datei:** Wie Raster: `<img :src="iconUrl">` mit URL (z. B. CDN wie `https://unpkg.com/.../icon.svg`).
- Es wird **kein npm-Paket** benötigt; die Icons werden als Markup oder per URL eingebunden.

Demo-Widget **ImageIconDemo** zeigt beides: optionales Bild über Prop `image_src` und ein eingebautes Inline-SVG-Icon (Heroicons „speaker-wave“).

## Absolute Positionierung und z-index (Container + Overlay)

**Ja.** Widgets lassen sich in einem Container absolut positionieren und per `z-index` überlappen – z. B. für ein Link-Budget: Hintergrundbild (Funkstrecke Sender → Kanal → Empfänger), darauf Parameter-Widgets (Tx Power, Path Loss, …).

**Vorgehen in NiceGUI:**

1. **Container:** `ui.element('div')` mit festen Abmessungen und `position: relative`, optional `background-image: url(...)`.
2. **Kinder** im Container erzeugen und Referenzen halten.
3. **Pro Kind** `.style('position: absolute; left: …; top: …; z-index: …')` setzen (Angaben in `px` oder `%`). Höherer `z-index` liegt oben.

Beispiel:

```python
with ui.element('div').style(
    'position: relative; width: 700px; height: 220px; '
    'background: linear-gradient(90deg, #e8f4 0%, #c0d8 50%, #e8f4 100%); '
    'border: 1px solid #999; border-radius: 8px;'
) as container:
    tx_label = ui.label('Tx Power [dBm]')
    tx_input = ui.number('Tx', value=10)
    rx_label = ui.label('Rx (berechnet)')
    tx_label.style('position: absolute; left: 24px; top: 16px; z-index: 2;')
    tx_input.style('position: absolute; left: 24px; top: 44px; z-index: 2;')
    rx_label.style('position: absolute; right: 24px; top: 24px; z-index: 2;')
```

Statt Gradient kann `background-image: url("/static/link_budget.svg")` (nach `add_static_files`) verwendet werden.

**Animation:** Die Position kannst du jederzeit programmatisch ändern: im Timer- oder Event-Callback erneut `.style('position: absolute; left: …px; top: …px; …')` setzen und `.update()` aufrufen. So entstehen timer- oder eventgesteuerte Bewegungen (z. B. Symbol wandert Sender → Empfänger).
