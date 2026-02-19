# Widget: Markdown (mit LaTeX/KaTeX, Scroll, optional editierbar)

## Übersicht

Das **markdown**-Widget zeigt Markdown-Text mit LaTeX-Formeln an (NiceGUI `ui.markdown` mit `extras=['latex']`), in einem Scrollbereich mit konfigurierbarer Höhe. Optional kann es **editierbar** sein: dann wird unter dem Anzeige-Markdown eine Textarea für Studenten-Antworten angezeigt; der Inhalt liegt im State und kann persistiert werden.

## Einordnung in die Architektur

- **Wie andere Widgets:** Ein Eintrag in `WIDGET_DEFAULTS` (layout_model), State-Default in `WIDGET_STATE_DEFAULTS` (layout_schema), ein `elif widget_type == "markdown"` im Renderer. Keine neuen Abstraktionsebenen.
- **State:** `state[path_id]` = bei **nur Anzeige** optional der programmatisch gesetzte Markdown-Inhalt (App kann z. B. Datei laden und `state[path_id] = content` setzen); bei **editable** der Text der Studenten-Antwort (Textarea).
- **Programmatisches Laden:** App liest z. B. eine `.md`-Datei und setzt `state[path_id] = datei_inhalt` (oder ruft `widget_registry[path_id].set_content(...)` wenn das Widget in der Registry steht). Danach ggf. `on_state_change()` / UI-Update.
- **Editierbar:** Wenn `props.editable === true`, wird unter dem festen Markdown (aus `props.content`) eine Textarea gerendert; Änderungen schreiben in `state[path_id]` und lösen optional einen **change**-Callback aus (wie bei input/slider). Im Skeleton erscheint nur bei `editable` ein Callback-Stub.

## Props (Layout / Property-Editor)

| Prop | Typ | Bedeutung |
|------|-----|-----------|
| `content` | string | Initialer/fester Markdown-Text (Anzeige; bei editable = Aufgabentext). |
| `editable` | bool | `true` = Textarea für Antworten unter dem Markdown; State = Antworttext. |
| `placeholder` | string | Placeholder-Text der Textarea (nur bei editable). |
| `extras` | string / list | Markdown2-Extras, z. B. `"latex"` für LaTeX (Standard: latex + fenced-code-blocks, tables). |
| `height` | string | max-height des Scrollbereichs (z. B. `"300px"`). |

## Aufwand

- **Implementierung:** gering – ein neues Widget wie label/input: Defaults, State, Renderer-Zweig, optional Callback bei editable. Keine neuen Frameworks.
- **LaTeX:** NiceGUI nutzt markdown2 mit `extras=['latex']` (ggf. latex2mathml). Kein eigener KaTeX-Integration nötig.
- **Editierbar:** eine Textarea unter dem Markdown, gebunden an `state[path_id]` und an den bestehenden Callback-/State-Mechanismus.

## Verwendung

- **Nur Anzeige (z. B. Aufgabenstellung):** `content` im Layout setzen oder zur Laufzeit `state[path_id] = loaded_markdown` setzen; bei Verwendung der Registry `widget_registry[path_id].set_content(loaded_markdown)`.
- **Assignments mit Antworten:** `editable: true`, `content` = Aufgabentext; Student tippt in die Textarea → `state[path_id]` wird vom Renderer geschrieben, Session-Persistenz speichert den State (inkl. Antwort). Optional: change-Callback für sofortige Reaktion.
