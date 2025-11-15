// map-analysis.js
document.addEventListener("DOMContentLoaded", function() {
  // IITB Hospital coordinates
  const HOSPITAL_LAT = 19.1309507;
  const HOSPITAL_LNG = 72.9146062;
  const map = L.map("mapAnalysis").setView([HOSPITAL_LAT, HOSPITAL_LNG], 13);
  L.tileLayer("https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png", {
    maxZoom: 19,
    attribution: '&copy; <a href="https://www.openstreetmap.org/copyright">OpenStreetMap</a>'
  }).addTo(map);

  // Hospital marker
  const hospitalMarker = L.marker([HOSPITAL_LAT, HOSPITAL_LNG]).addTo(map)
    .bindPopup("IITB Hospital");

  let isoLayer = null;
  let freqLayer = null;
  let maxFrequency = 1;

  async function loadIsochrones() {
    try {
      const response = await fetch("/api/analysis/isochrones");
      
      // Check if response is ok before parsing JSON
      if (!response.ok) {
        let errorData = {};
        try {
          errorData = await response.json();
        } catch (e) {
          errorData = { error: `HTTP ${response.status}: ${response.statusText}` };
        }
        console.error("Isochrones API error:", errorData);
        alert(`Failed to load isochrones: ${errorData.error || errorData.detail || 'Unknown error'}`);
        return;
      }
      
      const data = await response.json();
      
      if (isoLayer) map.removeLayer(isoLayer);
      
      if (!data || !data.features || data.features.length === 0) {
        console.warn("No isochrone data received", data);
        // Don't show alert for empty data, just log it
        return;
      }

      // Color scheme for different time ranges (2, 3, 5, 7 minutes)
      const colorMap = {
        120: { color: "#fde725", fillColor: "#fde725", fillOpacity: 0.4, weight: 2 },   // 2 min - yellow
        180: { color: "#5dc963", fillColor: "#5dc963", fillOpacity: 0.4, weight: 2 },   // 3 min - green
        300: { color: "#21918c", fillColor: "#21918c", fillOpacity: 0.4, weight: 2 },   // 5 min - teal
        420: { color: "#3b528b", fillColor: "#3b528b", fillOpacity: 0.4, weight: 2 }    // 7 min - blue
      };

      isoLayer = L.geoJSON(data, {
        style: (feat) => {
          const range = feat.properties.value || feat.properties.range || 0;
          // Find closest matching range
          let style = colorMap[120]; // default (2 min)
          const ranges = [120, 180, 300, 420]; // 2, 3, 5, 7 minutes in seconds
          for (let r of ranges) {
            if (range <= r) {
              style = colorMap[r];
              break;
            }
          }
          return style;
        },
        onEachFeature: (feature, layer) => {
          const range = feature.properties.value || feature.properties.range || 0;
          const minutes = Math.round(range / 60);
          layer.bindPopup(`Within ${minutes} minutes from IITB Hospital`);
        }
      }).addTo(map);
      
      // Fit bounds to isochrones
      if (isoLayer.getBounds().isValid()) {
        map.fitBounds(isoLayer.getBounds(), {padding: [20, 20]});
      }
    } catch (err) {
      console.error("isochrones failed", err);
      // Handle different types of errors
      if (err.name === 'TypeError' && err.message.includes('fetch')) {
        alert("Failed to connect to server. Please make sure the server is running.");
      } else {
        alert("Failed to load isochrones: " + (err.message || err.toString()));
      }
    }
  }

  async function loadFrequency() {
    try {
      const data = await fetch("/api/analysis/frequency").then(r => r.json());
      if (freqLayer) map.removeLayer(freqLayer);
      
      if (!data || !data.features || data.features.length === 0) {
        console.warn("No frequency data received");
        return;
      }

      // Calculate max frequency for color scaling
      maxFrequency = 1;
      data.features.forEach(feat => {
        const count = feat.properties.count || 0;
        if (count > maxFrequency) maxFrequency = count;
      });

      freqLayer = L.geoJSON(data, {
        style: (feat) => {
          const c = feat.properties.count || 1;
          const normalized = c / maxFrequency;
          
          // Color gradient: gray (low) -> yellow -> orange -> red (high)
          let color, weight;
          if (normalized >= 0.7) {
            color = "#c62828"; // Dark red - very frequent
            weight = 8;
          } else if (normalized >= 0.5) {
            color = "#e53935"; // Red - frequent
            weight = 6;
          } else if (normalized >= 0.3) {
            color = "#ff8f00"; // Orange - moderate
            weight = 4;
          } else if (normalized >= 0.15) {
            color = "#ffb300"; // Yellow - less frequent
            weight = 3;
          } else {
            color = "#6e6e6e"; // Gray - rarely used
            weight = 2;
          }
          
          return {
            color: color,
            weight: weight,
            opacity: 0.8
          };
        },
        onEachFeature: (feature, layer) => {
          const count = feature.properties.count || 0;
          layer.bindPopup(`Route frequency: ${count} trip(s)`);
        }
      }).addTo(map);
      
      // Fit bounds to frequency data if available
      if (freqLayer.getBounds().isValid()) {
        const bounds = freqLayer.getBounds();
        // Only adjust if we have valid bounds and they're not too small
        if (bounds.getNorth() - bounds.getSouth() > 0.001) {
          map.fitBounds(bounds, {padding: [20, 20]});
        }
      }
    } catch (err) {
      console.error("frequency failed", err);
      alert("Failed to load frequency analysis: " + err.message);
    }
  }

  window.analysisMap = {
    loadAnalysis: async () => {
      await loadIsochrones();
      await loadFrequency();
    },
    map: map
  };

  // initial load
  window.analysisMap.loadAnalysis();
});
