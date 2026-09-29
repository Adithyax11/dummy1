const API = "/api";
const MAX_LOG = 20;
const logRows = [];
const $ = (id) => document.getElementById(id);

// One wrapper for every request: times it, reads X-Request-ID, adds it to the log
async function call(method, path, body, { quiet = false } = {}) {
  const started = performance.now();
  let status = 0, data = null, requestId = "";
  try {
    const res = await fetch(API + path, {
      method,
      headers: body ? { "Content-Type": "application/json" } : {},
      body: body ? JSON.stringify(body) : undefined,
    });
    status = res.status;
    requestId = res.headers.get("x-request-id") || "";
    const text = await res.text();
    try { data = JSON.parse(text); } catch { data = text; }
  } catch (err) {
    data = { error: String(err) };
  }
  const ms = Math.round(performance.now() - started);
  if (!quiet) addLog({ time: new Date(), method, path, status, ms, requestId });
  return { status, data, ms };
}

function show(el, r) {
  el.textContent = `${r.status} (${r.ms} ms)\n` + JSON.stringify(r.data, null, 2);
}

function statusClass(s) {
  if (s >= 200 && s < 400) return "s-ok";
  if (s >= 400 && s < 500) return "s-warn";
  return "s-err";
}

function addLog(entry) {
  logRows.unshift(entry);
  if (logRows.length > MAX_LOG) logRows.pop();
  renderLog();
}

function renderLog() {
  const tbody = $("log");
  tbody.replaceChildren();
  for (const e of logRows) {
    const tr = document.createElement("tr");
    const cells = [
      e.time.toLocaleTimeString(), e.method, e.path,
      e.status || "ERR", e.ms, e.requestId.slice(0, 12),
    ];
    cells.forEach((v, i) => {
      const td = document.createElement("td");
      td.textContent = v;
      if (i === 3) td.className = statusClass(e.status);
      tr.appendChild(td);
    });
    tbody.appendChild(tr);
  }
}

async function loadProducts({ quiet = false } = {}) {
  const r = await call("GET", "/products", null, { quiet });
  const select = $("sku");
  const prev = select.value;
  select.replaceChildren();
  if (r.status !== 200 || !Array.isArray(r.data)) {
    select.add(new Option("could not load products", ""));
    return;
  }
  for (const p of r.data) {
    const price = (p.price_cents / 100).toFixed(2);
    select.add(new Option(`${p.name} (${p.sku}) $${price}, stock ${p.stock}`, p.sku));
  }
  if (prev) select.value = prev;
}

$("order-btn").onclick = async () => {
  const r = await call("POST", "/orders", {
    sku: $("sku").value,
    quantity: parseInt($("qty").value, 10),
  });
  show($("order-out"), r);
  loadProducts({ quiet: true });   // refresh stock counts without logging
};

$("lookup-btn").onclick = async () => {
  const id = $("order-id").value;
  if (!id) return;
  show($("lookup-out"), await call("GET", `/orders/${id}`));
};

document.querySelectorAll(".chaos").forEach((btn) => {
  btn.onclick = async () => show($("chaos-out"), await call("GET", btn.dataset.path));
});

$("chain-btn").onclick = async () => {
  show($("chaos-out"), await call("GET", `/chain?depth=${$("depth").value}`));
};

$("clear-btn").onclick = () => { logRows.length = 0; renderLog(); };

loadProducts();