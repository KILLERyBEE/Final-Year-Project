/* =============================================
   AIRNAV — script.js
   Interactivity: Navbar, Modals, Scroll Reveal,
   Hamburger Menu, Smooth Scroll
   ============================================= */

// ===== NAVBAR SCROLL EFFECT =====
const navbar = document.getElementById('navbar');

window.addEventListener('scroll', () => {
  if (window.scrollY > 40) {
    navbar.classList.add('scrolled');
  } else {
    navbar.classList.remove('scrolled');
  }
}, { passive: true });

// ===== HAMBURGER MENU =====
const hamburger = document.getElementById('hamburger');
const navLinks = document.getElementById('navLinks');

hamburger.addEventListener('click', () => {
  hamburger.classList.toggle('open');
  navLinks.classList.toggle('open');
});

// Close menu when a link is clicked
navLinks.querySelectorAll('a').forEach(link => {
  link.addEventListener('click', () => {
    hamburger.classList.remove('open');
    navLinks.classList.remove('open');
  });
});

// ===== MODAL DATA =====
const modalData = {
  doc: {
    title: 'Document Control',
    icon: `<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.8">
             <rect x="4" y="2" width="16" height="20" rx="2"/>
             <line x1="8" y1="7" x2="16" y2="7"/>
             <line x1="8" y1="11" x2="16" y2="11"/>
             <line x1="8" y1="15" x2="12" y2="15"/>
           </svg>`,
    body: 'Navigate through documents and files using intuitive hand gestures. Swipe, scroll, zoom, and flip through pages without touching a single key. AirNav\'s document control module recognizes open-palm swipes for page turns and pinch gestures for zooming, enabling seamless reading and editing workflow automation. Works with PDF viewers, Word documents, and file explorers.'
  },
  zoom: {
    title: 'Zoom Control',
    icon: `<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.8">
             <circle cx="11" cy="11" r="8"/>
             <line x1="21" y1="21" x2="16.65" y2="16.65"/>
             <line x1="8" y1="11" x2="14" y2="11"/>
             <line x1="11" y1="8" x2="11" y2="14"/>
           </svg>`,
    body: 'Effortlessly zoom in and out of your screen or applications with a simple pinch gesture. The zoom control module intelligently detects the distance between your thumb and index finger, translating finger spacing into smooth, lag-free zoom transitions. Supports browsers, documents, images, maps, and any zoomable interface in real-time with sub-100ms latency.'
  },
  slide: {
    title: 'Slide Navigation',
    icon: `<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.8">
             <rect x="2" y="3" width="20" height="14" rx="2"/>
             <polyline points="8,21 12,17 16,21"/>
             <line x1="12" y1="17" x2="12" y2="21"/>
           </svg>`,
    body: 'Transform your presentations with hands-free slide control. A right-swipe gesture advances to the next slide while a left-swipe goes back. The system supports laser-pointer simulation via hand position tracking, helping speakers deliver impactful presentations without a physical clicker or remote. Compatible with PowerPoint, Google Slides, and LibreOffice Impress.'
  },
  volume: {
    title: 'Volume Adjustment',
    icon: `<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.8">
             <polygon points="11,5 6,9 2,9 2,15 6,15 11,19"/>
             <path d="M15.54 8.46a5 5 0 0 1 0 7.07"/>
             <path d="M19.07 4.93a10 10 0 0 1 0 14.14"/>
           </svg>`,
    body: 'Control system audio intuitively with vertical hand gestures. Raising your hand increases volume while lowering it decreases it. AirNav maps the vertical position of your palm to the system audio level in real-time, supporting both smooth gradual changes and quick mute toggles via a fist gesture. Integrates directly with the OS audio API for universal compatibility.'
  },
  video: {
    title: 'Video Playback Control',
    icon: `<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.8">
             <polygon points="23,7 16,12 23,17"/>
             <rect x="1" y="5" width="15" height="14" rx="2"/>
           </svg>`,
    body: 'AirNav supports media controls including play, pause, fast-forward, and rewind — all through mid-air gestures. A closed fist pauses playback, while pointing sideways seeks forward or backward. The system integrates with system-level media APIs, giving you universal control over any video application or stream. No special software installation required on the target video player.'
  },
  scroll: {
    title: 'Scroll Control',
    icon: `<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.8">
             <path d="M12 5v14"/>
             <polyline points="19,12 12,19 5,12"/>
           </svg>`,
    body: 'The scroll control module tracks the orientation and position of your hand to scroll web pages and documents naturally. Moving your index finger upward scrolls content up, while pointing it down scrolls down. The system supports velocity-sensitive scrolling for both subtle fine-control and rapid navigation across long pages. Works across all applications and browsers without configuration.'
  }
};

// ===== MODAL LOGIC =====
const overlay = document.getElementById('modalOverlay');
const modalBox = document.getElementById('modalBox');
const modalTitle = document.getElementById('modalTitle');
const modalBody = document.getElementById('modalBody');
const modalIcon = document.getElementById('modalIcon');
const modalClose = document.getElementById('modalClose');

function openModal(key) {
  const data = modalData[key];
  if (!data) return;
  modalTitle.textContent = data.title;
  modalBody.textContent = data.body;
  modalIcon.innerHTML = data.icon;
  overlay.classList.add('active');
  document.body.style.overflow = 'hidden';
}

function closeModal() {
  overlay.classList.remove('active');
  document.body.style.overflow = '';
}

// Attach to all "Learn More" buttons on cards → redirect to guide page
document.querySelectorAll('.btn-card').forEach(btn => {
  btn.addEventListener('click', () => {
    window.location.href = 'guide.html';
  });
});

modalClose.addEventListener('click', closeModal);

overlay.addEventListener('click', (e) => {
  if (e.target === overlay) closeModal();
});

document.addEventListener('keydown', (e) => {
  if (e.key === 'Escape') closeModal();
});

// ===== HERO PLAY BUTTON =====
const playCircle = document.querySelector('.play-circle');
if (playCircle) {
  playCircle.addEventListener('click', () => {
    // Pulse animation then scroll to features
    playCircle.style.transition = 'transform 0.15s ease, box-shadow 0.15s ease';
    playCircle.style.transform = 'translate(-50%, -50%) scale(0.92)';
    playCircle.style.boxShadow = '0 0 50px rgba(168,85,247,0.7)';
    setTimeout(() => {
      playCircle.style.transform = '';
      playCircle.style.boxShadow = '';
      document.getElementById('features').scrollIntoView({ behavior: 'smooth' });
    }, 180);
  });
}

// ===== HERO SCROLL BUTTONS =====
const getStartedBtn = document.getElementById('getStartedBtn');
const learnMoreBtn = document.getElementById('learnMoreBtn');

if (getStartedBtn) {
  getStartedBtn.addEventListener('click', () => {
    document.getElementById('features').scrollIntoView({ behavior: 'smooth' });
  });
}

if (learnMoreBtn) {
  learnMoreBtn.addEventListener('click', () => {
    document.getElementById('cta').scrollIntoView({ behavior: 'smooth' });
  });
}

// ===== START / STOP CAMERA (Flask backend) =====
const SERVER = 'http://localhost:5000';

const startCameraBtn = document.getElementById('startCameraBtn');
const stopCameraBtn = document.getElementById('stopCameraBtn');

// Helper: show a temporary status toast
function showToast(message, type = 'info') {
  // Remove existing toast
  const old = document.getElementById('airnav-toast');
  if (old) old.remove();

  const toast = document.createElement('div');
  toast.id = 'airnav-toast';
  toast.textContent = message;
  toast.style.cssText = `
    position: fixed; bottom: 2rem; left: 50%; transform: translateX(-50%);
    background: ${type === 'error' ? '#2a0a0a' : type === 'success' ? '#0a2a0a' : '#1a1a1a'};
    border: 1px solid ${type === 'error' ? 'rgba(255,80,80,0.4)' : type === 'success' ? 'rgba(80,255,80,0.3)' : 'rgba(255,255,255,0.15)'};
    color: ${type === 'error' ? '#ff8080' : type === 'success' ? '#80ff80' : '#cccccc'};
    padding: 0.75rem 1.5rem; border-radius: 10px; font-size: 0.85rem; font-weight: 500;
    z-index: 9999; font-family: inherit;
    box-shadow: 0 8px 30px rgba(0,0,0,0.5);
    animation: fadeSlideUp 0.3s ease both;
  `;
  document.body.appendChild(toast);
  setTimeout(() => toast.remove(), 3500);
}

// Helper: set button loading / active state
function setButtonState(btn, state) {
  if (!btn) return;
  btn.disabled = (state === 'loading');
  if (state === 'loading') {
    btn.dataset.original = btn.textContent;
    btn.textContent = '⏳ Please wait...';
    btn.style.opacity = '0.7';
  } else if (state === 'running') {
    btn.textContent = '🟢 ' + (btn.dataset.original || btn.textContent.replace('⏳ Please wait...', ''));
    btn.style.opacity = '1';
    btn.disabled = false;
  } else {
    btn.textContent = btn.dataset.original || btn.textContent;
    btn.style.opacity = '1';
    btn.disabled = false;
  }
}

// Start Camera button
if (startCameraBtn) {
  startCameraBtn.addEventListener('click', async () => {
    setButtonState(startCameraBtn, 'loading');
    try {
      const res = await fetch(`${SERVER}/start`, { method: 'POST' });
      const data = await res.json();

      if (data.status === 'started') {
        showToast('✅ Gesture controller started! Webcam is now active.', 'success');
        setButtonState(startCameraBtn, 'running');
        startCameraBtn.textContent = '🟢 Camera Running';
      } else if (data.status === 'already_running') {
        showToast('ℹ️ Gesture controller is already running.', 'info');
        setButtonState(startCameraBtn, 'normal');
        startCameraBtn.textContent = '🟢 Camera Running';
      } else {
        showToast(`❌ Error: ${data.message}`, 'error');
        setButtonState(startCameraBtn, 'normal');
      }
    } catch (err) {
      showToast('❌ Cannot connect to AirNav server. Please run: python server.py', 'error');
      setButtonState(startCameraBtn, 'normal');
      console.error('AirNav server error:', err);
    }
  });
}

// Stop Camera button
if (stopCameraBtn) {
  stopCameraBtn.addEventListener('click', async () => {
    setButtonState(stopCameraBtn, 'loading');
    try {
      const res = await fetch(`${SERVER}/stop`, { method: 'POST' });
      const data = await res.json();

      if (data.status === 'stopped') {
        showToast('🛑 Gesture controller stopped. Webcam closed.', 'info');
        setButtonState(stopCameraBtn, 'normal');
        if (startCameraBtn) startCameraBtn.textContent = 'Start Camera';
      } else if (data.status === 'not_running') {
        showToast('ℹ️ Gesture controller is not running.', 'info');
        setButtonState(stopCameraBtn, 'normal');
      } else {
        showToast(`❌ Error: ${data.message}`, 'error');
        setButtonState(stopCameraBtn, 'normal');
      }
    } catch (err) {
      showToast('❌ Cannot connect to AirNav server. Please run: python server.py', 'error');
      setButtonState(stopCameraBtn, 'normal');
      console.error('AirNav server error:', err);
    }
  });
}

// Sync button state on page load
async function syncStatus() {
  try {
    const res = await fetch(`${SERVER}/status`);
    const data = await res.json();
    if (data.running && startCameraBtn) {
      startCameraBtn.textContent = '🟢 Camera Running';
    }
  } catch (_) {
    // Server not running yet – that's fine
  }
}
syncStatus();

// ===== SCROLL REVEAL =====
const revealEls = document.querySelectorAll(
  '.feature-card, .cta-inner, .features-header, .hero-text, .hero-visual'
);

// Add reveal class
revealEls.forEach(el => el.classList.add('reveal'));

const revealObserver = new IntersectionObserver((entries) => {
  entries.forEach((entry, i) => {
    if (entry.isIntersecting) {
      // Stagger cards in a grid
      const delay = entry.target.classList.contains('feature-card')
        ? Array.from(revealEls).indexOf(entry.target) * 80
        : 0;
      setTimeout(() => {
        entry.target.classList.add('visible');
      }, delay);
      revealObserver.unobserve(entry.target);
    }
  });
}, {
  threshold: 0.12,
  rootMargin: '0px 0px -40px 0px'
});

revealEls.forEach(el => revealObserver.observe(el));

// ===== NAV ACTIVE LINK ON SCROLL =====
const sections = document.querySelectorAll('section[id]');
const navAnchors = document.querySelectorAll('.nav-links a');

const sectionObserver = new IntersectionObserver((entries) => {
  entries.forEach(entry => {
    if (entry.isIntersecting) {
      navAnchors.forEach(a => {
        a.classList.remove('active');
        if (a.getAttribute('href') === '#' + entry.target.id) {
          a.classList.add('active');
        }
      });
    }
  });
}, { threshold: 0.4 });

sections.forEach(s => sectionObserver.observe(s));

// ===== CURSOR GLOW (optional subtle effect on hero) =====
const heroSection = document.querySelector('.hero');
if (heroSection) {
  heroSection.addEventListener('mousemove', (e) => {
    const rect = heroSection.getBoundingClientRect();
    const x = ((e.clientX - rect.left) / rect.width) * 100;
    const y = ((e.clientY - rect.top) / rect.height) * 100;
    heroSection.style.setProperty('--mx', x + '%');
    heroSection.style.setProperty('--my', y + '%');
  });
}

// ===== FEATURE CARD TILT ON HOVER =====
document.querySelectorAll('.feature-card').forEach(card => {
  card.addEventListener('mousemove', (e) => {
    const rect = card.getBoundingClientRect();
    const cx = rect.left + rect.width / 2;
    const cy = rect.top + rect.height / 2;
    const dx = (e.clientX - cx) / (rect.width / 2);
    const dy = (e.clientY - cy) / (rect.height / 2);
    card.style.transform = `translateY(-4px) rotateX(${-dy * 4}deg) rotateY(${dx * 4}deg)`;
  });

  card.addEventListener('mouseleave', () => {
    card.style.transform = '';
  });
});

console.log('AirNav – Gesture-Driven Automation | Script loaded ✓');
