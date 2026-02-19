"""
lab_suite/widgets – Wiederverwendbare Custom-Widgets (Vue/JS + NiceGUI Element).

Jedes Widget lebt in einer eigenen Datei:
  - <name>.py   → Python-Klasse (Element mit component='<name>.js')
  - <name>.js   → Vue/JS-Frontend (oder .vue wenn gebaut)

Verwendung in einer App:
  from lab_suite.widgets import GainControlVue
  gain = GainControlVue('Gain', min_=0, max_=10, value=1, on_change=...)
"""
from .banner import Banner
from .gain_control import GainControlVue
from .image_icon_demo import ImageIconDemo
from .led import Led
from .plotly_graph import PlotlyGraph
from .vu_meter import VuMeter

__all__ = ["Banner", "GainControlVue", "ImageIconDemo", "Led", "PlotlyGraph", "VuMeter"]
