// src/api/evApi.js
import axios from "axios";

const BASE_URL = "http://127.0.0.1:5000";

function safeJson(resp) {
  // If backend returns plain JSON (list or dict), axios puts it in resp.data
  return resp.data;
}

// ---- basic fetch helpers ----
export async function fetchPrices() {
  const resp = await axios.get(`${BASE_URL}/priceperhour`);
  return safeJson(resp); // [24 numbers]
}

export async function fetchBaseload() {
  const resp = await axios.get(`${BASE_URL}/baseload`);
  return safeJson(resp); // [24 numbers]
}

export async function fetchInfo() {
  const resp = await axios.get(`${BASE_URL}/info`);
  return safeJson(resp); // {sim_time_hour, base_current_load, battery_capacity_kWh, ev_battery_charge_start_stopp}
}

export async function fetchBatteryPercent() {
  const resp = await axios.get(`${BASE_URL}/charge`);
  return safeJson(resp); // number or simple JSON
}

// ---- control endpoints ----
export async function apiStartCharging() {
  const resp = await axios.post(`${BASE_URL}/charge`, { charging: "on" });
  return safeJson(resp);
}

export async function apiStopCharging() {
  const resp = await axios.post(`${BASE_URL}/charge`, { charging: "off" });
  return safeJson(resp);
}

export async function apiDischarge() {
  const resp = await axios.post(`${BASE_URL}/discharge`, { discharging: "on" });
  return safeJson(resp);
}