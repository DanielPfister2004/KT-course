"""
User-Template: Kern- und Fachlogik für die Übung.

Hier lösen Sie die eigentliche Fach-Aufgabe. Die GUI liefert Parameter über get()
und zeigt Ergebnisse über set(); die Zuordnung Widget ↔ fachliche Größe erfolgt
über die User-ID im Layout (SEMANTIC_BINDING wird daraus automatisch befüllt).

Stand get() / set() / update_plot():
- get(key) und set(key, value) sind vollständig implementiert.
- get(key): Liest den Wert aus dem State (key = User-ID aus dem Layout).
- set(key, value): Schreibt in State und aktualisiert Output-Widgets (LED: set_state,
  VU-Meter: set_value), sofern die path_id in der Widget-Registry steht.
- update_plot(key, data, layout=None): Aktualisiert ein Plotly-Widget (user_id = key).
- Voraussetzung: Aufruf im GUI-Kontext (z. B. aus user_callbacks.py oder aus einem
  ui.timer), damit ui.context.client.state und widget_registry verfügbar sind.
- Wenn SEMANTIC_BINDING korrekt befüllt ist (user_id pro Widget gesetzt), reicht
  get("power"), set("led_status", "on"), update_plot("sine_plot", data) etc.

Timer: Die App startet einen Timer (einstellbare Rate, z. B. 10 Hz) und ruft
timer_tick() in diesem Modul auf, falls vorhanden. So können Plots/Logik periodisch
laufen, unabhängig von Button-Callbacks.

Performance: ENABLE_PERF_STATS=True oder DEBUG_PERF=1 aktiviert Laufzeit-Messung
(perf_counter) und optional Prozess-CPU (psutil). Budget = Timer-Intervall;
Headroom = verbleibende Zeit für DSP pro Tick.
"""
from __future__ import annotations

# Zugriff auf die GUI über fachliche Größen (User-IDs aus dem Layout)
from .._core import gui_binding

import math
import sys
global probabilities
probabilities = []

def _node_label(node: tuple) -> str:
    """Knoten-Beschriftung: Blatt 'x' (0.25) oder innerer Knoten [0.50]."""
    if node[0] is not None:
        s = repr(node[0])
        return f"{s} ({node[1]:.2f})"
    return f"[{node[1]:.2f}]"


def _huffman_tree_ascii(node: tuple, prefix: str = "", is_tail: bool = True, is_root: bool = True) -> list[str]:
    """Rekursive ASCII-Darstellung: node = (symbol, prob) für Blatt, (None, prob, left, right) für innere Knoten."""
    label = _node_label(node)
    if is_root:
        lines = [label]
    else:
        lines = [prefix + ("└── " if is_tail else "├── ") + label]
    if len(node) >= 4:
        _, _, left, right = node
        children = [c for c in (left, right) if c is not None]
        ext = "    " if is_tail else "│   "
        for i, child in enumerate(children):
            is_last = i == len(children) - 1
            lines.extend(_huffman_tree_ascii(child, prefix + ext, is_last, is_root=False))
    return lines


def _build_huffman_tree(freq: list[tuple], probabilities: list[float]) -> tuple:
    """Baut den Huffman-Baum aus (symbol, prob)-Blättern. Rückgabe: Wurzel-Knoten (symbol, prob) oder (None, prob, left, right)."""
    nodes = [(sym, p) for (sym, _), p in zip(freq, probabilities)]
    if len(nodes) == 1:
        return nodes[0]
    while len(nodes) > 1:
        nodes.sort(key=lambda n: n[1])
        left, right = nodes[0], nodes[1]
        prob_sum = left[1] + right[1]
        internal = (None, prob_sum, left, right)
        nodes = [internal] + nodes[2:]
    return nodes[0]


class HuffmanCode:
    def __init__(self, probability):
        self.probability = probability

    def position(self, value, index):
        for j in range(len(self.probability)):
            if value >= self.probability[j]:
                return j
        return index - 1

    def characteristics_huffman_code(self, code):
        length_of_code = [len(k) for k in code]
        mean_length = sum([a * b for a, b in zip(length_of_code, self.probability)])
        print("Average length of the code: %f" % mean_length)

    def compute_code(self):
        num = len(self.probability)
        huffman_code = [''] * num

        for i in range(num - 2):
            val = self.probability[num - i - 1] + self.probability[num - i - 2]
            if huffman_code[num - i - 1] != '' and huffman_code[num - i - 2] != '':
                huffman_code[-1] = ['1' + symbol for symbol in huffman_code[-1]]
                huffman_code[-2] = ['0' + symbol for symbol in huffman_code[-2]]
            elif huffman_code[num - i - 1] != '':
                huffman_code[num - i - 2] = '0'
                huffman_code[-1] = ['1' + symbol for symbol in huffman_code[-1]]
            elif huffman_code[num - i - 2] != '':
                huffman_code[num - i - 1] = '1'
                huffman_code[-2] = ['0' + symbol for symbol in huffman_code[-2]]
            else:
                huffman_code[num - i - 1] = '1'
                huffman_code[num - i - 2] = '0'

            position = self.position(val, i)
            probability = self.probability[0 : (len(self.probability) - 2)]
            probability.insert(position, val)
            if isinstance(huffman_code[num - i - 2], list) and isinstance(huffman_code[num - i - 1], list):
                complete_code = huffman_code[num - i - 1] + huffman_code[num - i - 2]
            elif isinstance(huffman_code[num - i - 2], list):
                complete_code = huffman_code[num - i - 2] + [huffman_code[num - i - 1]]
            elif isinstance(huffman_code[num - i - 1], list):
                complete_code = huffman_code[num - i - 1] + [huffman_code[num - i - 2]]
            else:
                complete_code = [huffman_code[num - i - 2], huffman_code[num - i - 1]]

            huffman_code = huffman_code[0 : (len(huffman_code) - 2)]
            huffman_code.insert(position, complete_code)

        huffman_code[0] = ['0' + symbol for symbol in huffman_code[0]]
        huffman_code[1] = ['1' + symbol for symbol in huffman_code[1]]

        if len(huffman_code[1]) == 0:
            huffman_code[1] = '1'

        count = 0
        final_code = [''] * num

        for i in range(2):
            for j in range(len(huffman_code[i])):
                final_code[count] = huffman_code[i][j]
                count += 1

        final_code = sorted(final_code, key=len)
        return final_code




def run_domain_logic() -> None:

    string =  gui_binding.get("my_text")

    freq = {}
    for c in string:
        if c in freq:
            freq[c] += 1
        else:
            freq[c] = 1

    freq = sorted(freq.items(), key=lambda x: x[1], reverse=True)
    length = len(string)

    probabilities = [float("{:.2f}".format(frequency[1]/length)) for frequency in freq]
    probabilities = sorted(probabilities, reverse=True)

    huffmanClassObject = HuffmanCode(probabilities)
    P = probabilities

    huffman_code = huffmanClassObject.compute_code()

    # Tabelle als einen String bauen und einmal setzen (jedes set() überschreibt die Box)
    gui_binding.clear_markdown('code_table')
    lines = ['\n Char | Huffman code\n   ', '----------------------\  ']
    for id, char in enumerate(freq):
        if huffman_code[id] == '':
            lines.append(' %-4r |%12s' % (char[0], 1))
        else:
            lines.append(' %-4r |%12s' % (char[0], huffman_code[id]))
    gui_binding.set('code_table', '  \n'.join(lines))

    # Codebaum (ASCII) im dritten Markdown-Widget (user_id=code_tree) ausgeben
    gui_binding.clear_markdown('code_tree')
    try:
        root = _build_huffman_tree(freq, probabilities)
        tree_lines = _huffman_tree_ascii(root)
        gui_binding.set('code_tree', '\n'.join(tree_lines))
    except Exception:
        gui_binding.set('code_tree', '(Baum konnte nicht erzeugt werden)')

    huffmanClassObject.characteristics_huffman_code(huffman_code)


def solve_task() -> None:
    """
    Einstieg für die eigentliche Fach-Aufgabe.
    Wird typisch aus user_callbacks.py oder einem Timer aufgerufen.
    """
    print("Solve Task")
    run_domain_logic()

