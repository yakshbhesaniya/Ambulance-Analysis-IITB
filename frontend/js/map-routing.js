// map-routing.js
document.addEventListener("DOMContentLoaded", function() {
  // initialize map and expose simple API on window.routingMap
  // IITB Hospital coordinates
  const HOSPITAL_LAT = 19.1309507;
  const HOSPITAL_LNG = 72.9146062;
  const map = L.map("mapRouting").setView([HOSPITAL_LAT, HOSPITAL_LNG], 14);
  L.tileLayer("https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png", {
    maxZoom: 19,
    attribution: '&copy; <a href="https://www.openstreetmap.org/copyright">OpenStreetMap</a>'
  }).addTo(map);

  // Hospital marker with default icon
  const hospitalMarker = L.marker([HOSPITAL_LAT, HOSPITAL_LNG]).addTo(map).bindPopup("IITB Hospital");

  // Create ambulance icon with error handling
  const ambulanceIcon = L.icon({
    iconUrl: '/frontend/images/ambulance.png',
    iconSize: [40, 40],
    iconAnchor: [20, 20],
    popupAnchor: [0, -20],
    errorIconUrl: 'https://raw.githubusercontent.com/pointhi/leaflet-color-markers/master/img/marker-icon-blue.png'
  });
  
  // Fallback if ambulance icon fails to load
  let ambulanceIconLoaded = true;
  const img = new Image();
  img.onerror = () => {
    ambulanceIconLoaded = false;
    console.warn("Ambulance icon failed to load, using default marker");
  };
  img.src = '/frontend/images/ambulance.png';

  let routeLayer = null;
  let animMarker = null;
  let animInterval = null;
  let pickupMarker = null;
  let startMarker = null;
  let endMarker = null;
  let currentRoute = null;
  let currentIndex = 0;
  let isAnimating = false;

  function drawRoute(geojson) {
    // Clear previous route and markers
    if (routeLayer) { map.removeLayer(routeLayer); routeLayer = null; }
    if (animMarker) { map.removeLayer(animMarker); animMarker = null; }
    if (pickupMarker) { map.removeLayer(pickupMarker); pickupMarker = null; }
    if (startMarker) { map.removeLayer(startMarker); startMarker = null; }
    if (endMarker) { map.removeLayer(endMarker); endMarker = null; }
    if (animInterval) { clearInterval(animInterval); animInterval = null; }
    
    if (!geojson || !geojson.features || geojson.features.length === 0) {
      console.error("Invalid geojson data");
      return;
    }

    const coords = geojson.features[0].geometry.coordinates;
    if (!coords || coords.length < 2) {
      console.error("Invalid coordinates");
      return;
    }

    const latlngs = coords.map(c => [c[1], c[0]]);
    
    // Verify route starts and ends at IITB Hospital
    // Note: Due to road snapping, coordinates may be slightly different from exact hospital location
    const HOSPITAL_LAT = 19.1309507;
    const HOSPITAL_LNG = 72.9146062;
    const hospitalPoint = [HOSPITAL_LAT, HOSPITAL_LNG];
    
    // Ensure route starts from hospital - prepend hospital point if route start is far
    const startPoint = latlngs[0];
    const endPoint = latlngs[latlngs.length - 1];
    
    // Calculate distance from route start to hospital
    const routeStartDistance = Math.sqrt(
      Math.pow((startPoint[0] - HOSPITAL_LAT) * 111000, 2) + 
      Math.pow((startPoint[1] - HOSPITAL_LNG) * 111000 * Math.cos(HOSPITAL_LAT * Math.PI / 180), 2)
    );
    
    // If route start is more than 50m from hospital, prepend hospital point to route
    if (routeStartDistance > 50) {
      latlngs.unshift(hospitalPoint);
      console.log("Prepended hospital coordinates to route (route start was", Math.round(routeStartDistance), "m away)");
    }
    
    // Draw route with smooth blue line (now includes hospital start point if needed)
    routeLayer = L.polyline(latlngs, {
      color: "#0066ff",
      weight: 5,
      opacity: 0.7,
      smoothFactor: 1
    }).addTo(map);
    
    // Fit bounds with padding
    map.fitBounds(routeLayer.getBounds(), {padding: [50, 50]});
    
    // Check if start and end are near hospital (within ~500m tolerance for road snapping)
    const tolerance = 0.005; // approximately 500 meters (allows for road snapping)
    const startNearHospital = Math.abs(startPoint[0] - HOSPITAL_LAT) < tolerance && 
                              Math.abs(startPoint[1] - HOSPITAL_LNG) < tolerance;
    const endNearHospital = Math.abs(endPoint[0] - HOSPITAL_LAT) < tolerance && 
                            Math.abs(endPoint[1] - HOSPITAL_LNG) < tolerance;
    
    // Only log warnings if significantly far from hospital
    if (!startNearHospital) {
      const distance = Math.sqrt(
        Math.pow((startPoint[0] - HOSPITAL_LAT) * 111000, 2) + 
        Math.pow((startPoint[1] - HOSPITAL_LNG) * 111000 * Math.cos(HOSPITAL_LAT * Math.PI / 180), 2)
      );
      if (distance > 1000) { // Only warn if more than 1km away
        console.warn("Route start is far from IITB Hospital. Distance:", Math.round(distance), "m");
      }
    }
    if (!endNearHospital) {
      const distance = Math.sqrt(
        Math.pow((endPoint[0] - HOSPITAL_LAT) * 111000, 2) + 
        Math.pow((endPoint[1] - HOSPITAL_LNG) * 111000 * Math.cos(HOSPITAL_LAT * Math.PI / 180), 2)
      );
      if (distance > 1000) { // Only warn if more than 1km away
        console.warn("Route end is far from IITB Hospital. Distance:", Math.round(distance), "m");
      }
    }

    // Find pickup point (middle point of route)
    const pickupIndex = Math.floor(latlngs.length / 2);
    const pickupPoint = latlngs[pickupIndex];
    
    // Add start marker (Hospital - departure)
    startMarker = L.marker(startPoint, {
      icon: L.icon({
        iconUrl: 'https://raw.githubusercontent.com/pointhi/leaflet-color-markers/master/img/marker-icon-green.png',
        iconSize: [25, 41],
        iconAnchor: [12, 41],
        popupAnchor: [1, -34]
      })
    }).addTo(map).bindPopup("IITB Hospital (Start)");
    
    // Add pickup marker
    pickupMarker = L.marker(pickupPoint, {
      icon: L.icon({
        iconUrl: 'https://raw.githubusercontent.com/pointhi/leaflet-color-markers/master/img/marker-icon-red.png',
        iconSize: [25, 41],
        iconAnchor: [12, 41],
        popupAnchor: [1, -34]
      })
    }).addTo(map).bindPopup("Pickup Location");
    
    // Add end marker (Hospital - return)
    endMarker = L.marker(endPoint, {
      icon: L.icon({
        iconUrl: 'https://raw.githubusercontent.com/pointhi/leaflet-color-markers/master/img/marker-icon-blue.png',
        iconSize: [25, 41],
        iconAnchor: [12, 41],
        popupAnchor: [1, -34]
      })
    }).addTo(map).bindPopup("IITB Hospital (Return)");

    // Start animation from hospital - ambulance always starts at actual hospital location
    // (latlngs[0] should now be hospital point if we prepended it)
    currentRoute = latlngs;
    currentIndex = 0;
    isAnimating = true;

    // Create ambulance marker at hospital location (first point of route, which is now hospital)
    const iconToUse = ambulanceIconLoaded ? ambulanceIcon : undefined;
    animMarker = L.marker(latlngs[0], {
      icon: iconToUse,
      rotationAngle: 0
    }).addTo(map);

    // Calculate bearing for rotation
    function calculateBearing(from, to) {
      const dLon = (to[1] - from[1]) * Math.PI / 180;
      const lat1 = from[0] * Math.PI / 180;
      const lat2 = to[0] * Math.PI / 180;
      const y = Math.sin(dLon) * Math.cos(lat2);
      const x = Math.cos(lat1) * Math.sin(lat2) - Math.sin(lat1) * Math.cos(lat2) * Math.cos(dLon);
      const bearing = Math.atan2(y, x) * 180 / Math.PI;
      return (bearing + 360) % 360;
    }

    // Smooth animation with rotation
    // Slower speed to simulate real vehicle movement (like a truck/ambulance)
    let lastBearing = 0;
    const animationSpeed = 200; // milliseconds per step (slower = more realistic vehicle speed)
    
    animInterval = setInterval(() => {
      if (currentIndex >= currentRoute.length - 1) {
        clearInterval(animInterval);
        isAnimating = false;
        // Show completion message
        animMarker.bindPopup("Arrived at IITB Hospital").openPopup();
        return;
      }

      const current = currentRoute[currentIndex];
      const next = currentRoute[currentIndex + 1];
      
      // Calculate bearing and rotate icon
      const bearing = calculateBearing(current, next);
      
      // Smooth rotation
      let rotationDiff = bearing - lastBearing;
      if (rotationDiff > 180) rotationDiff -= 360;
      if (rotationDiff < -180) rotationDiff += 360;
      lastBearing += rotationDiff * 0.3; // Smooth rotation
      if (lastBearing < 0) lastBearing += 360;
      if (lastBearing >= 360) lastBearing -= 360;

      // Update icon rotation using CSS transform
      const iconElement = animMarker._icon;
      if (iconElement) {
        iconElement.style.transform = `rotate(${lastBearing}deg)`;
        iconElement.style.transition = 'transform 0.1s ease-out';
      }

      // Move to next position
      currentIndex++;
      animMarker.setLatLng(currentRoute[currentIndex]);
      
      // Update popup at pickup point
      if (currentIndex === pickupIndex) {
        animMarker.bindPopup("Picked up patient").openPopup();
      }
    }, animationSpeed);
  }

  window.routingMap = {
    showRoute: drawRoute,
    map: map
  };
});
