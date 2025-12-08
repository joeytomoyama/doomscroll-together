(function () {
  // CHANGE THIS to the element you want to read
  const SELECTOR = "my-tag"; 
  // e.g. "#price", "span.value", "input[name='foo']"

	function extractValue() {
		const el = document.querySelector(".ytPlayerProgressBarDragContainer");
		if (!el) {
			console.log("[FlaskSync] Element not found");
			return null;
		}

		const value = el.getAttribute("aria-valuenow");
		console.log("[FlaskSync] aria-valuenow =", value);
		return value;
	}


  function sendValue(value) {
    fetch("http://127.0.0.1:5000/sample", {
      method: "POST",
      headers: {
        "Content-Type": "application/json"
      },
      body: JSON.stringify({ value })
    }).catch((err) =>
      console.error("[Send Tag to Flask] Error:", err)
    );
  }

  // Send every second
  setInterval(() => {
    const value = extractValue();
	// const value = "test haha"
	console.log("value:", value);
    if (value !== null) {
      sendValue(value);
    }
  }, 1000); // 1000 ms = 1 second
})();
