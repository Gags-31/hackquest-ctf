// Live clock countdown label + nav active highlight on scroll
window.addEventListener('scroll', () => {
  const links = document.querySelectorAll('nav a');
  links.forEach(a => {
    const target = document.querySelector(a.getAttribute('href'));
    if (target) {
      const rect = target.getBoundingClientRect();
      if (rect.top <= 120 && rect.bottom >= 120) a.style.color = '#2ea043';
      else a.style.color = '#58a6ff';
    }
  });
});
