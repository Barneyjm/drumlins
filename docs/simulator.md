---
hide:
  - toc
---

# Simulator

An interactive toy of the bed instability. Drag the sliders for ice flow direction, ice speed, ice viscosity, till–water coupling (Π) and growth time, and watch a field of bumps grow into ribs or streamlined drumlins. On a phone, the map stays pinned at the top while you scroll the controls.

<iframe id="sim-frame" src="../sim/index.html" title="Drumlin field simulator" loading="lazy" style="width:100%;height:1250px;border:0;border-radius:8px;"></iframe>

<script>
(function () {
  var f = document.getElementById("sim-frame");
  function scheme() { return document.body.getAttribute("data-md-color-scheme") === "slate" ? "dark" : "light"; }
  function sendTheme() { try { f.contentWindow.postMessage({ theme: scheme() }, "*"); } catch (e) {} }
  function fit() {
    try {
      if (window.innerWidth < 860) {            // phones: fixed-height frame that scrolls inside, so the map can stay pinned
        f.style.height = (window.innerHeight - 56) + "px";
        f.setAttribute("scrolling", "yes");
        return;
      }
      var d = f.contentWindow.document;
      f.style.height = Math.max(d.documentElement.scrollHeight, d.body.scrollHeight) + "px";
    } catch (e) {}
  }
  f.addEventListener("load", function () {
    fit(); sendTheme();
    try { new ResizeObserver(fit).observe(f.contentWindow.document.body); } catch (e) {}
  });
  window.addEventListener("resize", fit);
  new MutationObserver(sendTheme).observe(document.body, { attributes: true, attributeFilter: ["data-md-color-scheme"] });
})();
</script>

[Open full screen](sim/index.html){ .md-button }

The simulator is illustrative. Its growth rates follow the linear instability described in [Stage 1](stage-1-size.md). It does not include the within-field lengthening described in [Stage 2](stage-2-lengthening.md).
