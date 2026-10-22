// bootstrap.js — injected by edit_server.py.
// Auto-load the served SVG, and rebind Ctrl/Cmd+S to save it back in place.
(function () {
  // Method Draw declares `svgCanvas` as a top-level `const` (a global lexical
  // binding), NOT as a property of window — so check the bare identifier, not
  // window.svgCanvas. The try/catch guards the temporal dead zone before
  // modals.js has run.
  function ready(cb) {
    try {
      if (typeof svgCanvas !== "undefined" && svgCanvas &&
          typeof svgCanvas.setSvgString === "function" &&
          typeof svgCanvas.getSvgString === "function") return cb();
    } catch (e) { /* svgCanvas not initialized yet */ }
    setTimeout(function () { ready(cb); }, 100);
  }

  function note(msg, ok) {
    var d = document.getElementById("md-save-note");
    if (!d) {
      d = document.createElement("div");
      d.id = "md-save-note";
      d.style.cssText =
        "position:fixed;left:50%;top:12px;transform:translateX(-50%);" +
        "padding:6px 14px;border-radius:4px;font:13px sans-serif;" +
        "z-index:99999;color:#fff;transition:opacity .3s;";
      document.body.appendChild(d);
    }
    d.textContent = msg;
    d.style.background = ok ? "#2e7d32" : "#c62828";
    d.style.opacity = "1";
    clearTimeout(d._t);
    d._t = setTimeout(function () { d.style.opacity = "0"; }, 1500);
  }

  function saveBack() {
    var svg = svgCanvas.getSvgString();
    fetch("/save", {
      method: "POST",
      headers: { "Content-Type": "image/svg+xml" },
      body: svg
    })
      .then(function (r) { note(r.ok ? "Saved" : "Save failed", r.ok); })
      .catch(function () { note("Save failed", false); });
  }

  ready(function () {
    fetch("/figure.svg")
      .then(function (r) {
        if (!r.ok) throw new Error("HTTP " + r.status);
        return r.text();
      })
      .then(function (t) { svgCanvas.setSvgString(t); })
      .catch(function () { note("Load failed", false); });

    document.addEventListener("keydown", function (e) {
      var isS = e.key === "s" || e.key === "S";
      if (isS && (e.ctrlKey || e.metaKey)) {
        e.preventDefault();
        e.stopPropagation();
        saveBack();
      }
    }, true);
  });
})();
