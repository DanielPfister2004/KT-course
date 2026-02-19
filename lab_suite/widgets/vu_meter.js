// VU-Meter – analoge Anzeige (Skala + Nadel), rein SVG/CSS im Template
// value: 0..1 (oder nutze min/max). Nadel dreht von links (-90°) nach rechts (+90°).
export default {
  template: `
    <div class="vu-meter" :style="containerStyle">
      <svg viewBox="0 0 120 70" class="vu-svg" preserveAspectRatio="xMidYMid meet" style="max-width:100%; height:auto;">
        <!-- Skala: Halbkreis-Bogen -->
        <path
          d="M 20 60 A 40 40 0 0 1 100 60"
          fill="none"
          stroke="#333"
          stroke-width="2"
        />
        <!-- Skalenstriche (optional) -->
        <line x1="20" y1="60" x2="20" y2="55" stroke="#333" stroke-width="1"/>
        <line x1="60" y1="25" x2="60" y2="30" stroke="#333" stroke-width="1"/>
        <line x1="100" y1="60" x2="100" y2="55" stroke="#333" stroke-width="1"/>
        <!-- Nadel: von Mitte unten, Länge 36, Rotation um (value → Winkel) -->
        <line
          x1="60"
          y1="60"
          :x2="needleX"
          :y2="needleY"
          stroke="#c00"
          stroke-width="2"
          stroke-linecap="round"
        />
        <!-- Nadel-Punkt (Mittelpunkt) -->
        <circle cx="60" cy="60" r="3" fill="#333"/>
      </svg>
      <div class="vu-value" v-if="showValue">{{ displayValue }}</div>
    </div>
  `,
  props: {
    value: { type: Number, default: 0 },
    min: { type: Number, default: 0 },
    max: { type: Number, default: 1 },
    showValue: { type: Boolean, default: true },
    width: { type: String, default: '120px' },
    height: { type: String, default: '80px' },
  },
  computed: {
    normalized() {
      const v = this.value;
      const lo = this.min;
      const hi = this.max;
      if (hi <= lo) return 0;
      return Math.max(0, Math.min(1, (v - lo) / (hi - lo)));
    },
    angleDeg() {
      return -90 + this.normalized * 180;
    },
    needleX() {
      const deg = (this.angleDeg * Math.PI) / 180;
      const len = 36;
      return 60 + len * Math.cos(deg);
    },
    needleY() {
      const deg = (this.angleDeg * Math.PI) / 180;
      const len = 36;
      return 60 - len * Math.sin(deg);
    },
    displayValue() {
      return this.value.toFixed(2);
    },
    containerStyle() {
      return `width:${this.width}; height:${this.height};`;
    },
  },
};
