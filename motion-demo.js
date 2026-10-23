const root = document.documentElement;
const section = document.getElementById('motionScroll');
const percent = document.getElementById('percent');

const clamp = (value, min = 0, max = 1) => Math.min(max, Math.max(min, value));
const smooth = (a, b, value) => {
  const t = clamp((value - a) / (b - a));
  return t * t * (3 - 2 * t);
};

function paint(progress) {
  const intro = 1 - smooth(0.015, 0.16, progress);
  const enter = smooth(0.16, 0.29, progress);
  const leave = 1 - smooth(0.70, 0.84, progress);
  const copy = enter * leave;
  const end = smooth(0.81, 0.985, progress);
  root.style.setProperty('--p', progress.toFixed(5));
  root.style.setProperty('--intro-opacity', intro.toFixed(4));
  root.style.setProperty('--copy-opacity', copy.toFixed(4));
  root.style.setProperty('--end-opacity', end.toFixed(4));
  percent.textContent = String(Math.round(progress * 100)).padStart(2, '0');
}

function measure() {
  const rect = section.getBoundingClientRect();
  const distance = Math.max(1, section.offsetHeight - innerHeight);
  paint(clamp(-rect.top / distance));
}

addEventListener('scroll', measure, {passive: true});
addEventListener('resize', measure);
measure();
