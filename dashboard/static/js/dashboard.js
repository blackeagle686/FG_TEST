/**
 * FortyGuard Urban Thermal AI - Dashboard Controller
 * Manages Dual Leaflet Sync Maps, Predictive Engine Calls,
 * Chart.js Time Series, and Station Analytics.
 */

let mapCurrent, mapPredicted;
let geojsonCurrentLayer, geojsonPredictedLayer;
let timeseriesChart = null;
let currentForecastHours = 3;
let currentScenario = "baseline";
let selectedLocationId = "LOC_001_DOWNTOWN";

// Color ramp for urban thermal gradients
function getThermalColor(tempC) {
  if (tempC >= 38.0) return "#e74c3c"; // Crimson Extreme
  if (tempC >= 34.0) return "#e67e22"; // Dark Amber Hot
  if (tempC >= 31.5) return "#d4af37"; // Metallic Gold High
  if (tempC >= 29.0) return "#c5a028"; // Muted Gold Warm
  if (tempC >= 26.0) return "#f3e5ab"; // Light Gold Mild
  return "#5dade2";                   // Cool Cyan
}

// Free Basemaps (100% Free, No API Key Required)
const FREE_BASEMAPS = {
  esriDark: {
    url: "https://server.arcgisonline.com/ArcGIS/rest/services/Canvas/World_Dark_Gray_Base/MapServer/tile/{z}/{y}/{x}",
    options: {
      attribution: '&copy; <a href="https://www.esri.com" target="_blank" style="color:#d4af37">Esri</a> & FortyGuard',
      maxZoom: 16
    }
  },
  osm: {
    url: "https://tile.openstreetmap.org/{z}/{x}/{y}.png",
    options: {
      attribution: '&copy; <a href="https://www.openstreetmap.org/copyright" target="_blank" style="color:#d4af37">OpenStreetMap</a> contributors',
      maxZoom: 19
    }
  },
  satellite: {
    url: "https://server.arcgisonline.com/ArcGIS/rest/services/World_Imagery/MapServer/tile/{z}/{y}/{x}",
    options: {
      attribution: '&copy; <a href="https://www.esri.com" target="_blank" style="color:#d4af37">Esri Satellite</a> & FortyGuard',
      maxZoom: 18
    }
  }
};

let currentBasemapKey = "esriDark";
let tileLayerCurrent, tileLayerPredicted;

// Initialize Leaflet Maps
function initMaps() {
  const defaultCenter = [40.7115, -74.0100];
  const defaultZoom = 15;

  const activeBasemap = FREE_BASEMAPS[currentBasemapKey];

  // Map 1: Current Observed
  mapCurrent = L.map("map-current", {
    center: defaultCenter,
    zoom: defaultZoom,
    zoomControl: false
  });
  tileLayerCurrent = L.tileLayer(activeBasemap.url, activeBasemap.options).addTo(mapCurrent);
  L.control.zoom({ position: "bottomleft" }).addTo(mapCurrent);

  // Map 2: Model Predicted
  mapPredicted = L.map("map-predicted", {
    center: defaultCenter,
    zoom: defaultZoom,
    zoomControl: false
  });
  tileLayerPredicted = L.tileLayer(activeBasemap.url, activeBasemap.options).addTo(mapPredicted);
  L.control.zoom({ position: "bottomleft" }).addTo(mapPredicted);

  // Synchronize Map Panning & Zooming
  let isSyncing = false;
  function syncMaps(source, target) {
    if (isSyncing) return;
    isSyncing = true;
    target.setView(source.getCenter(), source.getZoom(), { animate: false });
    isSyncing = false;
  }

  mapCurrent.on("move", () => syncMaps(mapCurrent, mapPredicted));
  mapPredicted.on("move", () => syncMaps(mapPredicted, mapCurrent));
}

// Load and Render Observed Heatmap
async function loadCurrentHeatmap() {
  try {
    const res = await fetch("/api/heatmap/current");
    const data = await res.json();

    if (geojsonCurrentLayer) mapCurrent.removeLayer(geojsonCurrentLayer);

    geojsonCurrentLayer = L.geoJSON(data, {
      style: (feature) => {
        const temp = feature.properties?.average_temperature || 32.0;
        return {
          fillColor: getThermalColor(temp),
          weight: 0.8,
          opacity: 0.8,
          color: "rgba(212, 175, 55, 0.4)",
          fillOpacity: 0.65
        };
      },
      onEachFeature: (feature, layer) => {
        const p = feature.properties || {};
        layer.bindPopup(`
          <div style="font-family: 'Plus Jakarta Sans', sans-serif;">
            <div style="color: #d4af37; font-weight: 700; font-size: 0.85rem; margin-bottom: 4px;">
              <i class="fas fa-layer-group"></i> TILE #${p.tile_id || 0}
            </div>
            <div style="font-size: 1.25rem; font-weight: 800; color: #ffffff;">
              ${(p.average_temperature || 32.0).toFixed(2)} °C
            </div>
            <div style="font-size: 0.75rem; color: #94a3b8; margin-top: 4px;">
              Min: ${(p.min_temperature || 0).toFixed(2)} °C | Max: ${(p.max_temperature || 0).toFixed(2)} °C
            </div>
          </div>
        `);
        layer.on("mouseover", function() {
          this.setStyle({ fillOpacity: 0.9, weight: 1.5, color: "#ffffff" });
        });
        layer.on("mouseout", function() {
          geojsonCurrentLayer.resetStyle(this);
        });
      }
    }).addTo(mapCurrent);

    if (data.features && data.features.length > 0) {
      mapCurrent.fitBounds(geojsonCurrentLayer.getBounds(), { padding: [20, 20] });
    }
  } catch (err) {
    console.error("Error loading current heatmap:", err);
  }
}

// Load and Render AI-Predicted Heatmap
async function loadPredictedHeatmap(hoursAhead, scenario) {
  try {
    const res = await fetch(`/api/heatmap/predict?hours_ahead=${hoursAhead}&scenario=${scenario}`);
    const data = await res.json();

    if (geojsonPredictedLayer) mapPredicted.removeLayer(geojsonPredictedLayer);

    geojsonPredictedLayer = L.geoJSON(data, {
      style: (feature) => {
        const temp = feature.properties?.predicted_temperature || 33.0;
        return {
          fillColor: getThermalColor(temp),
          weight: 0.8,
          opacity: 0.8,
          color: "rgba(212, 175, 55, 0.5)",
          fillOpacity: 0.72
        };
      },
      onEachFeature: (feature, layer) => {
        const p = feature.properties || {};
        const deltaSign = p.delta_celsius >= 0 ? `+${p.delta_celsius.toFixed(2)}` : p.delta_celsius.toFixed(2);
        const deltaColor = p.delta_celsius >= 0 ? "#ff6b6b" : "#2ecc71";

        layer.bindPopup(`
          <div style="font-family: 'Plus Jakarta Sans', sans-serif;">
            <div style="display: flex; justify-content: space-between; align-items: center; margin-bottom: 6px;">
              <span style="color: #d4af37; font-weight: 700; font-size: 0.82rem;">
                <i class="fas fa-brain"></i> PREDICTED (+${hoursAhead}h)
              </span>
              <span style="background: ${deltaColor}20; color: ${deltaColor}; font-weight: 700; font-size: 0.72rem; padding: 2px 6px; border-radius: 4px;">
                Δ ${deltaSign} °C
              </span>
            </div>
            <div style="font-size: 1.35rem; font-weight: 800; color: #ffffff;">
              ${(p.predicted_temperature || 33.0).toFixed(2)} °C
            </div>
            <div style="font-size: 0.76rem; color: #94a3b8; margin-top: 4px;">
              Heat Index: ${(p.heat_index_celsius || 0).toFixed(1)} °C | Risk: <b style="color: ${p.theme_color || '#fff'}">${p.risk_level}</b>
            </div>
          </div>
        `);
        layer.on("mouseover", function() {
          this.setStyle({ fillOpacity: 0.95, weight: 1.8, color: "#d4af37" });
        });
        layer.on("mouseout", function() {
          geojsonPredictedLayer.resetStyle(this);
        });
      }
    }).addTo(mapPredicted);

    // Update KPI metrics
    if (data.summary) {
      document.getElementById("kpi-current-mean").innerText = `${data.summary.current_mean_c.toFixed(1)} °C`;
      document.getElementById("kpi-pred-mean").innerText = `${data.summary.predicted_mean_c.toFixed(1)} °C`;
      
      const deltaSign = data.summary.average_delta_c >= 0 ? `+${data.summary.average_delta_c.toFixed(2)}` : data.summary.average_delta_c.toFixed(2);
      document.getElementById("kpi-delta").innerText = `Δ ${deltaSign} °C`;
      document.getElementById("kpi-delta").className = `delta-badge ${data.summary.average_delta_c >= 0 ? 'warm' : 'cool'}`;
      
      document.getElementById("kpi-max-heat").innerText = `${data.summary.max_predicted_c.toFixed(1)} °C`;
      document.getElementById("forecast-badge-time").innerText = `+${hoursAhead}h (${data.summary.forecast_time})`;
    }
  } catch (err) {
    console.error("Error loading predicted heatmap:", err);
  }
}

// Load Microclimate Locations
async function loadLocations(hoursAhead) {
  try {
    const res = await fetch(`/api/locations?hours_ahead=${hoursAhead}`);
    const locations = await res.json();
    const container = document.getElementById("stations-container");
    container.innerHTML = "";

    locations.forEach((loc) => {
      const isAct = loc.location_id === selectedLocationId ? "active" : "";
      const deltaSign = loc.delta_c >= 0 ? `+${loc.delta_c.toFixed(1)}` : loc.delta_c.toFixed(1);
      const deltaClass = loc.delta_c >= 0 ? "warm" : "cool";

      const card = document.createElement("div");
      card.className = `station-card ${isAct}`;
      card.onclick = () => selectStation(loc);

      card.innerHTML = `
        <div class="d-flex justify-content-between align-items-center">
          <div>
            <div class="station-name">${loc.name}</div>
            <div class="station-cat">${loc.category}</div>
          </div>
          <div class="text-end">
            <div class="station-temp text-white">${loc.predicted_temp_c.toFixed(1)} °C</div>
            <span class="delta-badge ${deltaClass}">${deltaSign} °C</span>
          </div>
        </div>
      `;
      container.appendChild(card);
    });
  } catch (err) {
    console.error("Error loading locations:", err);
  }
}

function selectStation(loc) {
  selectedLocationId = loc.location_id;
  document.querySelectorAll(".station-card").forEach(c => c.classList.remove("active"));
  event?.currentTarget?.classList.add("active");

  // Center maps on station
  mapCurrent.flyTo([loc.latitude, loc.longitude], 16, { duration: 1.2 });
  mapPredicted.flyTo([loc.latitude, loc.longitude], 16, { duration: 1.2 });

  // Update Time Series Chart
  loadTimeSeriesChart(loc.location_id);
}

// Render Time Series Chart
async function loadTimeSeriesChart(locationId) {
  try {
    const res = await fetch(`/api/timeseries/${locationId}`);
    const data = await res.json();

    document.getElementById("chart-station-title").innerText = `${data.location.name} (Past 24h & Next 24h Forecast)`;

    const ctx = document.getElementById("timeseries-chart").getContext("2d");

    if (timeseriesChart) {
      timeseriesChart.destroy();
    }

    // Chart Gradient for Confidence Area
    const gradient = ctx.createLinearGradient(0, 0, 0, 240);
    gradient.addColorStop(0, "rgba(212, 175, 55, 0.25)");
    gradient.addColorStop(1, "rgba(212, 175, 55, 0.0)");

    timeseriesChart = new Chart(ctx, {
      type: "line",
      data: {
        labels: data.labels,
        datasets: [
          {
            label: "Observed Temperature (°C)",
            data: data.historical,
            borderColor: "#ffffff",
            backgroundColor: "transparent",
            borderWidth: 2.2,
            pointRadius: 0,
            pointHoverRadius: 4,
            tension: 0.35
          },
          {
            label: "Model Predicted (°C)",
            data: data.forecast,
            borderColor: "#d4af37",
            backgroundColor: gradient,
            fill: true,
            borderWidth: 2.5,
            borderDash: [5, 5],
            pointRadius: 0,
            pointHoverRadius: 5,
            tension: 0.35
          },
          {
            label: "Upper Bound (95%)",
            data: data.upper_bound,
            borderColor: "rgba(212, 175, 55, 0.15)",
            backgroundColor: "transparent",
            borderWidth: 1,
            pointRadius: 0,
            fill: false,
            tension: 0.35
          },
          {
            label: "Lower Bound (95%)",
            data: data.lower_bound,
            borderColor: "rgba(212, 175, 55, 0.15)",
            backgroundColor: "transparent",
            borderWidth: 1,
            pointRadius: 0,
            fill: false,
            tension: 0.35
          }
        ]
      },
      options: {
        responsive: true,
        maintainAspectRatio: false,
        interaction: {
          mode: "index",
          intersect: false
        },
        plugins: {
          legend: {
            display: true,
            position: "top",
            labels: {
              color: "#94a3b8",
              font: { size: 11, family: "Plus Jakarta Sans" },
              boxWidth: 12,
              filter: (item) => item.text.includes("Observed") || item.text.includes("Model")
            }
          },
          tooltip: {
            backgroundColor: "rgba(12, 14, 21, 0.95)",
            titleColor: "#d4af37",
            bodyColor: "#ffffff",
            borderColor: "rgba(212, 175, 55, 0.3)",
            borderWidth: 1,
            padding: 10,
            boxPadding: 4,
            callbacks: {
              label: (ctx) => `${ctx.dataset.label}: ${ctx.raw ? ctx.raw.toFixed(2) + " °C" : ""}`
            }
          }
        },
        scales: {
          x: {
            grid: { color: "rgba(255, 255, 255, 0.03)" },
            ticks: {
              color: "#64748b",
              maxTicksLimit: 12,
              font: { size: 10 }
            }
          },
          y: {
            grid: { color: "rgba(255, 255, 255, 0.04)" },
            ticks: {
              color: "#94a3b8",
              font: { size: 10 },
              callback: (val) => `${val}°`
            }
          }
        }
      }
    });
  } catch (err) {
    console.error("Error loading time series chart:", err);
  }
}

// Basemap Switcher (100% Free, Zero Key)
function changeBasemap(key) {
  if (!FREE_BASEMAPS[key]) return;
  currentBasemapKey = key;
  const cfg = FREE_BASEMAPS[key];

  if (tileLayerCurrent) mapCurrent.removeLayer(tileLayerCurrent);
  if (tileLayerPredicted) mapPredicted.removeLayer(tileLayerPredicted);

  tileLayerCurrent = L.tileLayer(cfg.url, cfg.options).addTo(mapCurrent);
  tileLayerPredicted = L.tileLayer(cfg.url, cfg.options).addTo(mapPredicted);

  if (geojsonCurrentLayer) geojsonCurrentLayer.bringToFront();
  if (geojsonPredictedLayer) geojsonPredictedLayer.bringToFront();
}

// Time Horizon Button Handlers
function setupEventListeners() {
  document.querySelectorAll('input[name="time_horizon"]').forEach((input) => {
    input.addEventListener("change", (e) => {
      currentForecastHours = parseInt(e.target.value);
      loadPredictedHeatmap(currentForecastHours, currentScenario);
      loadLocations(currentForecastHours);
    });
  });

  const scenarioSelect = document.getElementById("scenario-select");
  if (scenarioSelect) {
    scenarioSelect.addEventListener("change", (e) => {
      currentScenario = e.target.value;
      loadPredictedHeatmap(currentForecastHours, currentScenario);
      loadLocations(currentForecastHours);
    });
  }

  const basemapSelect = document.getElementById("basemap-select");
  if (basemapSelect) {
    basemapSelect.addEventListener("change", (e) => {
      changeBasemap(e.target.value);
    });
  }
}

// Live Clock in Header
function updateClock() {
  const clockEl = document.getElementById("live-clock");
  if (clockEl) {
    const now = new Date();
    clockEl.innerText = now.toUTCString().replace("GMT", "UTC");
  }
}

// Entrypoint
document.addEventListener("DOMContentLoaded", () => {
  initMaps();
  loadCurrentHeatmap();
  loadPredictedHeatmap(currentForecastHours, currentScenario);
  loadLocations(currentForecastHours);
  loadTimeSeriesChart(selectedLocationId);
  setupEventListeners();
  updateClock();
  setInterval(updateClock, 1000);
});
