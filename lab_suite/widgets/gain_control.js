// GainControl – Vue-Komponente für NiceGUI (lab_suite/widgets)
// EINZIGE Quelle: lab_suite/widgets/gain_control.js (keine Duplikate).
// Emittiert NUR in: onInput (beim Ziehen) und reset() (Button). Natives @change (Maus loslassen) wird mit .stop abgefangen, damit NiceGUI kein 1.0 nachschiebt.
// Einmal nach Änderung: Browser mit deaktiviertem Cache neu laden.
export default {
  template: `
    <div class="gain-control" style="background:#ccc; padding:8px; border-radius:6px; display:inline-flex; align-items:center; gap:8px;">
      <span>{{ label }}</span>
      <span>{{ displayValue }}</span>
      <input
        type="range"
        :min="min"
        :max="max"
        :value="internalValue"
        step="0.01"
        style="min-width:80px;"
        @input="onInput"
        @change.stop="onNativeChange"
      />
      <button type="button" @click="reset">Reset</button>
    </div>
  `,
  props: {
    label: { type: String, default: 'Gain' },
    min: { type: Number, default: 0 },
    max: { type: Number, default: 10 },
    value: { type: Number, default: 1 },
  },
  data() {
    return {
      internalValue: this.value,
    };
  },
  computed: {
    displayValue() {
      return this.internalValue.toFixed(2);
    },
  },
  watch: {
    value(v) {
      const num = Number(v);
      if (Number.isNaN(num)) return;
      if (num === 1 && this.internalValue !== 1) return;
      this.internalValue = num;
    },
  },
  methods: {
    onInput(ev) {
      const v = parseFloat(ev.target.value);
      if (Number.isNaN(v)) return;
      this.internalValue = v;
      this._emitValue(v);
    },
    onNativeChange(ev) {
      // Natives change (Maus loslassen) stoppen – sonst leitet NiceGUI es weiter und sendet 1.0
      ev.stopPropagation();
      ev.preventDefault();
    },
    reset() {
      this.internalValue = 1;
      this._emitValue(1);
    },
    _emitValue(v) {
      const num = Number(v);
      if (!Number.isNaN(num)) this.$emit('change', num);
    },
  },
};
