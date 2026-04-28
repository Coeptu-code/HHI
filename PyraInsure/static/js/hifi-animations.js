// PyraInsure Hi-Fi Animations — Vanilla JS ports of React components

// Ring: animated SVG stroke-dashoffset animation for score rings
function initRings() {
  document.querySelectorAll('[data-ring-value]').forEach(container => {
    const value = parseInt(container.dataset.ringValue, 10) || 0;
    const size = parseInt(container.dataset.ringSize, 10) || 220;
    const strokeW = parseInt(container.dataset.ringStroke, 10) || 14;
    const color = container.dataset.ringColor || 'var(--orange)';
    const track = 'var(--bg-2)';
    const r = (size - strokeW) / 2;
    const circumference = 2 * Math.PI * r;
    const cx = size / 2, cy = size / 2;

    const svg = document.createElementNS('http://www.w3.org/2000/svg', 'svg');
    svg.setAttribute('width', size);
    svg.setAttribute('height', size);
    svg.style.display = 'block';

    // Track circle
    const trackCircle = document.createElementNS('http://www.w3.org/2000/svg', 'circle');
    trackCircle.setAttribute('cx', cx);
    trackCircle.setAttribute('cy', cy);
    trackCircle.setAttribute('r', r);
    trackCircle.setAttribute('stroke', track);
    trackCircle.setAttribute('stroke-width', strokeW);
    trackCircle.setAttribute('fill', 'none');

    // Fill circle
    const fillCircle = document.createElementNS('http://www.w3.org/2000/svg', 'circle');
    fillCircle.setAttribute('cx', cx);
    fillCircle.setAttribute('cy', cy);
    fillCircle.setAttribute('r', r);
    fillCircle.setAttribute('stroke', color);
    fillCircle.setAttribute('stroke-width', strokeW);
    fillCircle.setAttribute('fill', 'none');
    fillCircle.setAttribute('stroke-dasharray', circumference);
    fillCircle.setAttribute('stroke-dashoffset', circumference);
    fillCircle.setAttribute('stroke-linecap', 'round');
    fillCircle.setAttribute('transform', `rotate(-90 ${cx} ${cy})`);
    fillCircle.style.transition = 'stroke-dashoffset 1.2s cubic-bezier(.2,.8,.2,1.0)';

    svg.appendChild(trackCircle);
    svg.appendChild(fillCircle);
    container.appendChild(svg);

    // Trigger animation after a frame so transition fires
    requestAnimationFrame(() => requestAnimationFrame(() => {
      fillCircle.setAttribute('stroke-dashoffset', circumference - (value / 100) * circumference);
    }));
  });
}

// Confetti: burst animation from container
function triggerConfetti(container) {
  const colors = ['#e57244','#2d7a7a','#c47a1a','#2f8a5b','#d35a2e','#226363'];
  const count = 28;
  const wrap = document.createElement('div');
  wrap.style.cssText = 'position:absolute;inset:0;pointer-events:none;overflow:hidden;z-index:10;';

  for (let i = 0; i < count; i++) {
    const piece = document.createElement('span');
    piece.className = 'confetti-piece';
    piece.style.left = (Math.random() * 100).toFixed(1) + '%';
    piece.style.top = '0';
    piece.style.animationDelay = (Math.random() * 0.6).toFixed(2) + 's';
    piece.style.background = colors[i % colors.length];
    piece.style.transform = `rotate(${Math.floor(Math.random() * 360)}deg)`;
    wrap.appendChild(piece);
  }

  container.appendChild(wrap);
  setTimeout(() => wrap.remove(), 2200);
}

// Counter: animate number from 0 to target
function animateCounter(element, target, duration = 1200) {
  let start = null;
  function step(ts) {
    if (!start) start = ts;
    const progress = Math.min((ts - start) / duration, 1);
    element.textContent = Math.round(progress * target);
    if (progress < 1) requestAnimationFrame(step);
  }
  requestAnimationFrame(step);
}

// Severity bars: animate width on intersection
function initSevBars() {
  const observer = new IntersectionObserver((entries) => {
    entries.forEach(entry => {
      if (entry.isIntersecting) {
        const fill = entry.target;
        const width = fill.dataset.width || '50';
        // Small delay before triggering animation
        setTimeout(() => {
          fill.style.width = width + '%';
        }, 100);
        observer.unobserve(fill);
      }
    });
  });

  document.querySelectorAll('.sev-bar > div').forEach(el => {
    el.style.width = '0';
    observer.observe(el);
  });
}

// DOMContentLoaded: init all animations
document.addEventListener('DOMContentLoaded', () => {
  initRings();
  initSevBars();

  // Score page animations: confetti + counter
  const scoreWrap = document.querySelector('[data-ring-animate]');
  if (scoreWrap) {
    const target = parseInt(scoreWrap.dataset.ringValue, 10);
    const counterEl = document.querySelector('[data-counter-target]');

    if (counterEl) {
      animateCounter(counterEl, target, 1200);
    }

    // Trigger confetti 1400ms after page load (ring animation finishes at 1200ms)
    setTimeout(() => triggerConfetti(scoreWrap.parentElement), 1400);
  }
});
