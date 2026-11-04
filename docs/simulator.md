---
hide:
  - toc
---

# Simulator

An interactive toy of the bed instability. Drag the sliders for ice speed, ice viscosity, till–water coupling (Π) and growth time, and watch a field of bumps grow into ribs or streamlined drumlins.

<iframe id="sim-frame" src="../sim/index.html" title="Drumlin field simulator" loading="lazy" style="width:100%;height:1250px;border:0;border-radius:8px;"></iframe>

<script>
(function () {
  var f = document.getElementById("sim-frame");
  function fit() {
    try {
      var d = f.contentWindow.document;
      f.style.height = Math.max(d.documentElement.scrollHeight, d.body.scrollHeight) + "px";
    } catch (e) {}
  }
  f.addEventListener("load", function () {
    fit();
    try { new ResizeObserver(fit).observe(f.contentWindow.document.body); } catch (e) {}
  });
  window.addEventListener("resize", fit);
})();
</script>

[Open full screen](sim/index.html){ .md-button }

The simulator is illustrative. Its growth rates follow the linear instability described in [Stage 1](stage-1-size.md); it does not include the within-field lengthening found in [Stage 2](stage-2-lengthening.md).
