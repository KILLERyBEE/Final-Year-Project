/* =============================================
   AIRNAV — guide.js
   Guide page interactivity: navbar, modals, scroll reveal
   ============================================= */

// ===== NAVBAR SCROLL =====
const navbar = document.getElementById('navbar');
window.addEventListener('scroll', () => {
    navbar.classList.toggle('scrolled', window.scrollY > 40);
}, { passive: true });

// ===== HAMBURGER =====
const hamburger = document.getElementById('hamburger');
const navLinks = document.getElementById('navLinks');
hamburger.addEventListener('click', () => {
    hamburger.classList.toggle('open');
    navLinks.classList.toggle('open');
});
navLinks.querySelectorAll('a').forEach(link => {
    link.addEventListener('click', () => {
        hamburger.classList.remove('open');
        navLinks.classList.remove('open');
    });
});

// ===== MODAL DATA =====
const modalData = {
    main: {
        title: 'Main Program',
        body: 'The main program is the central entry point for AirNav. It initialises MediaPipe Hands, loads the CNN gesture classifier, and activates the appropriate module based on the detected gesture mode. It continuously processes webcam frames and uses hand landmark data to determine which gesture the user is performing, then routes control to the relevant module (scroll, zoom, volume, video, document, or slide).'
    },
    scroll: {
        title: 'Scroll Control',
        body: 'The scroll module uses the orientation and height of your index finger to scroll any window in real-time. Moving your finger upward scrolls the page up and pointing it downward scrolls the page down. It supports velocity-sensitive scrolling so the faster you move, the quicker it scrolls. Activate scroll mode by performing a Peace gesture from the master program.'
    },
    zoom: {
        title: 'Zoom Control',
        body: 'Zoom control detects the pixel distance between your thumb tip and index finger tip. As you move your fingers apart, it triggers a zoom-in action; bringing them together triggers zoom-out. This module uses pyautogui to send Ctrl+Plus and Ctrl+Minus commands, making it universally compatible with browsers, editors, and image viewers.'
    },
    volume: {
        title: 'Volume Adjustment',
        body: 'Volume control maps the vertical Y-coordinate of your open palm to the system volume level. The module uses the pycaw library on Windows to directly interface with the audio API. Raising your hand increases volume while lowering it decreases it. A closed fist toggles mute. The response is smooth and lag-free, with a configurable sensitivity range.'
    },
    video: {
        title: 'Video Playback Control',
        body: 'This module supports play/pause, fast-forward, and rewind for any video application running in focus. A closed fist sends a space bar press (play/pause). Pointing right sends a right-arrow key press (seek forward) and pointing left sends left-arrow (rewind). It integrates at the OS keyboard event level, so it works with VLC, YouTube, Netflix, and most other players.'
    },
    app: {
        title: 'App Switching',
        body: 'The app switching module detects directional hand swipes and simulates Alt+Tab keyboard shortcuts to cycle through open applications. A rightward swipe moves forward through the task switcher while a leftward swipe goes back. This module uses pyautogui to send the keyboard combinations and works reliably on Windows, making multitasking completely hands-free.'
    },
    doc: {
        title: 'Document Control',
        body: 'Document control enables gesture-based navigation through PDF files, Word documents, and file explorers. An open-palm rightward swipe sends Page Down and a leftward swipe sends Page Up. Pinch gestures trigger Ctrl+Plus/Minus for zoom. The module can also detect a fist gesture to close the current file or exit the document view, giving you complete hands-free document reading.'
    },
    slide: {
        title: 'Slide Travel',
        body: 'Slide travel is designed for presenters who want to control PowerPoint, Google Slides, or LibreOffice Impress without a physical clicker. A rightward swipe sends the right-arrow key to advance to the next slide. A leftward swipe sends the left-arrow key to go back. The module also supports a laser-pointer simulation mode where hand position maps to on-screen cursor position.'
    }
};

// ===== MODAL LOGIC =====
const overlay = document.getElementById('modalOverlay');
const modalTitle = document.getElementById('modalTitle');
const modalBody = document.getElementById('modalBody');
const modalIcon = document.getElementById('modalIcon');
const modalClose = document.getElementById('modalClose');

function openModal(key) {
    const data = modalData[key];
    if (!data) return;
    modalTitle.textContent = data.title;
    modalBody.textContent = data.body;
    modalIcon.innerHTML = `<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.8">
    <circle cx="12" cy="12" r="10"/>
    <line x1="12" y1="8" x2="12" y2="12"/>
    <line x1="12" y1="16" x2="12.01" y2="16"/>
  </svg>`;
    overlay.classList.add('active');
    document.body.style.overflow = 'hidden';
}

function closeModal() {
    overlay.classList.remove('active');
    document.body.style.overflow = '';
}

document.querySelectorAll('.guide-btn').forEach(btn => {
    btn.addEventListener('click', () => openModal(btn.getAttribute('data-modal')));
});

modalClose.addEventListener('click', closeModal);
overlay.addEventListener('click', e => { if (e.target === overlay) closeModal(); });
document.addEventListener('keydown', e => { if (e.key === 'Escape') closeModal(); });

// ===== SCROLL REVEAL =====
document.querySelectorAll('.reveal').forEach(el => {
    new IntersectionObserver((entries) => {
        entries.forEach(entry => {
            if (entry.isIntersecting) {
                entry.target.classList.add('visible');
            }
        });
    }, { threshold: 0.1, rootMargin: '0px 0px -40px 0px' }).observe(el);
});

console.log('AirNav Guide | Script loaded ✓');
