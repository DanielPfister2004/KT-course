// Generisches Plotly-Graph-Widget – eine Vue-Komponente für alle Modi (Spektrum, Oszilloskop, Scatter, 3D).
// Lädt plotly.js bei Bedarf von CDN (NiceGUI setzt window.Plotly oft nicht).
const PLOTLY_CDN = "https://cdn.plot.ly/plotly-2.27.0.min.js";

export default {
  template: `
    <div class="plotly-graph-wrapper" :style="wrapperStyle">
      <div v-if="!plotlyReady" class="plotly-placeholder" style="position:absolute;inset:0;display:flex;align-items:center;justify-content:center;background:#e8e8f0;color:#666;font-size:14px;">Plotly wird geladen…</div>
      <div ref="container" class="plotly-graph" :style="containerStyle"></div>
    </div>
  `,
  props: {
    data: { type: Array, default: () => [] },
    layout: { type: Object, default: () => ({}) },
    config: { type: Object, default: () => ({ responsive: true }) },
    height: { type: String, default: "400px" },
    /** Leer = CDN (Internet). Für Offline: z. B. "/static/plotly.min.js" (Datei lokal ausliefern). */
    plotlyScriptUrl: { type: String, default: "" },
    /** Bei true: nur Trace-Daten (x/y) per restyle aktualisieren, kein voller react – flüssiger bei Animation. */
    restyleOnly: { type: Boolean, default: false },
  },
  data() {
    return { plotlyReady: false, loadStarted: false };
  },
  computed: {
    wrapperStyle() {
      return `width: 100%; height: ${this.height}; min-height: 200px; position: relative;`;
    },
    containerStyle() {
      return `width: 100%; height: 100%; min-height: 200px;`;
    },
  },
  mounted() {
    if (typeof window === "undefined") return;
    if (window.Plotly) {
      this.plotlyReady = true;
      this.$nextTick(() => this.draw());
      return;
    }
    this.loadPlotly();
  },
  methods: {
    loadPlotly() {
      if (this.loadStarted) return;
      this.loadStarted = true;
      const script = document.createElement("script");
      script.src = (this.plotlyScriptUrl && this.plotlyScriptUrl.trim()) ? this.plotlyScriptUrl.trim() : PLOTLY_CDN;
      script.onload = () => {
        this.plotlyReady = true;
        this.$nextTick(() => this.draw());
      };
      script.onerror = () => {
        this.loadStarted = false;
        console.warn("PlotlyGraph: CDN load failed");
      };
      document.head.appendChild(script);
    },
    async draw() {
      const el = this.$refs.container;
      if (!el || !window.Plotly) return;
      const data = Array.isArray(this.data) && this.data.length ? this.data : [{ x: [], y: [], mode: "lines" }];
      const layout = this.layout && typeof this.layout === "object" ? { ...this.layout } : {};
      const config = this.config && typeof this.config === "object" ? this.config : { responsive: true };
      const t0 = typeof performance !== "undefined" ? performance.now() : 0;
      try {
        if (!el.data) {
          await window.Plotly.newPlot(el, data, layout, config);
        } else if (this.restyleOnly && data.length > 0) {
          const xArr = data.map((t) => t.x || []);
          const yArr = data.map((t) => t.y || []);
          await window.Plotly.restyle(el, { x: xArr, y: yArr });
          // Achsen fix halten: Plotly reaktiviert bei restyle oft autorange – relayout mit flachen Keys
          const relayoutArg = {};
          if (layout.xaxis) {
            if (layout.xaxis.range) relayoutArg["xaxis.range"] = layout.xaxis.range;
            if (layout.xaxis.autorange === false) relayoutArg["xaxis.autorange"] = false;
          }
          if (layout.yaxis) {
            if (layout.yaxis.range) relayoutArg["yaxis.range"] = layout.yaxis.range;
            if (layout.yaxis.autorange === false) relayoutArg["yaxis.autorange"] = false;
          }
          if (Object.keys(relayoutArg).length) await window.Plotly.relayout(el, relayoutArg);
        } else {
          await window.Plotly.react(el, data, layout, config);
        }
        if (typeof window !== "undefined" && t0 > 0) {
          const durationMs = performance.now() - t0;
          window.__lastPlotDurationMs = durationMs;
          if (typeof console !== "undefined" && console.log) {
            console.log("[PlotlyGraph] draw:", durationMs.toFixed(2), "ms");
          }
        }
      } catch (err) {
        console.warn("PlotlyGraph draw:", err);
      }
    },
  },
  watch: {
    data: { handler() { if (this.plotlyReady) this.$nextTick(() => this.draw()); }, deep: true },
    layout: { handler() { if (this.plotlyReady && !this.restyleOnly) this.$nextTick(() => this.draw()); }, deep: true },
    restyleOnly: { handler() { if (this.plotlyReady) this.$nextTick(() => this.draw()); } },
  },
};
