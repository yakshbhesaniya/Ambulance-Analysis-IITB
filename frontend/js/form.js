// form.js
document.addEventListener("DOMContentLoaded", function() {
  const form = document.getElementById("tripForm");
  const exportBtn = document.getElementById("exportBtn");
  const locationSelect = document.getElementById("location_name");
  const startOdometerDisplay = document.getElementById("start_odometer_display");
  const dateInput = document.getElementById("date");

  // show current date/time in Date field (display only) - updates every second
  function refreshDate() {
    const now = new Date();
    dateInput.value = now.toLocaleString('en-IN', {
      year: 'numeric',
      month: '2-digit',
      day: '2-digit',
      hour: '2-digit',
      minute: '2-digit',
      second: '2-digit',
      hour12: false
    });
  }
  refreshDate();
  setInterval(refreshDate, 1000); // Update every second

  // load locations and populate select
  async function loadLocations() {
    try {
      const res = await fetch("/api/locations").then(r => r.json());
      const locations = res.locations || {};
      locationSelect.innerHTML = '<option value="">-- choose location --</option>';
      Object.keys(locations).forEach(name => {
        const opt = document.createElement("option");
        opt.value = name;
        opt.textContent = name;
        locationSelect.appendChild(opt);
      });
    } catch (err) {
      console.error("Failed to load locations", err);
    }
  }

  // fetch last trip and prefill start odometer display
  async function prefillStartOdometerDisplay() {
    try {
      const res = await fetch("/api/trip/last").then(r => r.json());
      const last = res.last;
      if (last && last.next_odometer !== null && last.next_odometer !== undefined) {
        startOdometerDisplay.value = last.next_odometer;
      } else {
        startOdometerDisplay.value = 0;
      }
    } catch (err) {
      console.error("Failed to fetch last trip", err);
      startOdometerDisplay.value = 0;
    }
  }

  // initial load
  loadLocations();
  prefillStartOdometerDisplay();

  form.addEventListener("submit", async (e) => {
    e.preventDefault();
    const payload = {
      location_name: (document.getElementById("location_name").value || "").trim(),
      patient_name: (document.getElementById("patient_name").value || "").trim(),
      driver_name: (document.getElementById("driver_name").value || "").trim(),
      purpose: (document.getElementById("purpose").value || "").trim(),
      notes: document.getElementById("notes").value || ""
    };
    try {
      const res = await fetchJSON("/api/trip", {
        method: "POST",
        body: JSON.stringify(payload),
        headers: { "Content-Type": "application/json" }
      });
      showLastTrip(res);

      // update displayed start odometer to server-returned start_odometer (should be same as displayed before)
      if (res.start_odometer !== null && res.start_odometer !== undefined) {
        startOdometerDisplay.value = res.start_odometer;
      }
      // update displayed to next_odometer so user sees the progression
      if (res.next_odometer !== null && res.next_odometer !== undefined) {
        startOdometerDisplay.value = res.next_odometer;
      }

      // update displayed date to computed date
      if (res.date) {
        const dateObj = new Date(res.date);
        dateInput.value = dateObj.toLocaleString('en-IN', {
          year: 'numeric',
          month: '2-digit',
          day: '2-digit',
          hour: '2-digit',
          minute: '2-digit',
          second: '2-digit',
          hour12: false
        });
      }
      
      // Show trip summary with timing
      const tripSummary = document.getElementById("tripSummary");
      const tripDetails = document.getElementById("tripDetails");
      if (res.departure_time && res.arrival_time && res.route_seconds) {
        const depTime = new Date(res.departure_time);
        const arrTime = new Date(res.arrival_time);
        const durationMin = Math.floor(res.route_seconds / 60);
        const durationSec = res.route_seconds % 60;
        
        tripDetails.innerHTML = `
          <div><strong>Distance:</strong> ${res.distance_km || 0} km</div>
          <div><strong>Duration:</strong> ${durationMin}m ${durationSec}s</div>
          <div><strong>Departure:</strong> ${depTime.toLocaleTimeString()}</div>
          <div><strong>Arrival:</strong> ${arrTime.toLocaleTimeString()}</div>
          <div><strong>Odometer:</strong> ${res.start_odometer || 0} → ${res.next_odometer || 0} km</div>
        `;
        tripSummary.style.display = "block";
      }

      // draw route on routing map
      if (window.routingMap && res.geojson) {
        window.routingMap.showRoute(res.geojson);
      }
      // refresh analysis
      if (window.analysisMap) {
        window.analysisMap.loadAnalysis();
      }
    } catch (err) {
      const errorMsg = err.error || err.message || JSON.stringify(err);
      alert("Submit failed: " + errorMsg);
      console.error("Form submission error:", err);
      
      // Hide trip summary on error
      const tripSummary = document.getElementById("tripSummary");
      if (tripSummary) tripSummary.style.display = "none";
    }
  });

  exportBtn.addEventListener("click", () => {
    window.location = "/api/trip/export";
  });

});
