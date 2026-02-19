// Banner – Vue-Komponente für Kommunikationstechnik-Optik (Funk/Signal, Verlauf, 3 Textfelder).
// Flex: volle Breite, Höhe über Prop. Keine Events (nur Anzeige).
export default {
  template: `
    <div class="kt-banner" :style="bannerStyle">
      <div class="kt-banner__waves" :style="wavesStyle" aria-hidden="true">
        <svg class="kt-banner__waves-svg" viewBox="0 0 200 40" preserveAspectRatio="none" style="width:100%;height:100%;opacity:0.25;">
          <path fill="none" stroke="currentColor" stroke-width="0.8" d="M0 20 Q25 5 50 20 T100 20 T150 20 T200 20" />
          <path fill="none" stroke="currentColor" stroke-width="0.6" d="M0 22 Q25 35 50 22 T100 22 T150 22 T200 22" />
          <path fill="none" stroke="currentColor" stroke-width="0.5" d="M0 18 Q50 28 100 18 T200 18" />
        </svg>
      </div>
      <div class="kt-banner__content" :style="contentStyle">
        <span class="kt-banner__text" :style="text1Style">{{ text1 }}</span>
        <span class="kt-banner__text" :style="text2Style">{{ text2 }}</span>
        <span class="kt-banner__text" :style="text3Style">{{ text3 }}</span>
      </div>
      <div class="kt-banner__antenna" :style="antennaStyle" aria-hidden="true">
        <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.2" style="width:100%;height:100%;opacity:0.4;">
          <path d="M12 2v4M12 18v4M4 12h4M18 12h4M6.34 6.34l2.83 2.83M14.83 14.83l2.83 2.83M6.34 17.66l2.83-2.83M14.83 9.17l2.83-2.83" />
          <circle cx="12" cy="12" r="2.5" />
        </svg>
      </div>
    </div>
  `,
  props: {
    text1: { type: String, default: "" },
    text2: { type: String, default: "" },
    text3: { type: String, default: "" },
    height: { type: String, default: "80px" },
    font_family: { type: String, default: "" },
    font_size1: { type: String, default: "" },
    font_size2: { type: String, default: "" },
    font_size3: { type: String, default: "" },
    text_color: { type: String, default: "" },
    gradient_start: { type: String, default: "#0d47a1" },
    gradient_end: { type: String, default: "#1565c0" },
  },
  computed: {
    bannerStyle() {
      const h = this.height && this.height.trim() ? this.height.trim() : "80px";
      const g1 = this.gradient_start && this.gradient_start.trim() ? this.gradient_start.trim() : "#0d47a1";
      const g2 = this.gradient_end && this.gradient_end.trim() ? this.gradient_end.trim() : "#1565c0";
      return {
        minHeight: h,
        height: h,
        width: "100%",
        boxSizing: "border-box",
        position: "relative",
        display: "flex",
        alignItems: "center",
        justifyContent: "space-between",
        padding: "0 1rem 0 1rem",
        background: `linear-gradient(105deg, ${g1} 0%, ${g2} 50%, #0a3d91 100%)`,
        color: "rgba(255,255,255,0.95)",
        overflow: "hidden",
      };
    },
    wavesStyle() {
      return {
        position: "absolute",
        left: 0,
        right: 0,
        bottom: 0,
        height: "50%",
        pointerEvents: "none",
        color: "rgba(255,255,255,0.5)",
      };
    },
    contentStyle() {
      return {
        position: "relative",
        zIndex: 1,
        display: "flex",
        alignItems: "center",
        justifyContent: "flex-start",
        gap: "1.5rem",
        flexWrap: "wrap",
        flex: "1 1 auto",
      };
    },
    antennaStyle() {
      return {
        position: "relative",
        zIndex: 1,
        width: "32px",
        height: "32px",
        flexShrink: 0,
        color: "rgba(255,255,255,0.6)",
      };
    },
    text1Style() {
      return this._textStyle(this.font_size1, "1.1rem", "bold");
    },
    text2Style() {
      return this._textStyle(this.font_size2, "1rem", "normal");
    },
    text3Style() {
      return this._textStyle(this.font_size3, "1.25rem", "bold");
    },
  },
  methods: {
    _textStyle(fontSize, defaultSize, defaultWeight) {
      const s = { fontSize: (fontSize && fontSize.trim()) ? fontSize.trim() : defaultSize, fontWeight: defaultWeight || "normal" };
      if (this.font_family && this.font_family.trim()) s.fontFamily = this.font_family.trim();
      if (this.text_color && this.text_color.trim()) s.color = this.text_color.trim();
      return s;
    },
  },
};
