# F1 Track Master 2026 — PWA

Upload the contents of this folder to any static HTTPS host.

Files:
- index.html — game
- manifest.webmanifest — PWA metadata
- sw.js — service worker
- icon-192.png / icon-512.png — app icons

On iPhone:
1. Open the HTTPS site in Safari.
2. Tap Share.
3. Tap Add to Home Screen.
4. Tap Add.

The app then launches full-screen like a lightweight native app.

For best offline behavior, the app shell works without network. Circuit photos are fetched from Wikimedia when available; the embedded circuit-map fallback remains available if a photo cannot load.

Important: service workers/PWA installation require HTTPS (localhost is also allowed during development). A file opened directly from the Files app cannot install a PWA.
