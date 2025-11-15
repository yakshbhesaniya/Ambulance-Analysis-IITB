// helpers.js
const API_BASE = "/api";

function fetchJSON(url, opts) {
  return fetch(url, opts).then(r => {
    if (!r.ok) return r.json().then(j => { throw j; });
    return r.json();
  });
}

function showLastTrip(data) {
  const el = document.getElementById("lastTrip");
  el.textContent = JSON.stringify(data, null, 2);
}

function lngLatArrayToLatLngs(coords) {
  // coords from ORS: [ [lng,lat], [lng,lat], ... ]
  return coords.map(c => [c[1], c[0]]);
}
