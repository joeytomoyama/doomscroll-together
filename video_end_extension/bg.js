// Forward messages from content scripts to your local HTTP endpoint.
const ENDPOINT = "http://127.0.0.1:17865/ended";

browser.runtime.onMessage.addListener(async (msg, sender) => {
  if (!msg || msg.type !== "SVD_ENDED") return;

  try {
    const res = await fetch(ENDPOINT, {
      method: "POST",
      headers: {"Content-Type": "application/json"},
      body: JSON.stringify(msg.payload)
    });
    console.log("[SVD] POST ->", ENDPOINT, res.status);
  } catch (e) {
    console.error("[SVD] POST failed:", e);
  }
});
