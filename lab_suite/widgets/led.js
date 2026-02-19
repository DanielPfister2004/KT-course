// LED-Symbol: Erscheinung per State (off / on / warning / error) steuerbar
export default {
  template: `
    <div class="led-widget" :style="containerStyle">
      <div
        class="led-dot"
        :style="{ backgroundColor: color, width: sizePx, height: sizePx, borderRadius: '50%', boxShadow: glow }"
      ></div>
      <span v-if="label" class="led-label">{{ label }}</span>
    </div>
  `,
  props: {
    state: { type: [String, Number], default: "off" },
    label: { type: String, default: "" },
    size: { type: [String, Number], default: 16 },
  },
  computed: {
    normalizedState() {
      const s = this.state;
      if (typeof s === "number") {
        if (s <= 0) return "off";
        if (s === 1) return "on";
        if (s === 2) return "warning";
        return "error";
      }
      const t = String(s).toLowerCase();
      if (["off", "on", "warning", "error"].includes(t)) return t;
      return "off";
    },
    color() {
      const map = { off: "#444", on: "#0c0", warning: "#fa0", error: "#f00" };
      return map[this.normalizedState] || map.off;
    },
    glow() {
      if (this.normalizedState === "off") return "none";
      return `0 0 6px ${this.color}, 0 0 10px ${this.color}40`;
    },
    sizePx() {
      const n = typeof this.size === "number" ? this.size : parseInt(this.size, 10) || 16;
      return `${n}px`;
    },
    containerStyle() {
      return "display: inline-flex; align-items: center; gap: 6px;";
    },
  },
};
