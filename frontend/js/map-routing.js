// map-routing.js
document.addEventListener("DOMContentLoaded", function() {
  // initialize map and expose simple API on window.routingMap
  const map = L.map("mapRouting").setView([19.1334,72.9133], 14);
  L.tileLayer("https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png", {
    maxZoom: 19
  }).addTo(map);

  const hospitalMarker = L.marker([19.1334,72.9133]).addTo(map).bindPopup("IITB Hospital");

  let routeLayer = null;
  let animMarker = null;
  let animInterval = null;

  function drawRoute(geojson) {
    if (routeLayer) { map.removeLayer(routeLayer); routeLayer = null; }
    if (animMarker) { map.removeLayer(animMarker); animMarker = null; clearInterval(animInterval); }

    const coords = geojson.features[0].geometry.coordinates;
    const latlngs = coords.map(c => [c[1], c[0]]);
    routeLayer = L.polyline(latlngs, {color:"blue", weight:4}).addTo(map);
    map.fitBounds(routeLayer.getBounds(), {padding:[20,20]});

    // animate marker along route (simple)
    let idx = 0;
    animMarker = L.circleMarker(latlngs[0], {radius:7, color:"red"}).addTo(map);
    animInterval = setInterval(() => {
      idx++;
      if (idx >= latlngs.length) { clearInterval(animInterval); return; }
      animMarker.setLatLng(latlngs[idx]);
    }, 80);
  }

  window.routingMap = {
    showRoute: drawRoute
  };
});
