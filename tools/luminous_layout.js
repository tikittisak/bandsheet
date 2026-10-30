// Alpha.2 P0: geometry changes must never render song data or persist view state.
var LAYOUT_FRAME = 0;
function updateLayout() {
  // Safari pinch zoom changes the visual viewport, not the intended chart layout.
  // Page Zoom can still change layout viewport width with visual scale === 1.
  var viewport = window.visualViewport;
  if (viewport && Math.abs(viewport.scale - 1) > 0.01) return;
  updateCellWidthCore();
  document.dispatchEvent(new Event('bandsheet:layout'));
}
function scheduleLayout() {
  if (LAYOUT_FRAME) return;
  LAYOUT_FRAME = requestAnimationFrame(function () {
    LAYOUT_FRAME = 0;
    updateLayout();
  });
}
window.addEventListener('resize', scheduleLayout, { passive: true });
if (window.visualViewport) {
  window.visualViewport.addEventListener('resize', scheduleLayout, { passive: true });
}
