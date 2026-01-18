// ==UserScript==
// @name         Loop Detector + Auto Next (YT/IG/TikTok) → Flask
// @namespace    joel
// @version      1.1
// @description  Detect loops, send to Flask, and auto-click next video depending on website
// @match        *://*/*
// @grant        GM_xmlhttpRequest
// @connect      127.0.0.1
// ==/UserScript==

(function () {
  "use strict";

  const INTERVAL_MS = 200;
  const NEXT_COOLDOWN_MS = 1200; // minimum gap between next-clicks
  let lastTime = 0;
  let lastAdvanceAt = 0;

  console.log("[LoopDetector] Script loaded:", window.location.href);

  // -----------------------
  // SEND TO FLASK
  // -----------------------
  function sendLoopToFlask(val) {
    GM_xmlhttpRequest({
      method: "POST",
      url: "http://127.0.0.1:5000/sample",
      headers: { "Content-Type": "application/json" },
      data: JSON.stringify({ value: val }),
    });
  }

  function sendProgressToFlask(currentTime, duration) {
    GM_xmlhttpRequest({
      method: "POST",
      url: "http://127.0.0.1:5000/progress",
      headers: { "Content-Type": "application/json" },
      data: JSON.stringify({ currentTime: currentTime, duration: duration }),
    });
  }

  // -----------------------
  // GET CURRENT VIDEO
  // (works for IG + YT + TikTok)
  // -----------------------
  function getActiveVideo() {
    const videos = Array.from(document.querySelectorAll("video"));

    const playing = videos.find(
      (v) => !v.paused && v.currentTime > 0 && v.readyState >= 2
    );
    if (playing) return playing;

    return videos.find((v) => v.offsetParent !== null) || null;
  }

  // -----------------------
  // AUTO CLICK NEXT BUTTON
  // -----------------------
  function clickNextPlatform() {
    const url = window.location.href;

    // --- YOUTUBE ---
    if (url.includes("youtube.com")) {
      const btn = document.querySelector('button[aria-label="Next video"]');
      if (btn) {
        console.log("[LoopDetector] Clicking YouTube Next button");
        btn.click();
      }
      return;
    }

    // --- INSTAGRAM ---
    if (url.includes("instagram.com")) {
      const btn = document.querySelector('div[aria-label="Navigate to next Reel"]');
      if (btn) {
        console.log("[LoopDetector] Clicking Instagram Next Reel button");
        btn.click();
      }
      return;
    }

    // --- TIKTOK ---
    if (url.includes("tiktok.com")) {
      // There are multiple TUX buttons — we want the 2nd one
      const btns = Array.from(document.querySelectorAll(
        'button.TUXButton.TUXButton--capsule.TUXButton--medium.TUXButton--secondary.action-item.css-16m89jc'
      ));

      if (btns.length >= 2) {
        console.log("[LoopDetector] Clicking TikTok Next button (2nd instance)");
        btns[1].click();
      }
      return;
    }

    // Other sites (do nothing)
  }

  // -----------------------
  // MAIN LOOP
  // -----------------------
  setInterval(() => {
    const video = getActiveVideo();
    if (!video) {
      lastTime = 0;
      return;
    }

    const t = video.currentTime;
    const d = video.duration;

	// Create/update progress display element
	let progressDisplay = document.getElementById("loop-detector-progress");
	if (!progressDisplay) {
		progressDisplay = document.createElement("div");
		progressDisplay.id = "loop-detector-progress";
		progressDisplay.style.cssText =
			"position: fixed; top: 10px; left: 10px; background: rgba(0,0,0,0.7); color: #fff; padding: 8px 12px; border-radius: 4px; font-size: 14px; z-index: 9999; font-family: Arial, sans-serif;";
		document.body.appendChild(progressDisplay);
	}

	const percentage = Math.round((t / d) * 100);
	progressDisplay.textContent = `${percentage}%`;

    if (!d || d === Infinity) {
      lastTime = t;
      return;
    }

    sendProgressToFlask(t, d);

    // LOOP DETECTED: currentTime dropped
    if (t < lastTime - 1) { // used to be 0.05
      const now = Date.now();
      // Cooldown: prevent rapid double-advance
      const tooSoon = now - lastAdvanceAt < NEXT_COOLDOWN_MS;

      if (tooSoon) {
        // skip to avoid double scroll
        lastTime = t;
        return;
      }

      console.log("%c[LoopDetector] LOOP detected!", "color: #00b050");

      sendLoopToFlask("loop");
      clickNextPlatform();

      lastAdvanceAt = now;
    }

    lastTime = t;
  }, INTERVAL_MS);
})();
