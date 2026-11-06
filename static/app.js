/* منطق صفحات — داشبورد، گزارش‌ساز، گزارش آماده، مرور داده، منبع داده */
(function () {
  'use strict';

  // ---------------- تم ----------------
  var themeBtn = document.getElementById('themeToggle');
  function applyTheme(t) {
    document.documentElement.setAttribute('data-theme', t);
    try { localStorage.setItem('rz_theme', t); } catch (e) {}
    if (themeBtn) themeBtn.textContent = t === 'dark' ? '☀️' : '🌙';
  }
  try { applyTheme(localStorage.getItem('rz_theme') || 'light'); } catch (e) {}
  if (themeBtn) themeBtn.onclick = function () {
    var cur = document.documentElement.getAttribute('data-theme') === 'dark' ? 'light' : 'dark';
    applyTheme(cur);
  };

  function $(s, box) { return (box || document).querySelector(s); }
  function $$(s, box) { return Array.prototype.slice.call((box || document).querySelectorAll(s)); }
  function fa(v) { return String(v == null ? '' : v); }

  function renderResult(box, data, opts) {
    opts = opts || {};
    box.innerHTML = '';
    if (data.error) {
      box.innerHTML = '<div class="msg-err">' + fa(data.error) + '</div>';
      return;
    }
    var meta = document.createElement('div');
    meta.className = 'tbl-foot';
    meta.innerHTML = '<span>' + fa(data.count) + ' ردیف' +
      (data.elapsed_ms ? ' — ' + fa(data.elapsed_ms) + ' میلی‌ثانیه' : '') + '</span>';
    box.appendChild(meta);
    var wrap = document.createElement('div');
    wrap.className = 'tbl-wrap';
    var t = document.createElement('table');
    t.className = 'data';
    var head = '<tr>' + data.columns.map(function (c) { return '<th>' + fa(c.label) + '</th>'; }).join('') + '</tr>';
    var rows = data.rows.map(function (r) {
      return '<tr>' + r.map(function (v) {
        var s = v == null || v === '' ? '—' : fa(v);
        return '<td>' + s + '</td>';
      }).join('') + '</tr>';
    }).join('');
    t.innerHTML = '<thead>' + head + '</thead><tbody>' +
      (rows || '<tr><td colspan="' + data.columns.length + '" class="muted">ردیفی یافت نشد</td></tr>') + '</tbody>';
    wrap.appendChild(t);
    box.appendChild(wrap);
    if (opts.chartable && data.grouped && data.rows.length && data.rows[0].length === 2) {
      var ch = { kind: 'bars', title: '', labels: data.rows.slice(0, 15).map(function (r) { return r[0]; }), values: data.rows.slice(0, 15).map(function (r) { return Number(String(r[1]).replace(/[^\d-]/g, '')) || 0; }) };
      var cb = document.createElement('div');
      cb.className = 'chart-card wide';
      cb.style.marginTop = '12px';
      renderChart(ch, cb);
      box.appendChild(cb);
    }
  }

  // ================= داشبورد =================
  var dashBox = $('#biRoot');
  if (dashBox) {
    var provSel = $('#fProvince'), df = $('#fDateFrom'), dt = $('#fDateTo');
    function loadBI() {
      var q = new URLSearchParams();
      if (provSel && provSel.value) q.set('province', provSel.value);
      if (df && df.value) q.set('date_from', df.value);
      if (dt && dt.value) q.set('date_to', dt.value);
      dashBox.innerHTML = '<div class="card"><span class="spin"></span> در حال محاسبه آمار…</div>';
      fetch('/api/bi?' + q.toString()).then(function (r) { return r.json(); }).then(function (data) {
        if (data.error) { dashBox.innerHTML = '<div class="msg-err">خطا در خواندن آمار</div>'; return; }
        dashBox.innerHTML = '';
        var kg = document.createElement('div'); kg.className = 'kpis';
        (data.kpis || []).forEach(function (k) {
          var d = document.createElement('div');
          d.className = 'kpi ' + (k.tone || '');
          d.innerHTML = '<div class="v">' + k.value + '</div><div class="l">' + k.icon + ' ' + fa(k.label) + '</div>' + (k.sub ? '<div class="s">' + fa(k.sub) + '</div>' : '');
          kg.appendChild(d);
        });
        dashBox.appendChild(kg);
        var grid = document.createElement('div'); grid.className = 'charts';
        (data.charts || []).forEach(function (ch) {
          var card = document.createElement('div');
          card.className = 'chart-card' + (ch.kind === 'line' ? ' wide' : '');
          var head = document.createElement('div'); head.className = 'chart-head spread flex';
          head.innerHTML = '<b>' + fa(ch.title) + '</b>';
          var dl = document.createElement('a');
          dl.className = 'csv-link'; dl.textContent = 'دریافت CSV ⬇';
          dl.href = '/api/bi.csv/' + ch.id + '?' + q.toString();
          dl.download = ch.id + '.csv';
          head.appendChild(dl);
          card.appendChild(head);
          if (ch.insight) {
            var ins = document.createElement('div');
            ins.className = 'insight';
            ins.textContent = '💡 ' + fa(ch.insight);
            card.appendChild(ins);
          }
          var box = document.createElement('div');
          card.appendChild(box);
          grid.appendChild(card);
          renderChart(ch, box);
        });
        dashBox.appendChild(grid);
        if (data.budget_table) {
          var card = document.createElement('div'); card.className = 'card';
          card.innerHTML = '<h3>🎯 ' + fa(data.budget_table.title) + '</h3>';
          var box = document.createElement('div');
          card.appendChild(box);
          dashBox.appendChild(card);
          renderChart(data.budget_table, box);
        }
        renderPins(dashBox);
      }).catch(function () {
        dashBox.innerHTML = '<div class="msg-err">ارتباط با سرور برقرار نشد</div>';
      });
    }
    // --- ذخیره و بارگذاری داشبورد ---
    var saveDash = $('#dashSave');
    if (saveDash) saveDash.onclick = function () {
      var name = prompt('نام داشبورد:', 'داشبورد من');
      if (!name) return;
      fetch('/api/dashboards', { method: 'POST', headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ name: name, filters: dashFilters() }) })
        .then(function (r) { return r.json(); })
        .then(function (d) { if (d.ok) location.reload(); else alert(d.error || 'خطا'); });
    };
    function dashFilters() {
      return { province: provSel ? provSel.value : '', date_from: df ? df.value : '', date_to: dt ? dt.value : '' };
    }
    $$('.apply-dash').forEach(function (b) {
      b.onclick = function () {
        var d = (window.DASHBOARDS || [])[Number(b.dataset.i)] || {};
        var f = d.filters || {};
        if (provSel) provSel.value = f.province || '';
        if (df) df.value = f.date_from || '';
        if (dt) dt.value = f.date_to || '';
        loadBI();
      };
    });
    $$('.del-dash').forEach(function (b) {
      b.onclick = function () {
        if (!confirm('حذف داشبورد؟')) return;
        fetch('/api/dashboards/' + encodeURIComponent(b.dataset.name), { method: 'DELETE' })
          .then(function () { location.reload(); });
      };
    });
    // --- نمودارهای سنجاق‌شده (داشبورد شخصی) ---
    function renderPins(root) {
      var pins = window.DASH_PINS || [];
      if (!pins.length) return;
      var head = document.createElement('h2');
      head.className = 'cat-title';
      head.textContent = '📌 داشبورد شخصی من (نمودارهای سنجاق‌شده از گزارش‌ساز)';
      root.appendChild(head);
      var grid = document.createElement('div'); grid.className = 'charts';
      pins.forEach(function (p, i) {
        var card = document.createElement('div');
        card.className = 'chart-card wide';
        var h = document.createElement('div'); h.className = 'chart-head spread flex';
        h.innerHTML = '<b>' + fa(p.title) + '</b>';
        var del = document.createElement('button');
        del.className = 'btn gray'; del.textContent = 'حذف';
        del.onclick = function () {
          fetch('/api/dashboards', { method: 'POST', headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ remove_pin: i }) })
            .then(function (r) { return r.json(); })
            .then(function (d) { if (d.ok) location.reload(); });
        };
        h.appendChild(del);
        card.appendChild(h);
        var box = document.createElement('div');
        box.innerHTML = '<div class="small muted">در حال محاسبه…</div>';
        card.appendChild(box);
        grid.appendChild(card);
        fetch('/api/report', { method: 'POST', headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify(p.spec) })
          .then(function (r) { return r.json(); })
          .then(function (data) {
            box.innerHTML = '';
            if (data.error) { box.innerHTML = '<div class="msg-err">' + fa(data.error) + '</div>'; return; }
            var ch = null;
            if (data.grouped && data.rows.length && data.rows[0].length === 2) {
              ch = { kind: 'bars', title: '', labels: data.rows.slice(0, 15).map(function (r) { return r[0]; }),
                     values: data.rows.slice(0, 15).map(function (r) { return Number(String(r[1]).replace(/[^\d-]/g, '')) || 0; }) };
            } else if (data.grouped && data.rows.length && data.rows[0].length === 3) {
              ch = { kind: 'bars2', title: '', labels: data.rows.slice(0, 12).map(function (r) { return r[0]; }),
                     series: [{ name: fa(data.columns[1].label), values: data.rows.slice(0, 12).map(function (r) { return Number(String(r[1]).replace(/[^\d-]/g, '')) || 0; }) },
                              { name: fa(data.columns[2].label), values: data.rows.slice(0, 12).map(function (r) { return Number(String(r[2]).replace(/[^\d-]/g, '')) || 0; }) }] };
            }
            if (ch) { renderChart(ch, box); }
            else { renderResult(box, data); }
          }).catch(function () { box.innerHTML = '<div class="msg-err">خطا</div>'; });
      });
      root.appendChild(grid);
    }
    var runBtn = $('#biRun');
    if (runBtn) runBtn.onclick = loadBI;
    loadBI();
  }

  // ================= گزارش آماده =================
  var presetRoot = $('#presetRoot');
  if (presetRoot && window.PRESET) {
    var pr = window.PRESET;
    var fbox = $('#presetFilters');
    (pr.filters || []).forEach(function (f) {
      var lab = document.createElement('label');
      lab.className = 'f';
      var inp;
      if (f.kind === 'select') {
        inp = document.createElement('select');
        inp.dataset.fkey = f.key;
        inp.dataset.dict = f.dict || '';
        var o = document.createElement('option');
        o.value = ''; o.textContent = 'همه';
        inp.appendChild(o);
        (f.options || []).forEach(function (op) {
          var x = document.createElement('option'); x.value = op[0]; x.textContent = op[1];
          inp.appendChild(x);
        });
        if (f.dict) loadDictInto(inp, f.dict);
      } else if (f.kind === 'date') {
        inp = document.createElement('input');
        inp.type = 'text'; inp.placeholder = '۱۴۰۴/۰۱/۰۱'; inp.dataset.fkey = f.key;
      } else {
        inp = document.createElement('input');
        inp.type = 'text'; inp.placeholder = f.label; inp.dataset.fkey = f.key;
      }
      lab.appendChild(document.createTextNode(f.label));
      lab.appendChild(inp);
      fbox.appendChild(lab);
    });
    function loadDictInto(sel, dict) {
      fetch('/api/dicts/' + dict).then(function (r) { return r.json(); }).then(function (items) {
        items.forEach(function (it) {
          var x = document.createElement('option'); x.value = it.v; x.textContent = it.t;
          sel.appendChild(x);
        });
      });
    }
    function collectParams(limit) {
      var p = { limit: limit || 200 };
      $$('#presetFilters [data-fkey]').forEach(function (el) {
        if (el.value) p[el.dataset.fkey] = el.value;
      });
      return p;
    }
    function runPreset(limit, into) {
      into.innerHTML = '<div class="card"><span class="spin"></span> در حال اجرای گزارش…</div>';
      fetch('/api/preset/' + window.PRESET_KEY, {
        method: 'POST', headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(collectParams(limit))
      }).then(function (r) { return r.json(); }).then(function (data) {
        renderResult(into, data);
      }).catch(function () { into.innerHTML = '<div class="msg-err">خطا در اجرا</div>'; });
    }
    var runBtn = $('#presetRun');
    if (runBtn) runBtn.onclick = function () { runPreset(parseInt($('#presetLimit').value, 10) || 200, presetRoot); };
    var expCsv = $('#presetCsv'), expXls = $('#presetXlsx'), printBtn = $('#presetPrint');
    function exportPreset(fmt) {
      var p = collectParams(100000); p.format = fmt;
      // مهم: خروجی فایل باید از مسیر /export بگیرد؛ مسیر بدون /export همیشه JSON برمی‌گرداند
      fetch('/api/preset/' + window.PRESET_KEY + '/export', {
        method: 'POST', headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(p)
      }).then(function (r) {
        if (!r.ok) return r.text().then(function (t) { throw new Error(t); });
        var ct = r.headers.get('Content-Type') || '';
        if (ct.indexOf('json') !== -1) throw new Error('پاسخ سرور JSON بود به‌جای فایل');
        var ext = fmt === 'xlsx' ? 'xlsx' : 'csv';
        return r.blob().then(function (b) { dl(b, 'report.' + ext); });
      }).catch(function (e) { alert('خطا در خروجی: ' + e.message); });
    }
    function dl(blob, name) {
      var a = document.createElement('a');
      a.href = URL.createObjectURL(blob); a.download = name;
      document.body.appendChild(a); a.click();
      setTimeout(function () { URL.revokeObjectURL(a.href); a.remove(); }, 800);
    }
    if (expCsv) expCsv.onclick = function () { exportPreset('csv'); };
    if (expXls) expXls.onclick = function () { exportPreset('xlsx'); };
    if (printBtn) printBtn.onclick = function () { window.print(); };
    runPreset(200, presetRoot);
  }

  // ================= گزارش‌ساز (سازنده آزاد) =================
  var bRoot = $('#builderRoot');
  if (bRoot) {
    var TABLES = window.META_TABLES || [];
    var selTable = $('#bTable'), colsBox = $('#bCols'), filtersBox = $('#bFilters');
    var gbSel = $('#bGroupBy'), gbMode = $('#bGroupMode'), aggSel = $('#bAggCol'), aggFn = $('#bAggFn');
    var aggs = [];

    TABLES.forEach(function (t) {
      var o = document.createElement('option');
      o.value = t.name; o.textContent = t.label + ' (' + faNumRows(t.rows) + ')';
      selTable.appendChild(o);
    });
    function faNumRows(n) {
      n = n || 0;
      return String(n).replace(/\d/g, function (d) { return '۰۱۲۳۴۵۶۷۸۹'[d]; }) + ' ردیف';
    }
    function curTable() {
      return TABLES.filter(function (t) { return t.name === selTable.value; })[0] || null;
    }
    function renderCols() {
      colsBox.innerHTML = '';
      var t = curTable(); if (!t) return;
      var all = document.createElement('label');
      all.innerHTML = '<input type=checkbox id=bAllCols> همه ستون‌ها';
      colsBox.appendChild(all);
      t.cols.forEach(function (c) {
        var l = document.createElement('label');
        l.innerHTML = '<input type=checkbox value="' + c.name + '"' + (c.fk ? ' data-fk=1' : '') + '> ' + fa(c.label);
        colsBox.appendChild(l);
      });
      $('#bAllCols').onchange = function () {
        $$('input[type=checkbox]', colsBox).forEach(function (cb) {
          if (cb.id !== 'bAllCols') cb.checked = $('#bAllCols').checked;
        });
      };
      renderFilterColOptions();
      renderAggOptions();
    }
    function renderFilterColOptions() {
      var t = curTable(); if (!t) return;
      var sel = $('#bFilterCol');
      sel.innerHTML = '';
      t.cols.forEach(function (c) {
        var o = document.createElement('option');
        o.value = c.name; o.textContent = c.label + ' — ' + c.name;
        sel.appendChild(o);
      });
    }
    function renderAggOptions() {
      var t = curTable(); if (!t) return;
      aggSel.innerHTML = '<option value="*">— (شمارش)</option>';
      t.cols.forEach(function (c) {
        var o = document.createElement('option');
        o.value = c.name; o.textContent = c.label;
        aggSel.appendChild(o);
      });
    }
    selTable.onchange = renderCols;
    if (TABLES.length) { selTable.value = 'Events'; renderCols(); }

    $('#bAddFilter').onclick = function () {
      var t = curTable(); if (!t) return;
      var col = $('#bFilterCol').value;
      var row = document.createElement('div');
      row.className = 'frow';
      var colLabel = col;
      t.cols.forEach(function (c) { if (c.name === col) colLabel = c.label; });
      row.innerHTML = '<span class="tag">' + fa(colLabel) + '</span>' +
        '<select class="op">' +
        '<option value=eq>= برابر</option><option value=ne>≠ مخالف</option>' +
        '<option value=contains>شامل</option><option value=ncontains>بدون</option>' +
        '<option value=gt>&gt; بزرگ‌تر</option><option value=ge>≥</option>' +
        '<option value=lt>&lt; کوچک‌تر</option><option value=le>≤</option>' +
        '<option value=empty>خالی</option><option value=notempty>پر</option></select>' +
        '<input type=text placeholder="مقدار — تاریخ: ۱۴۰۴/۰۷/۱۲">' +
        '<button class="btn gray">حذف</button>';
      row.querySelector('button').onclick = function () { row.remove(); };
      row.dataset.col = col;
      filtersBox.appendChild(row);
    };

    $('#bAddAgg').onclick = function () {
      var fn = aggFn.value, col = aggSel.value;
      var t = curTable();
      var lbl = { count: 'تعداد', sum: 'جمع', avg: 'میانگین', min: 'کمینه', max: 'بیشینه' }[fn];
      var colLabel = col === '*' ? 'همه' : col;
      if (t) t.cols.forEach(function (c) { if (c.name === col) colLabel = c.label; });
      aggs.push({ fn: fn, col: col });
      var tag = document.createElement('span');
      tag.className = 'tag';
      tag.textContent = lbl + ' ' + colLabel + ' ✕';
      tag.style.cursor = 'pointer';
      tag.onclick = function () { aggs = aggs.filter(function (a) { return !(a.fn === fn && a.col === col); }); tag.remove(); };
      $('#bAggList').appendChild(tag);
    };

    function buildSpec(limit) {
      var cols = $$('input[type=checkbox]:checked', colsBox)
        .filter(function (cb) { return cb.id !== 'bAllCols'; })
        .map(function (cb) { return cb.value; });
      if ($('#bAllCols') && $('#bAllCols').checked) cols = [];
      var filters = $$('.frow', filtersBox).map(function (row) {
        return {
          col: row.dataset.col,
          op: row.querySelector('.op').value,
          value: row.querySelector('input').value
        };
      }).filter(function (f) { return f.op === 'empty' || f.op === 'notempty' || f.value !== ''; });
      var spec = {
        table: selTable.value,
        columns: cols,
        filters: filters,
        search: $('#bSearch').value,
        date_from: $('#bDateFrom').value,
        date_to: $('#bDateTo').value,
        limit: limit || parseInt($('#bLimit').value, 10) || 200
      };
      if (gbSel.value) {
        spec.group_by = [{ col: gbSel.value, mode: gbMode.value }];
        spec.aggs = aggs.length ? aggs : [{ fn: 'count', col: '*' }];
        var ord = spec.group_by[0].col;
        if (aggs.length) ord = String(1 + 1);
        spec.order = [{ col: aggs.length ? '2' : ord, dir: 'desc' }];
      } else if ($('#bSortCol').value) {
        spec.order = [{ col: $('#bSortCol').value, dir: $('#bSortDir').value }];
      }
      return spec;
    }

    $('#bRun').onclick = function () {
      bRoot.innerHTML = '<div class="card"><span class="spin"></span> در حال اجرا…</div>';
      fetch('/api/report', { method: 'POST', headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(buildSpec()) })
        .then(function (r) { return r.json(); })
        .then(function (data) { renderResult(bRoot, data, { chartable: true }); })
        .catch(function () { bRoot.innerHTML = '<div class="msg-err">خطا</div>'; });
    };
    $('#bCsv').onclick = function () { exportSpec('csv'); };
    $('#bXlsx').onclick = function () { exportSpec('xlsx'); };
    function exportSpec(fmt) {
      var spec = buildSpec(100000); spec.format = fmt;
      fetch('/api/report/export', { method: 'POST', headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(spec) })
        .then(function (r) {
          if (!r.ok) return r.text().then(function (t) { throw new Error(t); });
          return r.blob().then(function (b) { dl(b, fmt === 'xlsx' ? 'report.xlsx' : 'report.csv'); });
        }).catch(function (e) { alert('خطا: ' + e.message); });
    }
    $('#bSave').onclick = function () {
      var name = prompt('نام گزارش را وارد کنید:');
      if (!name) return;
      fetch('/api/saved', { method: 'POST', headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ name: name, spec: buildSpec(200) }) })
        .then(function (r) { return r.json(); })
        .then(function (d) {
          if (d.ok) location.reload();
          else alert(d.error || 'خطا');
        });
    };
    var bPin = $('#bPin');
    if (bPin) bPin.onclick = function () {
      var spec = buildSpec(15);
      if (!spec.group_by || !spec.group_by.length) {
        if (!confirm('برای نمایش در داشبورد، گروه‌بندی توصیه می‌شود. بدون گروه‌بندی به‌صورت جدول سنجاق شود؟')) return;
      }
      fetch('/api/dashboards', { method: 'POST', headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ add_pin: { title: (curTable() ? curTable().label : spec.table) + ' — ' + new Date().toLocaleDateString('fa-IR'), spec: spec } }) })
        .then(function (r) { return r.json(); })
        .then(function (d) {
          if (d.ok) { alert('به داشبورد «' + d.dashboard + '» سنجاق شد — از منوی داشبورد ببینید.'); location.href = '/'; }
          else alert(d.error || 'خطا');
        });
    };
    function dl(blob, name) {
      var a = document.createElement('a');
      a.href = URL.createObjectURL(blob); a.download = name;
      document.body.appendChild(a); a.click();
      setTimeout(function () { URL.revokeObjectURL(a.href); a.remove(); }, 800);
    }
    $$('.load-saved').forEach(function (b) {
      b.onclick = function () {
        var spec = window.SAVED_SPECS[b.dataset.name];
        if (!spec) return;
        selTable.value = spec.table; renderCols();
        setTimeout(function () {
          (spec.columns || []).forEach(function (c) {
            $$('input[type=checkbox]', colsBox).forEach(function (cb) {
              if (cb.value === c) cb.checked = true;
            });
          });
          $('#bSearch').value = spec.search || '';
          $('#bDateFrom').value = spec.date_from || '';
          $('#bDateTo').value = spec.date_to || '';
          $('#bLimit').value = spec.limit || 200;
          if (spec.group_by && spec.group_by[0]) {
            gbSel.value = spec.group_by[0].col; gbMode.value = spec.group_by[0].mode || 'value';
          }
        }, 30);
        window.scrollTo({ top: 0, behavior: 'smooth' });
      };
    });
    $$('.del-saved').forEach(function (b) {
      b.onclick = function () {
        if (!confirm('حذف شود؟')) return;
        fetch('/api/saved/' + encodeURIComponent(b.dataset.name), { method: 'DELETE' })
          .then(function () { location.reload(); });
      };
    });
  }

  // ================= مرور جدول =================
  var sortHeaders = $$('th[data-sort]');
  sortHeaders.forEach(function (th) {
    th.style.cursor = 'pointer';
    th.onclick = function () {
      var cur = new URLSearchParams(location.search);
      var same = cur.get('sort') === th.dataset.sort;
      cur.set('sort', th.dataset.sort);
      cur.set('dir', same && cur.get('dir') !== 'desc' ? 'desc' : 'asc');
      cur.delete('p');
      location.search = cur.toString();
    };
  });

  // ================= منبع داده =================
  // توجه: شرط باید بر اساس وجود خود دکمه‌ها باشد نه یک نگهدارنده اختیاری؛
  // در غیر این صورت هیچ هندلری به دکمه‌ها وصل نمی‌شود و «هیچ دکمه‌ای کار نمی‌کند».
  var optBtn0 = $('#optimizeBtn');
  var impBox0 = $('#impBox');
  var setupRoot = $('.use-db') || $('.import-sql') || optBtn0 || impBox0 ||
      document.getElementById('setupRoot');
  if (setupRoot) {
    function post(url, body) {
      return fetch(url, { method: 'POST', headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(body || {}) })
        .then(function (r) { return r.json(); })
        .catch(function () { return { error: 'ارتباط با سرور برقرار نشد — برنامه در حال اجرا است؟' }; });
    }
    $$('.use-db').forEach(function (b) {
      b.onclick = function () {
        b.disabled = true; b.textContent = 'در حال تنظیم…';
        post('/api/use_db', { path: b.dataset.path }).then(function (d) {
          if (d.ok) location.href = '/';
          else { alert(d.error || 'خطا'); b.disabled = false; b.textContent = 'استفاده از این دیتابیس'; }
        });
      };
    });
    $$('.import-sql').forEach(function (b) {
      b.onclick = function () {
        if (!confirm('استخراج از بکاپ شروع شود؟ (بسته به حجم فایل ممکن است طول بکشد)')) return;
        b.disabled = true; b.textContent = 'در صف اجرا…';
        post('/api/import_sql', { path: b.dataset.path }).then(function (d) {
          if (d.ok) pollStatus();
          else { alert(d.error || 'خطا'); b.disabled = false; b.textContent = 'استخراج از این بکاپ'; }
        });
      };
    });
    var optBtn = $('#optimizeBtn');
    if (optBtn) optBtn.onclick = function () {
      optBtn.disabled = true; optBtn.textContent = 'در حال ساخت…';
      post('/api/optimize').then(function (d) {
        if (d.ok) pollStatus(); else { alert(d.error || 'خطا'); optBtn.disabled = false; optBtn.textContent = 'ساخت ایندکس‌ها برای سرعت'; }
      });
    };
    function pollStatus() {
      fetch('/api/status').then(function (r) { return r.json(); }).catch(function () { return {}; }).then(function (st) {
        var bar = $('#impProgress'), box = $('#impBox');
        if (st.importing) {
          box.classList.remove('hidden');
          var pct = Math.round(st.percent || 0);
          bar.querySelector('div').style.width = pct + '%';
          bar.querySelector('span').textContent = pct + '٪ — ' + fa(st.phase || '') +
            (st.current_table ? ' — ' + fa(st.current_table) : '') +
            ' — ' + fa((st.rows || 0).toLocaleString('en-US')) + ' ردیف';
          setTimeout(pollStatus, 1500);
        } else if (st.optimizing) {
          box.classList.remove('hidden');
          var p2 = Math.round(st.percent || 0);
          bar.querySelector('div').style.width = p2 + '%';
          bar.querySelector('span').textContent = 'ایندکس‌ها: ' + p2 + '٪ (' + fa(st.done || 0) + ' از ' + fa(st.total || 0) + ')';
          setTimeout(pollStatus, 1500);
        } else {
          if (box && !box.classList.contains('hidden') && st.state === 'done') {
            location.reload();
            return;
          }
          if (optBtn && optBtn.disabled) { optBtn.disabled = false; optBtn.textContent = 'ساخت ایندکس‌ها برای سرعت'; }
          $$('.import-sql').forEach(function (b) { b.disabled = false; b.textContent = 'استخراج از این بکاپ'; });
        }
      });
    }
    pollStatus();
  }
})();
