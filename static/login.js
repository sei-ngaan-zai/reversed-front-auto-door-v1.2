const socket = io();

socket.on("login_result", (data) => {
  setLoading(false);
  if (data.ok) {
    window.location.href = "/dashboard";
  } else {
    showError(data.error || "Login failed");
  }
});

document.getElementById("loginForm").addEventListener("submit", (e) => {
  e.preventDefault();
  const email    = document.getElementById("email").value.trim();
  const password = document.getElementById("password").value.trim();
  if (!email || !password) return;
  clearError();
  setLoading(true);
  socket.emit("login", { email, password });
});

function setLoading(v) {
  document.getElementById("loginBtn").disabled = v;
  document.getElementById("loginBtnText").textContent = v ? "連線中…" : "Connect";
  document.getElementById("loginSpinner").classList.toggle("hidden", !v);
}

function showError(msg) {
  const el = document.getElementById("loginError");
  el.textContent = msg;
  el.classList.remove("hidden");
}

function clearError() {
  document.getElementById("loginError").classList.add("hidden");
}

document.getElementById("togglePassword").addEventListener("click", () => {
  const input = document.getElementById("password");
  input.type = input.type === "password" ? "text" : "password";
});
