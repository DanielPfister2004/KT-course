# lab_suite/app_builder

Kern des App-Builders: **JSON-Layout-Format**, **Modell-State** und **Callback-Skeleton** als Schnittstelle zum User-Code. Später: visueller Builder (Drag & Drop), der Layouts exportiert und Skeleton-Code erzeugt.

## Ordnerstruktur

```
app_builder/
├── README.md           # Diese Datei
├── layout_schema.py    # Dataclasses für Layout, Pfad-IDs, Validierung
├── layout_format.md    # Spezifikation des JSON-Layout-Formats
├── skeleton.py         # Erzeugt callback_skeleton.py + Modell aus Layout-JSON
└── __init__.py
```

## Verwendung (Ziel: development_app)

1. **Layout** in `development_app/layout.json` definieren (oder vom Builder exportieren).
2. **Skeleton erzeugen:** `python -m app_builder.skeleton development_app/layout.json --out development_app/`
3. **User-Code:** In `callback_skeleton.py` die leeren Callbacks mit Logik füllen; Zugriff auf `model.state` und ggf. Services.
4. **App starten:** `development_app/app.py` lädt Layout + Modell, baut die GUI aus dem Layout und verbindet die Callbacks.

## Schnittstelle zum User-Code

- **Modell:** Ein Dict `model.state` mit Keys = Pfad-IDs (z. B. `"top.run"`, `"top.gain_block.gain"`). Typ und Default pro Widget im Layout definiert.
- **Callbacks:** Pro Widget mit Event ein Eintrag im Skeleton (z. B. `def on_top_run_change(value: bool): ...`). Der User füllt nur den Rumpf.
- **Persistenz:** `model.state` wird als JSON gespeichert/geladen (Session).

Siehe `layout_format.md` und `skeleton.py`.
