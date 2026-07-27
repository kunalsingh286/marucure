# MaruCure: Silicosis Early Detection & Screening Engine

**Winner/Submission for the Rajasthan Innovation Challenge: Occupational Lung Disease Tech**

MaruCure is an enterprise-grade Progressive Web Application (PWA) and Field-to-Cloud ecosystem explicitly designed to solve the critical bottlenecks of rural Silicosis screening in Rajasthan's mining corridors: **zero internet connectivity** and **sluggish bureaucratic welfare routing**.

---

## 🏆 The Core Problem Solved
Traditional screening requires heavy desktop machines and immediate cloud connectivity. MaruCure shifts the entire diagnostic burden to the edge, running 100% locally on low-cost devices deep inside zero-connectivity sandstone pits.

### 1. Edge AI Radiology (No Internet Required)
We compiled a custom **2.9 MB Quantized INT8 TensorFlow Lite model** (`silicosis_detector.tflite`). Utilizing advanced WebAssembly (WASM) multi-threading and JS-Interop, MaruCure parses raw chest X-ray image matrices directly inside the browser tab's RAM. It generates a structural tissue-damage probability score and a live **Grad-CAM visual anomaly heatmap** locally in under 30 seconds.

### 2. Live Hardware Telemetry (Web-Bluetooth)
Bypassing falsifiable manual text entry, our Web-Dashboard utilizes the native **Web-Bluetooth GATT API**. It actively pairs with physical digital spirometers over the air, capturing live binary exhale packets to dynamically compute the critical $FEV_1/FVC$ ratio and chart a real-time obstructive breathing curve on the dashboard.

### 3. Indestructible Local Persistence (IndexedDB)
Because mining camps suffer from sudden power outages and harsh conditions, every single data point is instantly saved to the browser's native **IndexedDB transactional database**. If the laptop crashes mid-screening, zero medical data is lost.

---

## ⚙️ The "Air-Gapped" Mock Architecture (For Live Testing)
To respect Rajasthan state cybersecurity laws, we do not bundle live production keys (Jan Aadhaar 2.0 / Raj-SSO) with this prototype. Instead, we built a **High-Fidelity Mock Sandbox** directly into the repository so evaluators can physically test the software.

### How to Run the "Faraday Cage" Test
1. Disconnect your machine from the internet (Turn off Wi-Fi).
2. Start the local server and open the MaruCure dashboard.
3. Toggle the **Hardware Emulator** switch on the top right (this bypasses the native Bluetooth search and injects a live 5-second simulated FEV1/FVC breath curve).
4. Drag and drop a chest X-ray onto the canvas to execute the WASM AI inference offline.
5. Notice that the record saves flawlessly to the "Pending Sync" Outbox queue on the left panel. **Zero data is lost.**

### How to Run the "Network Recovery" Test
1. Turn your Wi-Fi back on.
2. The Go (Golang) Backend mock server is equipped with a **Chaos Engineering Throttler** that deliberately injects 1-3 seconds of latency and randomly drops 15% of requests with a `503 Service Unavailable` flag to simulate poor rural cellular networks.
3. Click **"Sync to SDC (Outbox)"** on the frontend.
4. Watch as the robust background worker iteratively retries failed connections, gracefully transitioning records from an orange "Pending" hourglass to a green "Synced" checkmark as the batch clears our Goroutine multiplexer.

---

## 🚀 Technical Stack
* **Frontend:** Flutter Web (Dart 3.0), PWA Service Workers, IndexedDB (`idb_shim`), Web-Bluetooth API, TFJS Interop (`dart:js_util`).
* **Backend:** Go (Golang) 1.20+, Chi Router, High-Concurrency Goroutine Pools, Hybrid AES-GCM / RSA-OAEP Encryption hooks (`backend_sync/internal/crypto`).
* **Infrastructure Target:** PostgreSQL 15, S3 Object Storage, Rajasthan State Data Centre (SDC) API Gateways.

---

## 🔐 State Gateway Integration Readiness
MaruCure is not a superficial concept sheet. It is structurally "Plug-and-Play" ready for the State Data Centre.
Our Go backend features an isolated environmental switch box (`production_env.json`) explicitly programmed to handle the DoIT&C mandated **Hybrid AES/RSA Sign-and-Encrypt handshakes**. 

The moment official `APP_CODE`, `SCHEME_CODE`, and `SEWADWAAR_PUBLIC_KEY` client secrets are provisioned by the state, the mock gateway detaches, and MaruCure instantly bridges field diagnostics into the live Rajasthan welfare network with **zero architectural code changes**.
