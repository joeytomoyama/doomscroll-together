console.log("[SVD] content script loaded on", location.href);

function sendEnded(info) {
  const payload = { url: location.href, ts: Date.now(), ...info };
  console.log("[SVD] ended/loop signal", payload);
  browser.runtime.sendMessage({ type: "SVD_ENDED", payload });
}

function attachToVideo(v) {
  if (!v || v._svdAttached) return;
  v._svdAttached = true;
  console.log("[SVD] attaching to <video>", v);

  v.addEventListener("ended", () => {
    const dur = Number.isFinite(v.duration) ? v.duration : null;
    sendEnded({ reason: "ended_event", duration: dur, loop: !!v.loop });
  });

  let lastTime = 0;
  v.addEventListener("timeupdate", () => {
    const dur = Number.isFinite(v.duration) ? v.duration : NaN;
    const t = v.currentTime || 0;
    if (Number.isFinite(dur) && dur > 1 && t >= dur - 0.15) v._nearEndSeen = true;
    if (v._nearEndSeen && t < 0.2 && lastTime > 0.5) {
      v._nearEndSeen = false;
      sendEnded({ reason: "loop_reset", duration: Number.isFinite(dur) ? dur : null });
    }
    lastTime = t;
  });

  const reset = () => { v._nearEndSeen = false; };
  v.addEventListener("loadeddata", reset);
  v.addEventListener("emptied", reset);
}

function scan() {
  const vids = document.querySelectorAll("video");
  if (vids.length) console.log(`[SVD] found ${vids.length} <video> element(s)`);
  vids.forEach(attachToVideo);
}

const mo = new MutationObserver(scan);
mo.observe(document.documentElement, { subtree: true, childList: true });
scan();

// Optional: report feed auto-advances that change the URL.
let lastHref = location.href;
setInterval(() => {
  if (location.href !== lastHref) {
    lastHref = location.href;
    sendEnded({ reason: "url_changed" });
  }
}, 500);

// Quick manual test hook: press Shift+E to simulate an 'ended' ping
window.addEventListener("keydown", (e) => {
  if (e.shiftKey && e.key.toLowerCase() === "e") {
    sendEnded({ reason: "manual_test" });
  }
});
