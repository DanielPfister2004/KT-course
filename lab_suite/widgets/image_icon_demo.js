// Demo: Rastergrafik (img) + Inline-SVG-Icon in einem Vue-Widget
// Zeigt: Bild per URL-Prop, SVG direkt im Template (z. B. von Heroicons kopiert)
export default {
  template: `
    <div class="image-icon-demo" style="display:inline-flex; align-items:center; gap:8px; padding:6px; border:1px solid #ccc; border-radius:6px;">
      <!-- Rastergrafik: src von Python (z. B. /static/foo.png oder Data-URL) -->
      <img v-if="imageSrc" :src="imageSrc" :alt="imageAlt" style="max-height:32px; max-width:64px; object-fit:contain;" />
      <!-- Inline-SVG (z. B. Heroicons "speaker-wave" – direkt ins Template kopiert) -->
      <svg v-if="showIcon" xmlns="http://www.w3.org/2000/svg" viewBox="0 0 24 24" fill="currentColor" style="width:24px; height:24px; flex-shrink:0;">
        <path d="M13.5 4.06c0-1.336-1.616-2.005-2.56-1.06l-4.5 4.5H4.508c-1.141 0-2.318.664-2.66 1.905A9.76 9.76 0 0 1 1.5 12c0 .898.121 1.768.35 2.595.341 1.24 1.518 1.905 2.659 1.905h1.93l4.5 4.5c.945.945 2.561.276 2.561-1.06V4.06Zm5.084 1.046a.75.75 0 0 1 1.06 0c3.808 3.807 3.808 9.98 0 13.788a.75.75 0 0 1-1.06-1.06 8.25 8.25 0 0 0 0-11.668.75.75 0 0 1 0-1.06Z" />
        <path d="M15.932 7.757a.75.75 0 0 1 1.061 0 6 6 0 0 1 0 8.486.75.75 0 0 1-1.06-1.061 4.5 4.5 0 0 0 0-6.364.75.75 0 0 1 0-1.06Z" />
      </svg>
      <span v-if="label" style="font-size:0.9em;">{{ label }}</span>
    </div>
  `,
  props: {
    imageSrc: { type: String, default: "" },
    imageAlt: { type: String, default: "Image" },
    showIcon: { type: Boolean, default: true },
    label: { type: String, default: "" },
  },
};
