// Matrix rain background
(function () {
  const canvas = document.getElementById("matrix");
  const ctx = canvas.getContext("2d");
  const chars = "アイウエオカキクケコサシスセソ01ABCDEF<>/\\{}[]$#@%&*+=?!;:.";
  let cols, drops, fontSize = 14;

  function resize() {
    canvas.width = window.innerWidth;
    canvas.height = window.innerHeight;
    cols = Math.floor(canvas.width / fontSize);
    drops = Array(cols).fill(1).map(() => Math.random() * -50);
  }
  resize();
  window.addEventListener("resize", resize);

  function draw() {
    ctx.fillStyle = "rgba(5, 8, 10, 0.08)";
    ctx.fillRect(0, 0, canvas.width, canvas.height);
    ctx.fillStyle = "#00ff9c";
    ctx.font = fontSize + "px monospace";
    for (let i = 0; i < drops.length; i++) {
      const ch = chars[Math.floor(Math.random() * chars.length)];
      ctx.fillText(ch, i * fontSize, drops[i] * fontSize);
      if (drops[i] * fontSize > canvas.height && Math.random() > 0.975) {
        drops[i] = 0;
      }
      drops[i]++;
    }
  }
  setInterval(draw, 50);
})();

// Scroll reveal animations
(function () {
  const sections = document.querySelectorAll("section");
  sections.forEach((s) => s.classList.add("reveal"));
  const observer = new IntersectionObserver(
    (entries) => {
      entries.forEach((e) => {
        if (e.isIntersecting) {
          e.target.classList.add("visible");
        }
      });
    },
    { threshold: 0.05 }
  );
  sections.forEach((s) => observer.observe(s));
})();

// Nav active link highlight on scroll
(function () {
  const links = document.querySelectorAll(".nav-links a");
  window.addEventListener("scroll", () => {
    let current = "";
    document.querySelectorAll("section[id]").forEach((sec) => {
      if (window.scrollY >= sec.offsetTop - 150) current = sec.id;
    });
    links.forEach((a) => {
      if (a.getAttribute("href") === "#" + current) {
        a.style.color = "#00ff9c";
      } else if (!a.classList.contains("cta-nav")) {
        a.style.color = "";
      }
    });
  });
})();

// Countdown timer (set event date here if desired)
(function () {
  const el = document.getElementById("countdown");
  // Optional: set a future date to show a live countdown, e.g.
  // const target = new Date("2026-10-20T10:00:00").getTime();
  // If no date set, show a static message.
  const target = null;
  if (!target) {
    el.textContent = "SYSTEM ONLINE · ARENA OPEN";
    return;
  }
  function tick() {
    const now = Date.now();
    let diff = target - now;
    if (diff <= 0) { el.textContent = "COMPETITION LIVE"; return; }
    const d = Math.floor(diff / 86400000);
    const h = Math.floor((diff % 86400000) / 3600000);
    const m = Math.floor((diff % 3600000) / 60000);
    const s = Math.floor((diff % 60000) / 1000);
    el.textContent = `T-MINUS ${d}d ${h}h ${m}m ${s}s`;
  }
  tick();
  setInterval(tick, 1000);
})();
