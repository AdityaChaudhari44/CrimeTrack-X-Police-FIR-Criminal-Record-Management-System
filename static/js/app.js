document.addEventListener("DOMContentLoaded", () => {
  const toggle = document.getElementById("navToggle");
  const sidebar = document.getElementById("sidebar");
  if (toggle && sidebar) toggle.addEventListener("click", () => sidebar.classList.toggle("open"));
  const current = window.location.pathname;
  document.querySelectorAll(".side-nav a").forEach((link) => {
    if (link.pathname === current || (link.pathname !== "/" && current.startsWith(link.pathname))) link.classList.add("active");
  });
});
