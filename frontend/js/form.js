// form.js
document.addEventListener("DOMContentLoaded", function() {
  const form = document.getElementById("tripForm");
  const exportBtn = document.getElementById("exportBtn");
  const locationSelect = document.getElementById("location_name");
  const startOdometerDisplay = document.getElementById("start_odometer_display");
  const dateInput = document.getElementById("date");

  // show current date/time in Date field (display only)
  function refreshDate() {
    const now = new Date();
    dateInput.value = now.toLocaleString();
  }
  refreshDate();
  setInterval(refreshDate, 30000);

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
        dateInput.value = new Date(res.date).toLocaleString();
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
      alert("Submit failed: " + (err.error || JSON.stringify(err)));
      console.error(err);
    }
  });

  exportBtn.addEventListener("click", () => {
    window.location = "/api/trip/export";
  });

});
