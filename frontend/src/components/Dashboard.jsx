// src/components/Dashboard.jsx
import { useEffect, useRef, useState } from "react";
import {
  fetchPrices,
  fetchBaseload,
  fetchInfo,
  apiStartCharging,
  apiStopCharging,
  apiDischarge,
} from "../api/evApi";
import CarScene from "./CarScene";

const BATTERY_CAPACITY_KWH = 46.3;
const MAX_HOURS = 24;
const POLL_MS = 2000; // 1 simulated hour ≈ 2 real seconds

// Dual SVG chart for price & load (24h)
function PriceChart({ prices, loads, currentHour, themeMode }) {
  const ready = prices && prices.length === 24 && loads && loads.length === 24;
  if (!ready) {
    return <p className="label">Waiting for server data…</p>;
  }

  const width = 600;
  const height = 240;
  const paddingX = 18;
  const paddingY = 26;
  const hours = [...Array(24).keys()];
  const cappedHour = Math.min(Math.max(currentHour ?? 0, 0), 23);
  const activeHours = hours.slice(0, Math.max(1, cappedHour + 1));

  const maxPrice = Math.max(...prices);
  const minPrice = Math.min(...prices);
  const priceRange = maxPrice - minPrice || 1;

  const maxLoad = Math.max(...loads);
  const minLoad = Math.min(...loads);
  const loadRange = maxLoad - minLoad || 1;

  const xForHour = (hour) =>
    (hour / 23) * (width - paddingX * 2) + paddingX;

  const priceY = (value) => {
    const norm = (value - minPrice) / priceRange;
    return height - paddingY - norm * (height - paddingY * 2);
  };

  const loadY = (value) => {
    const norm = (value - minLoad) / loadRange;
    return height - paddingY - norm * (height - paddingY * 2);
  };

  const pricePoints = activeHours
    .map((hour) => `${xForHour(hour)},${priceY(prices[hour])}`)
    .join(" ");
  const loadPoints = activeHours
    .map((hour) => `${xForHour(hour)},${loadY(loads[hour] ?? 0)}`)
    .join(" ");
  const indicatorX = xForHour(cappedHour);

  const isDark = themeMode === "dark";
  const axisColor = isDark ? "rgba(255, 255, 255, 0.35)" : "#c9a352";
  const priceColor = isDark ? "#ffb347" : "#ff7a3d";
  const loadColor = isDark ? "#6de6a6" : "#1f9d6d";
  const indicatorColor = isDark
    ? "rgba(255, 255, 255, 0.3)"
    : "rgba(80, 60, 10, 0.25)";

  return (
    <svg
      viewBox={`0 0 ${width} ${height}`}
      className="price-chart"
      role="img"
      aria-label="24-hour price and load trends"
    >
      <line
        x1={paddingX}
        y1={height - paddingY}
        x2={width - paddingX}
        y2={height - paddingY}
        stroke={axisColor}
        strokeWidth="1"
      />
      <line
        x1={paddingX}
        y1={paddingY}
        x2={paddingX}
        y2={height - paddingY}
        stroke={axisColor}
        strokeWidth="1"
      />
      <line
        x1={width - paddingX}
        y1={paddingY}
        x2={width - paddingX}
        y2={height - paddingY}
        stroke={axisColor}
        strokeWidth="1"
      />
      <polyline
        points={pricePoints}
        fill="none"
        stroke={priceColor}
        strokeWidth="2"
        strokeLinejoin="round"
        strokeLinecap="round"
      />
      <polyline
        points={loadPoints}
        fill="none"
        stroke={loadColor}
        strokeWidth="2"
        strokeLinejoin="round"
        strokeLinecap="round"
        strokeDasharray="4 4"
      />
      {activeHours.map((hour) => {
        const priceX = xForHour(hour);
        const priceVal = priceY(prices[hour]);
        const loadVal = loadY(loads[hour] ?? 0);
        return (
          <g key={hour}>
            <circle cx={priceX} cy={priceVal} r="3" fill={priceColor} />
            <circle cx={priceX} cy={loadVal} r="3" fill={loadColor} />
          </g>
        );
      })}
      <line
        x1={indicatorX}
        y1={paddingY}
        x2={indicatorX}
        y2={height - paddingY}
        stroke={indicatorColor}
        strokeWidth="1.5"
        strokeDasharray="6 4"
      />
    </svg>
  );
}

export default function Dashboard() {
  const [mode, setMode] = useState("price"); // "price" | "load"
  const [themeMode, setThemeMode] = useState("light");
  const [prices, setPrices] = useState([]);
  const [loads, setLoads] = useState([]);
  const [chartPrices, setChartPrices] = useState([]);
  const [chartLoads, setChartLoads] = useState([]);

  const [simHour, setSimHour] = useState(0);
  const [simMin, setSimMin] = useState(0);

  const [batteryPercent, setBatteryPercent] = useState(0);
  const [batteryKWh, setBatteryKWh] = useState(0);
  const [batteryMaxKWh, setBatteryMaxKWh] = useState(BATTERY_CAPACITY_KWH);
  const [currentLoad, setCurrentLoad] = useState(0);
  const [currentPrice, setCurrentPrice] = useState(0);
  const [charging, setCharging] = useState(false);

  const [logs, setLogs] = useState([]); // simulation log lines
  const [running, setRunning] = useState(false); // auto-simulation flag
  const [loadingInitial, setLoadingInitial] = useState(true);
  const [ringAngle, setRingAngle] = useState(0);
  const [userLocation, setUserLocation] = useState("Detecting location…");

  // Refs to avoid stale values inside setInterval
  const pricesRef = useRef([]);
  const loadsRef = useRef([]);
  const modeRef = useRef("price");
  const batteryMaxRef = useRef(BATTERY_CAPACITY_KWH);

  const intervalRef = useRef(null);
  const lastLoggedHourRef = useRef(null);
  const fullStopRef = useRef(false); // has 100% auto stop been logged?
  const runningRef = useRef(false);
  const pollInFlightRef = useRef(false);

  useEffect(() => {
    runningRef.current = running;
  }, [running]);

  useEffect(() => {
    pricesRef.current = prices;
  }, [prices]);

  useEffect(() => {
    loadsRef.current = loads;
  }, [loads]);

  useEffect(() => {
    modeRef.current = mode;
  }, [mode]);

  useEffect(() => {
    batteryMaxRef.current = batteryMaxKWh || BATTERY_CAPACITY_KWH;
  }, [batteryMaxKWh]);

  useEffect(() => {
    document.body.classList.toggle("theme-dark", themeMode === "dark");
  }, [themeMode]);

  useEffect(() => {
    return () => {
      document.body.classList.remove("theme-dark");
    };
  }, []);

  useEffect(() => {
    let cancelled = false;
    async function resolveLocation() {
      try {
        const resp = await fetch("https://ipapi.co/json/");
        if (!resp.ok) {
          throw new Error("Failed to detect location");
        }
        const data = await resp.json();
        if (cancelled) return;
        const city = data.city || data.region || data.country_name || "Unknown";
        const country = data.country_name || data.country || "";
        const label =
          country && city && country !== city
            ? `${city}, ${country}`
            : city || "Unknown location";
        setUserLocation(label);
      } catch {
        if (!cancelled) {
          setUserLocation("Unknown location");
        }
      }
    }
    resolveLocation();
    return () => {
      cancelled = true;
    };
  }, []);

  useEffect(() => {
    if (!charging) {
      return undefined;
    }
    const id = window.setInterval(() => {
      setRingAngle((prev) => (prev + 0.45) % 360);
    }, 40);
    return () => window.clearInterval(id);
  }, [charging]);


  useEffect(() => {
    async function init() {
      try {
        const [p, l, info] = await Promise.all([
          fetchPrices(),
          fetchBaseload(),
          fetchInfo(),
        ]);

        setPrices(p);
        setLoads(l);
        setChartPrices(p);
        setChartLoads(l);

        const maxKWh =
          info.battery_max_capacity_kWh ?? BATTERY_CAPACITY_KWH;
        const kWh = info.battery_capacity_kWh ?? 0;
        const pct = maxKWh > 0 ? (kWh / maxKWh) * 100 : 0;

        setBatteryMaxKWh(maxKWh);
        setBatteryKWh(kWh);
        setBatteryPercent(pct);
        setCurrentLoad(info.base_current_load ?? 0);
        setCharging(info.ev_battery_charge_start_stopp ?? false);

        const h = info.sim_time_hour ?? 0;
        const m = info.sim_time_min ?? 0;
        setSimHour(h);
        setSimMin(m);
        setCurrentPrice(p[h] ?? 0);
      } catch (e) {
        console.error("Init failed", e);
      } finally {
        setLoadingInitial(false);
      }
    }

    init();

    intervalRef.current = window.setInterval(pollTick, POLL_MS);

    return () => {
      if (intervalRef.current !== null) clearInterval(intervalRef.current);
    };
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, []);

  async function pollTick() {
    if (pollInFlightRef.current) {
      return;
    }
    pollInFlightRef.current = true;
    try {
      const info = await fetchInfo();

      const h = info.sim_time_hour ?? 0;
      const m = info.sim_time_min ?? 0;
      let maxKWh =
        info.battery_max_capacity_kWh ??
        batteryMaxRef.current ??
        BATTERY_CAPACITY_KWH;
      if (maxKWh <= 0) {
        maxKWh = BATTERY_CAPACITY_KWH;
      }

      const loadsArr = loadsRef.current;
      const pricesArr = pricesRef.current;

      const baseLoad =
        info.base_current_load ??
        (loadsArr.length > 0 ? loadsArr[h] ?? 0 : 0);
      const price = pricesArr.length > 0 ? pricesArr[h] ?? currentPrice : 0;

      let kWh = info.battery_capacity_kWh ?? 0;
      let pct = maxKWh > 0 ? (kWh / maxKWh) * 100 : 0;
      let isCharging = info.ev_battery_charge_start_stopp ?? false;
      setBatteryMaxKWh(maxKWh);

      // Global hard stop at 100% (manual + auto)
      if (pct >= 100 && isCharging) {
        await apiStopCharging();
        isCharging = false;
        setCharging(false);

        if (!fullStopRef.current) {
          fullStopRef.current = true;
          setLogs((prev) => [
            ...prev,
            " Stopping charging... (battery reached 100%)",
            ` Battery reached 100% – charging stopped automatically.`,
          ]);
        }
      }

      setSimHour(h);
      setSimMin(m);
      setCurrentLoad(baseLoad);
      setCurrentPrice(price);
      setChartLoads((prev) => {
        if (prev.length !== MAX_HOURS) {
          return prev.length ? prev : loadsArr;
        }
        if (prev[h] === baseLoad) return prev;
        const next = [...prev];
        next[h] = baseLoad;
        return next;
      });
      setChartPrices((prev) => {
        if (prev.length !== MAX_HOURS) {
          return prev.length ? prev : pricesArr;
        }
        if (prev[h] === price) return prev;
        const next = [...prev];
        next[h] = price;
        return next;
      });
      setBatteryKWh(kWh);
      setBatteryPercent(pct);
      setCharging(isCharging);

      if (!runningRef.current) {
        return;
      }

      // ---- AUTO STRATEGY (LOAD / PRICE) ----
      const reachedTarget = pct >= 100;
      let shouldCharge = false;

      if (!reachedTarget && baseLoad < 11) {
        const strategy = modeRef.current;

        if (strategy === "load") {
          // Load-based: charge whenever below 80% and total load < 11 kW
          shouldCharge = true;
        } else if (strategy === "price") {
          // Price-based: charge only during the 8 cheapest hours
          const pArr = pricesRef.current;
          if (pArr.length === MAX_HOURS) {
            const sortedHours = [...Array(MAX_HOURS).keys()].sort(
              (a, b) => pArr[a] - pArr[b]
            );
            const cheapestSet = new Set(sortedHours.slice(0, 8));
            if (cheapestSet.has(h)) {
              shouldCharge = true;
            }
          }
        }
      }

      if (shouldCharge && !isCharging) {
        await apiStartCharging();
        isCharging = true;
        setCharging(true);
        setLogs((prev) => [...prev, " Starting charging..."]);
      } else if (!shouldCharge && isCharging) {
        await apiStopCharging();
        isCharging = false;
        setCharging(false);
        setLogs((prev) => [...prev, " Stopping charging..."]);
      }

      const info2 = await fetchInfo();
      kWh = info2.battery_capacity_kWh ?? kWh;
      maxKWh =
        info2.battery_max_capacity_kWh ?? maxKWh ?? BATTERY_CAPACITY_KWH;
      if (maxKWh <= 0) {
        maxKWh = BATTERY_CAPACITY_KWH;
      }
      pct = maxKWh > 0 ? (kWh / maxKWh) * 100 : 0;
      isCharging = info2.ev_battery_charge_start_stopp ?? isCharging;
      setBatteryMaxKWh(maxKWh);

      const hourForLog = info2.sim_time_hour ?? h;

      setSimHour(hourForLog);
      setSimMin(info2.sim_time_min ?? m);
      setBatteryKWh(kWh);
      setBatteryPercent(pct);
      setCharging(isCharging);

      if (lastLoggedHourRef.current !== hourForLog) {
        lastLoggedHourRef.current = hourForLog;

        const timeLine = ` Simulated Time: Hour ${formatHour(hourForLog)}`;
        const statusLine = ` Base Load: ${baseLoad.toFixed(
          2
        )} kW |  Price: ${price.toFixed(2)} öre |  Battery: ${pct.toFixed(
          2
        )}% |  Charging: ${isCharging ? "True" : "False"}`;

        setLogs((prev) => [...prev, timeLine, statusLine]);
      }

      if (pct >= 100 || hourForLog >= MAX_HOURS - 1) {
        if (isCharging) {
          await apiStopCharging();
          setCharging(false);
        }
        setRunning(false);
        setLogs((prev) => [
          ...prev,
          ` Final Battery Charge: ${pct.toFixed(2)}%`,
        ]);
      }
    } catch (e) {
      console.error("Poll tick failed", e);
      setRunning(false);
    } finally {
      pollInFlightRef.current = false;
    }
  }

  async function startSimulation() {
    if (!prices.length || !loads.length) {
      alert("Server data not loaded yet.");
      return;
    }

    try {
      await apiDischarge();
      fullStopRef.current = false;
      setLogs([
        `Select mode (load/price): ${mode}`,
        ` Starting Battery Management Simulation in ${mode.toUpperCase()} mode...`,
        "  Discharging battery to 20%...",
        " Loaded electricity prices and base loads for 24h.",
      ]);
      lastLoggedHourRef.current = null;
      setRunning(true);
    } catch (e) {
      console.error("Could not start simulation", e);
    }
  }

  async function stopSimulation() {
    setRunning(false);
    runningRef.current = false;
    fullStopRef.current = false;
    try {
      await apiStopCharging();
      setCharging(false);
      setLogs((prev) => [
        ...prev,
        " Auto simulation manually stopped. Charging halted.",
      ]);
    } catch (e) {
      console.error("Failed to stop simulation", e);
      setLogs((prev) => [
        ...prev,
        " Auto simulation stopped but could not confirm charger shutdown.",
      ]);
    }
  }

  async function manualStart() {
    try {
      await apiStartCharging();

      const info = await fetchInfo();
      const h = info.sim_time_hour ?? simHour;
      const maxKWh =
        info.battery_max_capacity_kWh ??
        batteryMaxRef.current ??
        BATTERY_CAPACITY_KWH;
      const kWh = info.battery_capacity_kWh ?? batteryKWh;

      fullStopRef.current = false;
      setCharging(true);
      setBatteryMaxKWh(maxKWh);
      setBatteryKWh(kWh);
      setBatteryPercent(maxKWh > 0 ? (kWh / maxKWh) * 100 : 0);
      setCurrentLoad(loadsRef.current[h] ?? info.base_current_load ?? 0);
      setCurrentPrice(pricesRef.current[h] ?? 0);

      setLogs((prev) => [...prev, " Starting charging (MANUAL)..."]);
    } catch (e) {
      console.error("Manual start failed", e);
    }
  }

  async function manualStop() {
    try {
      await apiStopCharging();

      const info = await fetchInfo();
      const h = info.sim_time_hour ?? simHour;
      const maxKWh =
        info.battery_max_capacity_kWh ??
        batteryMaxRef.current ??
        BATTERY_CAPACITY_KWH;
      const kWh = info.battery_capacity_kWh ?? batteryKWh;

      setCharging(false);
      runningRef.current = false;
      setBatteryMaxKWh(maxKWh);
      setBatteryKWh(kWh);
      setBatteryPercent(maxKWh > 0 ? (kWh / maxKWh) * 100 : 0);
      setCurrentLoad(loadsRef.current[h] ?? info.base_current_load ?? 0);
      setCurrentPrice(pricesRef.current[h] ?? 0);

      setLogs((prev) => [...prev, " Stopping charging (MANUAL)..."]);
    } catch (e) {
      console.error("Manual stop failed", e);
    }
  }

  async function resetTo20() {
    try {
      setRunning(false);
      await apiDischarge();
      fullStopRef.current = false;
      setLogs((prev) => [
        ...prev,
        "  Battery reset to 20% and clock set to 00:00.",
      ]);
      lastLoggedHourRef.current = null;

      const pct = 20;
      const maxKWh = batteryMaxRef.current || BATTERY_CAPACITY_KWH;
      const kWh = (pct / 100) * maxKWh;
      setBatteryMaxKWh(maxKWh);
      setBatteryPercent(pct);
      setBatteryKWh(kWh);
      setSimHour(0);
      setSimMin(0);
      setCharging(false);
    } catch (e) {
      console.error("Reset failed", e);
    }
  }

  function formatHour(h) {
    return `${String(h).padStart(2, "0")}:00`;
  }


  const clampedPercent = Math.min(Math.max(batteryPercent, 0), 100);
  const hoursRemaining = Math.max((100 - clampedPercent) / 12, 0).toFixed(1);
  const strategyLabel = mode === "price" ? "Price-aware" : "Load-based";

  return (
    <div className="app-root mobile-app">
      {loadingInitial ? (
        <p className="loading-state">Loading server data…</p>
      ) : (
        <div className="layout-shell">
          <aside className="side-rail">
            <div className="logo-pill">GR</div>
            <div className="rail-controls">
              <button className="rail-btn" type="button">
                ←
              </button>
              <button className="rail-btn" type="button">
                ☰
              </button>
              <button className="rail-btn" type="button">
                ⚡
              </button>
              <button className="rail-btn" type="button">
                ⚙︎
              </button>
            </div>
          </aside>

          <main className="main-board">
            <header className="top-nav">
              <div className="tab-group mode-switch" role="group" aria-label="Theme selector">
                <button
                  type="button"
                  className={`soft-tab mode-btn mode-btn-light ${
                    themeMode === "light" ? "active" : ""
                  }`}
                  aria-pressed={themeMode === "light"}
                  onClick={() => setThemeMode("light")}
                >
                  <span className="mode-text">
                    <span>Light</span>
                    <small>Mode</small>
                  </span>
                  <span className="mode-icon" aria-hidden="true">
                    ☀️
                  </span>
                </button>
                <button
                  type="button"
                  className={`soft-tab mode-btn mode-btn-dark ${
                    themeMode === "dark" ? "active" : ""
                  }`}
                  aria-pressed={themeMode === "dark"}
                  onClick={() => setThemeMode("dark")}
                >
                  <span className="mode-text">
                    <span>Dark</span>
                    <small>Mode</small>
                  </span>
                  <span className="mode-icon" aria-hidden="true">
                    🌙
                  </span>
                </button>
              </div>
              <div
                className={`location-chip ${
                  userLocation && !userLocation.includes("Unknown")
                    ? "active"
                    : ""
                }`}
              >
                <span className="loc-dot" />
                Your location: {userLocation}
              </div>
            </header>

            <div className="hero-wrap single-card">
                <div className="hero-background">
                  <div className="car-stage">
                    <CarScene rotationAngle={ringAngle} />
                  </div>
                </div>
              <div className="hero-content">
                <section className="hero-info hero-panel hero-label-card">
                  <p className="eyebrow">Pulse</p>
                  <h1>Smart EV Control</h1>
                  <p className="subhead">Adaptive charging system</p>
                </section>

                <div className="status-floating card glass-card hero-strategy-card">
                  <div className="card-headline">
                    <div>
                      <p className="card-label">Strategy</p>
                      <h3>Charging mode</h3>
                    </div>
                    <span className="chip-mode">{strategyLabel}</span>
                  </div>
                  <p className="card-helper">
                    Choose the plan the automation engine should follow.
                  </p>
                  <div className="control-options pill stacked">
                    <label className="radio-option">
                      <input
                        type="radio"
                        value="load"
                        checked={mode === "load"}
                        onChange={() => setMode("load")}
                      />
                      <span>Load-based</span>
                    </label>
                    <label className="radio-option">
                      <input
                        type="radio"
                        value="price"
                        checked={mode === "price"}
                        onChange={() => setMode("price")}
                      />
                      <span>Price-aware</span>
                    </label>
                  </div>
                  <div className="time-display compact highlight">
                    <p>Simulated time</p>
                    <strong>{formatHour(simHour)}</strong>
                    <span>{String(simMin).padStart(2, "0")} min elapsed</span>
                  </div>
                  <div className="strategy-note">
                    Auto mode will respect this setting during the 24h run.
                  </div>
                </div>
              </div>
            </div>

            <section className="deck-grid expanded">
              <article className="card deck-card metric-card">
                <div className="card-headline stacked">
                  <div>
                    <p className="card-label">Live metrics</p>
                    <h3>Power snapshot</h3>
                  </div>
                </div>
                <div className="metric-cluster">
                  <div className="metric-item">
                    <p>Current price</p>
                    <strong>{currentPrice.toFixed(2)}</strong>
                    <span>öre/kWh</span>
                  </div>
                  <div className="metric-item">
                    <p>Current load</p>
                    <strong>{currentLoad.toFixed(2)}</strong>
                    <span>kW</span>
                  </div>
                  <div className="metric-item">
                    <p>Battery energy</p>
                    <strong>{batteryKWh.toFixed(1)}</strong>
                    <span>kWh stored</span>
                  </div>
                </div>
                <p className="card-helper">
                  Track the live price, load, and stored energy.
                </p>
              </article>

              <article className="card deck-card status-card deck-status-card">
                <div className="status-card-header">
                  <p className="card-label">Charging</p>
                  <span className={`status-dot ${charging ? "on" : "off"}`}>
                    {charging ? "Running" : "Idle"}
                  </span>
                </div>
                <div className="battery-visual">
                  <div className="battery-shell">
                    <div
                      className="battery-fill"
                      style={{ width: `${clampedPercent}%` }}
                    />
                    <div className="battery-cap" />
                  </div>
                  <div className={`battery-pulse ${charging ? "on" : ""}`} />
                </div>
                <div className="mode-pill floating">
                  {running ? `Auto · ${strategyLabel}` : "Manual control"}
                </div>
                <div className="battery-mini">
                  <div className={`battery-icon ${charging ? "on" : ""}`}>
                    <span />
                  </div>
                  <div>
                    <p>Battery</p>
                    <strong>{batteryPercent.toFixed(0)}%</strong>
                  </div>
                  <span className="chip-remaining">{hoursRemaining}h</span>
                </div>
                <div className="status-pairs">
                  <div>
                    <p>Simulated time</p>
                    <strong>{formatHour(simHour)}</strong>
                    <span>{String(simMin).padStart(2, "0")} min</span>
                  </div>
                  <div>
                    <p>Charging state</p>
                    <strong>{charging ? "Running" : "Standby"}</strong>
                    <span>{running ? "Auto" : "Manual"}</span>
                  </div>
                </div>
                <div className="status-meta">
                  <div>
                    <p>Current price</p>
                    <strong>{currentPrice.toFixed(2)}</strong>
                    <span>öre / kWh</span>
                  </div>
                  <div>
                    <p>Current load</p>
                    <strong>{currentLoad.toFixed(2)}</strong>
                    <span>kW</span>
                  </div>
                </div>
                <div className="status-actions">
                  <button
                    className="pill-btn solid"
                    onClick={manualStart}
                    disabled={charging}
                  >
                    Start charge
                  </button>
                  <button
                    className="pill-btn ghost"
                    onClick={manualStop}
                    disabled={!charging}
                  >
                    Stop charge
                  </button>
                </div>
                <button
                  className="pill-btn outline full-width"
                  onClick={resetTo20}
                >
                  Reset battery to 20%
                </button>
              </article>

              <article className="card deck-card controls-card">
                <div className="card-headline">
                  <div>
                    <p className="card-label">Automation</p>
                    <h3>24h Simulation</h3>
                  </div>
                  <span className={`status-dot ${running ? "on" : "off"}`}>
                    {running ? "Running" : "Idle"}
                  </span>
                </div>
                <p className="card-helper">
                  Run an automated cycle using the {strategyLabel} profile.
                </p>
                <div className="control-stat-grid">
                  <div>
                    <p>Battery</p>
                    <strong>{batteryPercent.toFixed(0)}%</strong>
                    <span>{hoursRemaining}h remaining</span>
                  </div>
                  <div>
                    <p>Simulated hour</p>
                    <strong>{formatHour(simHour)}</strong>
                    <span>{String(simMin).padStart(2, "0")} min</span>
                  </div>
                </div>
                <div className="action-buttons stretch">
                  <button
                    className="pill-btn solid"
                    onClick={startSimulation}
                    disabled={running}
                  >
                    Start auto 24h
                  </button>
                  <button
                    className="pill-btn ghost"
                    onClick={stopSimulation}
                    disabled={!running}
                  >
                    Stop auto
                  </button>
                </div>
                <p className="card-note">
                  Auto session stops at 100% charge or hour 24 — whichever comes
                  first.
                </p>
              </article>
            </section>

            <section className="insights-secondary">
              <article className="card insight-card chart-card">
                <div className="chart-head">
                  <div>
                    <p className="card-label">24h outlook</p>
                    <h3>Price vs load</h3>
                  </div>
                  <span className="badge-soft">
                    {formatHour(simHour)} · hour {simHour + 1}
                  </span>
                </div>
                <PriceChart
                  prices={chartPrices}
                  loads={chartLoads}
                  currentHour={simHour}
                  themeMode={themeMode}
                />
                <div className="chart-legend">
                  <div className="legend-item">
                    <span className="legend-dot price" />
                    <div>
                      <p>Price</p>
                      <strong>
                        {(
                          chartPrices[simHour] ?? currentPrice
                        ).toFixed(2)} öre/kWh
                      </strong>
                    </div>
                  </div>
                  <div className="legend-item">
                    <span className="legend-dot load" />
                    <div>
                      <p>Base load</p>
                      <strong>
                        {(chartLoads[simHour] ?? currentLoad).toFixed(2)} kW
                      </strong>
                    </div>
                  </div>
                </div>
              </article>

              <article className="card insight-card log-card">
                <div className="chart-head">
                  <div>
                    <p className="card-label">Activity</p>
                    <h3>Session log</h3>
                  </div>
                  <span className="badge-soft neutral">
                    {logs.length ? "Live feed" : "Waiting"}
                  </span>
                </div>
                <div className="log-lines">
                  {logs.length ? (
                    logs.slice(-12).map((line, idx) => (
                      <p key={`${line}-${idx}`} className="log-item">
                        {line}
                      </p>
                    ))
                  ) : (
                    <p className="log-empty">
                      No activity recorded yet. Start a session to see updates.
                    </p>
                  )}
                </div>
              </article>

              <article className="card insight-card note-card">
                <div className="chart-head">
                  <div>
                    <p className="card-label">Information</p>
                    <h3>Disclaimer</h3>
                  </div>
                </div>
                <p className="note-text">
                  <strong>English:</strong> This EV Charging Control System is a
                  non-commercial demo project built for learning and portfolio
                  purposes. No real vehicles or charging hardware are
                  connected. The app does not store personal data beyond basic,
                  anonymous usage logs for debugging. Do not use this system to
                  control any real charging equipment.
                </p>
              </article>
            </section>
          </main>
        </div>
      )}
    </div>
  );
}
