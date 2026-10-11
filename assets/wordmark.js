// Rotating wordmark. The names live in index.html as .wm-n elements; add a name by
// adding a line there. The anchor name (is-anchor) returns before every group of
// EVERY names, then the loop starts over.
(function () {
  var wm = document.querySelector('.wordmark');
  if (!wm) return;
  var names = Array.prototype.slice.call(wm.querySelectorAll('.wm-n'));
  var btn = document.querySelector('.wm-toggle');
  if (names.length < 2) return;

  var HOLD_ANCHOR = 2600, HOLD = 1600, FADE = 600, EVERY = 3, LOOPS = 1, CUSHION = 6;
  var reduce = window.matchMedia('(prefers-reduced-motion: reduce)');
  var anchor = Math.max(0, names.findIndex(function (n) { return n.classList.contains('is-anchor'); }));
  var alts = names.filter(function (n, j) { return j !== anchor; });

  // Build the play order: anchor, three names, anchor, three names, ...
  var order = [];
  alts.forEach(function (n, j) {
    if (j % EVERY === 0) order.push(anchor);
    order.push(names.indexOf(n));
  });

  // Alternate names share one size, fitted so the longest sits CUSHION px inside
  // "Historical Society" on each side, and never as large as the anchor.
  var namesBox = wm.querySelector('.wm-names');
  var tail = wm.querySelector('.wm-tail');
  function textWidth(el) {
    var r = document.createRange(); r.selectNodeContents(el);
    return r.getBoundingClientRect().width;
  }
  function fit() {
    if (!tail) return;
    var target = textWidth(tail) - 2 * CUSHION;
    var a = names[anchor];
    // Anchor: keep its CSS size, track the letters out until the word spans the target.
    namesBox.style.removeProperty('--wm-anchor-ls');
    var aSize = parseFloat(getComputedStyle(a).fontSize);
    var ls0 = parseFloat(getComputedStyle(a).letterSpacing) || 0;
    var letters = a.textContent.trim().length;
    var visible = textWidth(a) - ls0;               // drop the trailing letter-space
    var ls = Math.max(ls0, ls0 + (target - visible) / Math.max(1, letters - 1));
    namesBox.style.setProperty('--wm-anchor-ls', ls.toFixed(2) + 'px');
    if (!alts.length) return;
    // Alternates: one shared size, set by the longest single-word name and kept well
    // below the anchor. A multi-word name that still overruns gets its own smaller size.
    alts.forEach(function (n) { n.style.removeProperty('font-size'); });
    alts.forEach(function (n) { n.classList.remove('is-long'); });
    var setters = alts.filter(function (n) { return n.textContent.trim().indexOf(' ') < 0; });
    if (!setters.length) setters = alts;
    for (var pass = 0; pass < 2; pass++) {          // second pass corrects non-linear glyph scaling
      var base = parseFloat(getComputedStyle(setters[0]).fontSize);
      var widest = Math.max.apply(null, setters.map(textWidth));
      var size = Math.min(base * target / widest, aSize * 0.68);   // shared size is about two-thirds of Iroko
      namesBox.style.setProperty('--wm-alt-size', size.toFixed(2) + 'px');
    }
    alts.forEach(function (n) {
      if (textWidth(n) > target + 0.5) n.classList.add('is-long');   // tighter tracking first
      for (var pass = 0; pass < 2; pass++) {
        var w = textWidth(n);
        if (w <= target + 0.5) break;
        n.style.fontSize = (parseFloat(getComputedStyle(n).fontSize) * target / w).toFixed(2) + 'px';
      }
    });
  }
  fit();
  if (document.fonts && document.fonts.ready) document.fonts.ready.then(fit);
  window.addEventListener('resize', fit);

  // Tradition labels: one per name, built from data-trad, cross-fading with the names.
  var tradBox = document.querySelector('.wm-trad');
  var trads = names.map(function (n) {
    var t = document.createElement('span');
    t.setAttribute('aria-hidden', 'true');
    t.textContent = n.getAttribute('data-trad') || '';
    if (n.classList.contains('is-anchor')) t.className = 'is-anchor';
    if (tradBox) tradBox.appendChild(t);
    return t;
  });

  var pos = 0, loops = 0, timer = null, paused = false;
  // bare: show the name with no tradition label (the resting Iroko carries none)
  function show(k, bare) {
    names.forEach(function (n, j) { n.classList.toggle('is-on', j === k); });
    trads.forEach(function (t, j) { t.classList.toggle('is-on', !bare && j === k); });
  }
  function setBtn(playing) {
    if (!btn) return;
    btn.setAttribute('aria-pressed', playing ? 'false' : 'true');
    btn.setAttribute('aria-label', playing ? 'Pause name rotation' : 'Play name rotation');
  }
  function settle() { clearTimeout(timer); timer = null; paused = true; pos = 0; show(anchor, true); setBtn(false); }
  function step() {
    var hold = order[pos] === anchor ? HOLD_ANCHOR : HOLD;
    timer = setTimeout(function () {
      pos = (pos + 1) % order.length;
      if (pos === 0 && ++loops >= LOOPS) { settle(); return; }
      show(order[pos]); step();
    }, hold + FADE);
  }
  function play() { paused = false; loops = 0; pos = 0; show(order[0]); setBtn(true); clearTimeout(timer); step(); }

  wm.classList.add('is-live');
  show(anchor, true);
  if (btn) {
    btn.hidden = false;
    btn.addEventListener('click', function () { paused ? play() : settle(); });
  }
  if (reduce.matches) { settle(); return; }
  document.addEventListener('visibilitychange', function () {
    if (document.hidden) { clearTimeout(timer); timer = null; }
    else if (!paused && !timer) { step(); }
  });
  play();
})();
