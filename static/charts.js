/* رندر نمودارهای SVG — بدون هیچ وابستگی خارجی */
(function (global) {
  'use strict';
  var PALETTE = ['#e91e63', '#2563eb', '#16a34a', '#d97706', '#7c3aed', '#0891b2',
    '#dc2626', '#4d7c0f', '#be185d', '#475569', '#b45309', '#0f766e'];

  function faNum(v) {
    return String(v).replace(/\d/g, function (d) { return '۰۱۲۳۴۵۶۷۸۹'[d]; });
  }
  function fmt(v) { return faNum(Number(v || 0).toLocaleString('en-US')); }

  function el(tag, attrs, text) {
    var e = document.createElementNS('http://www.w3.org/2000/svg', tag);
    for (var k in attrs) e.setAttribute(k, attrs[k]);
    if (text != null) e.textContent = text;
    return e;
  }

  function svgRoot(w, h) {
    var s = el('svg', { viewBox: '0 0 ' + w + ' ' + h, width: '100%' });
    // صفحه RTL است؛ برای درست کار کردن text-anchor باید SVG صریحاً LTR باشد
    s.setAttribute('direction', 'ltr');
    return s;
  }

  // ---------------- دونات ----------------
  function donut(ch, box) {
    var vals = ch.values, labels = ch.labels, total = ch.total || vals.reduce(function (a, b) { return a + b; }, 0) || 1;
    var W = 380, H = 210, cx = 115, cy = 105, r = 78, ir = 46, a0 = -Math.PI / 2;
    var svg = svgRoot(W, H);
    var sum = 0;
    vals.forEach(function (v, i) {
      var frac = v / total; if (frac <= 0) return;
      var a1 = a0 + frac * Math.PI * 2;
      var large = frac > 0.5 ? 1 : 0;
      var x0 = cx + r * Math.cos(a0), y0 = cy + r * Math.sin(a0);
      var x1 = cx + r * Math.cos(a1), y1 = cy + r * Math.sin(a1);
      var xi1 = cx + ir * Math.cos(a1), yi1 = cy + ir * Math.sin(a1);
      var xi0 = cx + ir * Math.cos(a0), yi0 = cy + ir * Math.sin(a0);
      var d = 'M' + x0 + ',' + y0 + ' A' + r + ',' + r + ' 0 ' + large + ' 1 ' + x1 + ',' + y1 +
        ' L' + xi1 + ',' + yi1 + ' A' + ir + ',' + ir + ' 0 ' + large + ' 0 ' + xi0 + ',' + yi0 + ' Z';
      svg.appendChild(el('path', { d: d, fill: PALETTE[i % PALETTE.length], opacity: .92 },
        ''));
      var t = el('title', {}, labels[i] + ': ' + fmt(v) + ' (' + Math.round(frac * 100) + '٪)');
      svg.appendChild(t);
      a0 = a1; sum += v;
    });
    svg.appendChild(el('text', { x: cx, y: cy - 2, 'text-anchor': 'middle', 'font-size': 17, 'font-weight': 'bold', fill: 'currentColor' }, fmt(sum)));
    svg.appendChild(el('text', { x: cx, y: cy + 16, 'text-anchor': 'middle', 'font-size': 10, fill: '#889' }, 'مجموع'));
    var lg = document.createElement('div'); lg.className = 'legend';
    labels.forEach(function (l, i) {
      var s = document.createElement('span');
      s.innerHTML = '<i style="background:' + PALETTE[i % PALETTE.length] + '"></i>' + l + ' (' + fmt(vals[i]) + ')';
      lg.appendChild(s);
    });
    box.appendChild(svg); box.appendChild(lg);
  }

  // ---------------- میله‌ای ----------------
  function bars(ch, box, second) {
    var labels = ch.labels, vals = ch.values, vals2 = second ? ch.values2 : null;
    var W = 620, H = 40 + labels.length * 30 + 14;
    var max = 0;
    vals.concat(vals2 || []).forEach(function (v) { if (v > max) max = v; });
    max = max || 1;
    var svg = svgRoot(W, H);
    labels.forEach(function (lb, i) {
      var y = 30 + i * 30;
      var t = el('text', { x: W - 6, y: y + 13, 'text-anchor': 'end', 'font-size': 11, fill: 'currentColor' },
        String(lb).length > 34 ? String(lb).slice(0, 33) + '…' : String(lb));
      svg.appendChild(t);
      var w = Math.max(2, vals[i] / max * (W - 230));
      svg.appendChild(el('rect', { x: 130, y: y + 2, width: w, height: 11, rx: 3, fill: PALETTE[0] }));
      svg.appendChild(el('text', { x: 130 + w + 4, y: y + 12, 'font-size': 10, fill: 'currentColor' }, fmt(vals[i])));
      if (vals2) {
        var w2 = Math.max(0, vals2[i] / max * (W - 230));
        svg.appendChild(el('rect', { x: 130, y: y + 14, width: w2, height: 8, rx: 3, fill: '#94a3b8', opacity: .8 }));
        if (vals2[i] > 0)
          svg.appendChild(el('text', { x: 130 + w2 + 4, y: y + 21, 'font-size': 9.5, fill: '#889' }, fmt(vals2[i])));
      }
    });
    box.appendChild(svg);
    if (second) {
      var lg = document.createElement('div'); lg.className = 'legend';
      lg.innerHTML = '<span><i style="background:' + PALETTE[0] + '"></i>' + (ch.label_ok || 'تاییدشده') + '</span>' +
        '<span><i style="background:#94a3b8"></i>' + (ch.label_wait || 'در انتظار') + '</span>';
      box.appendChild(lg);
    }
  }

  // ---------------- خطی ----------------
  function line(ch, box) {
    var series = ch.series, labels = ch.labels;
    var W = 640, H = 240, padL = 46, padB = 46, padT = 14, padR = 10;
    var max = 0;
    series.forEach(function (s) { s.values.forEach(function (v) { if (v > max) max = v; }); });
    max = max || 1;
    var iw = W - padL - padR, ih = H - padT - padB;
    var svg = svgRoot(W, H);
    for (var g = 0; g <= 4; g++) {
      var gy = padT + ih - ih * g / 4;
      svg.appendChild(el('line', { x1: padL, y1: gy, x2: W - padR, y2: gy, stroke: '#8882', 'stroke-width': .6 }));
      svg.appendChild(el('text', { x: padL - 5, y: gy + 3, 'text-anchor': 'end', 'font-size': 9, fill: '#889' }, fmt(Math.round(max * g / 4))));
    }
    var n = labels.length;
    var step = n > 1 ? iw / (n - 1) : 0;
    series.forEach(function (s, si) {
      var pts = s.values.map(function (v, i) {
        var x = padL + (n > 1 ? i * step : iw / 2);
        var y = padT + ih - (v / max) * ih;
        return [x, y];
      });
      var path = pts.map(function (p, i) { return (i ? 'L' : 'M') + p[0].toFixed(1) + ',' + p[1].toFixed(1); }).join(' ');
      svg.appendChild(el('path', { d: path, fill: 'none', stroke: s.color || PALETTE[si % PALETTE.length], 'stroke-width': 2.2, 'stroke-linejoin': 'round' }));
      if (n <= 40) pts.forEach(function (p) {
        svg.appendChild(el('circle', { cx: p[0], cy: p[1], r: 2.4, fill: s.color || PALETTE[si % PALETTE.length] }));
      });
    });
    var tick = Math.ceil(n / 12);
    labels.forEach(function (lb, i) {
      if (i % tick) return;
      var x = padL + (n > 1 ? i * step : iw / 2);
      svg.appendChild(el('text', { x: x, y: H - 30, 'text-anchor': 'middle', 'font-size': 9, fill: '#889', transform: 'rotate(-32 ' + x + ' ' + (H - 30) + ')' }, lb));
    });
    var lg = document.createElement('div'); lg.className = 'legend';
    series.forEach(function (s, si) {
      lg.innerHTML += '<span><i style="background:' + (s.color || PALETTE[si % PALETTE.length]) + '"></i>' + s.name + '</span>';
    });
    box.appendChild(svg); box.appendChild(lg);
  }

  // ---------------- جدول ----------------
  function table(ch, box) {
    var t = document.createElement('table');
    t.className = 'data';
    var thead = '<thead><tr>' + ch.headers.map(function (h) { return '<th>' + h + '</th>'; }).join('') + '</tr></thead>';
    var rows = ch.rows.map(function (r) {
      return '<tr>' + r.map(function (c) { return '<td>' + (c == null ? '—' : c) + '</td>'; }).join('') + '</tr>';
    }).join('');
    t.innerHTML = thead + '<tbody>' + (rows || '<tr><td colspan="' + ch.headers.length + '" class="muted">داده‌ای نیست</td></tr>') + '</tbody>';
    box.appendChild(t);
  }

  global.renderChart = function (ch, box) {
    box.innerHTML = '';
    if (ch.kind === 'donut') donut(ch, box);
    else if (ch.kind === 'bars') bars(ch, box, false);
    else if (ch.kind === 'bars2') bars(ch, box, true);
    else if (ch.kind === 'line') line(ch, box);
    else if (ch.kind === 'table') table(ch, box);
  };
})(window);
