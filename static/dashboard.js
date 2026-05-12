const socket = io();
let state = {};

socket.on("connect",      () => { socket.emit("get_state"); });
socket.on("disconnected", () => { setBadge(false); });
socket.on("state",   (s)    => { state = s; renderAll(s); });
socket.on("log",     (data) => { appendLog(data.message); });

function renderAll(s) {
  setBadge(s.connected);
  document.getElementById("unionTag").textContent = s.union_id ? "#" + s.union_id : "—";

  const autoBtn = document.getElementById("toggleAuto");
  autoBtn.textContent = "自動：" + (s.auto ? "開" : "關");
  autoBtn.classList.toggle("active", s.auto);

  const dbgBtn = document.getElementById("toggleDebug");
  dbgBtn.textContent = "偵錯：" + (s.debug ? "開" : "關");
  dbgBtn.classList.toggle("active", s.debug);

  renderApplied(s.applied      || []);
  renderQueue(s.queue          || []);
  renderWhiteList(s.white_list || []);
  renderBlackList(s.black_list || []);
}

function setBadge(connected) {
  const el = document.getElementById("statusBadge");
  el.textContent = connected ? "● 已連線" : "● 已斷線";
  el.className   = "badge " + (connected ? "badge-green" : "badge-red");
}

function renderApplied(list) {
  document.getElementById("appliedCount").textContent = list.length;
  const el = document.getElementById("appliedList");
  if (!list.length) { el.innerHTML = '<div class="empty-state">無人申請</div>'; return; }
  el.innerHTML = list.map(uid => `
    <div class="user-row">
      <span class="uid"># ${uid}</span>
      <div class="actions">
        <button class="btn btn-sm btn-success" onclick="approve(${uid})">&#10003; 批准</button>
        <button class="btn btn-sm btn-danger"  onclick="reject(${uid})">&#10007; 拒絕</button>
        <button class="btn btn-sm btn-ghost"   onclick="quickWhite(${uid})">&rarr; 白名單</button>
        <button class="btn btn-sm btn-ghost"   onclick="quickBlack(${uid})">&rarr; 黑名單</button>
      </div>
    </div>`).join("");
}

function renderQueue(list) {
  document.getElementById("queueCount").textContent = list.length;
  const el = document.getElementById("queueList");
  if (!list.length) { el.innerHTML = '<div class="empty-state">無人排隊</div>'; return; }
  el.innerHTML = list.map(uid => `<span class="uid-chip">${uid}</span>`).join("");
}

function renderWhiteList(list) {
  document.getElementById("whiteCount").textContent = list.length;
  const el = document.getElementById("whiteList");
  if (!list.length) { el.innerHTML = '<div class="empty-state">空白</div>'; return; }
  el.innerHTML = list.map(uid =>
    `<span class="uid-chip uid-chip-green">${uid}
      <button class="chip-remove" onclick="removeWhite(${uid})">&times;</button>
    </span>`).join("");
}

function renderBlackList(list) {
  document.getElementById("blackCount").textContent = list.length;
  const el = document.getElementById("blackList");
  if (!list.length) { el.innerHTML = '<div class="empty-state">空白</div>'; return; }
  el.innerHTML = list.map(uid =>
    `<span class="uid-chip uid-chip-red">${uid}
      <button class="chip-remove" onclick="removeBlack(${uid})">&times;</button>
    </span>`).join("");
}

function appendLog(msg) {
  const box  = document.getElementById("logBox");
  const line = document.createElement("div");
  line.className = "log-line";
  const ts = new Date().toLocaleTimeString();
  line.innerHTML = `<span class="log-ts">${ts}</span> ${String(msg)
    .replace(/&/g, "&amp;").replace(/</g, "&lt;").replace(/>/g, "&gt;")}`;
  box.appendChild(line);
  box.scrollTop = box.scrollHeight;
}

function approve(uid)     { socket.emit("approve",      { uid }); }
function reject(uid)      { socket.emit("reject",       { uid }); }
function quickWhite(uid)  { socket.emit("add_white",    { uid }); }
function quickBlack(uid)  { socket.emit("add_black",    { uid }); }
function removeWhite(uid) { socket.emit("remove_white", { uid }); }
function removeBlack(uid) { socket.emit("remove_black", { uid }); }

document.getElementById("enterUnionBtn").addEventListener("click", () => {
  const val = document.getElementById("unionInput").value.trim();
  if (val) socket.emit("enter_union", { union_id: val });
});

document.getElementById("unionInput").addEventListener("keydown", (e) => {
  if (e.key === "Enter") document.getElementById("enterUnionBtn").click();
});

document.getElementById("refreshBtn").addEventListener("click",  () => { socket.emit("refresh"); });
document.getElementById("toggleAuto").addEventListener("click",  () => { socket.emit("toggle_auto"); });
document.getElementById("toggleDebug").addEventListener("click", () => { socket.emit("toggle_debug"); });

document.getElementById("addWhiteBtn").addEventListener("click", () => {
  const val = document.getElementById("whiteInput").value.trim();
  if (val) {
    socket.emit("add_white", { uid: parseInt(val) });
    document.getElementById("whiteInput").value = "";
  }
});

document.getElementById("addBlackBtn").addEventListener("click", () => {
  const val = document.getElementById("blackInput").value.trim();
  if (val) {
    socket.emit("add_black", { uid: parseInt(val) });
    document.getElementById("blackInput").value = "";
  }
});

document.getElementById("clearLog").addEventListener("click", () => {
  document.getElementById("logBox").innerHTML = "";
});

["whiteInput", "blackInput"].forEach(id => {
  document.getElementById(id).addEventListener("keydown", (e) => {
    if (e.key === "Enter")
      document.getElementById(id === "whiteInput" ? "addWhiteBtn" : "addBlackBtn").click();
  });
});
