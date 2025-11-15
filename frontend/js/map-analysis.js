// map-analysis.js
document.addEventListener("DOMContentLoaded", function() {
  const map = L.map("mapAnalysis").setView([19.1334,72.9133], 13);
  L.tileLayer("https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png", {
    maxZoom: 19
  }).addTo(map);

  const hospital = L.circle([19.1334,72.9133], {radius:50}).addTo(map);

  let isoLayer = null;
  let freqLayer = null;

  async function loadIsochrones() {
    try {
      const data = await fetch("/api/analysis/isochrones").then(r => r.json());
      if (isoLayer) map.removeLayer(isoLayer);
      isoLayer = L.geoJSON(data, {
        style: (feat) => {
          const val = feat.properties.value || feat.properties.range;
          // simple color by value
          if (val <= 3*60) return {color:"#fde725", fillOpacity:0.2};
          if (val <= 5*60) return {color:"#5dc963", fillOpacity:0.2};
          if (val <= 7*60) return {color:"#21918c", fillOpacity:0.2};
          return {color:"#3b528b", fillOpacity:0.2};
        }
      }).addTo(map);
    } catch (err) {
      console.error("isochrones failed", err);
    }
  }

  async function loadFrequency() {
    try {
      const data = await fetch("/api/analysis/frequency").then(r => r.json());
      if (freqLayer) map.removeLayer(freqLayer);
      freqLayer = L.geoJSON(data, {
        style: (feat) => {
          const c = feat.properties.count || 1;
          // color ramp: low -> gray, medium -> orange, high -> red
          let weight = Math.min(8, 1 + Math.log(1+c));
          let color = c > 4 ? "#c62828" : c > 2 ? "#ff8f00" : "#6e6e6e";
          return {color: color, weight: weight};
        }
      }).addTo(map);
      map.fitBounds(freqLayer.getBounds(), {padding:[20,20]});
    } catch (err) {
      console.error("frequency failed", err);
    }
  }

  window.analysisMap = {
    loadAnalysis: async () => {
      await loadIsochrones();
      await loadFrequency();
    }
  };

  // initial load
  window.analysisMap.loadAnalysis();
});
