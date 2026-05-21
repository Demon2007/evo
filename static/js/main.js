/* ====================================================
   EduNova — Main JavaScript
   ==================================================== */

// ── Page Loader ──────────────────────────────────────
document.addEventListener('DOMContentLoaded', () => {
  const loader = document.getElementById('page-loader');
  if (loader) {
    setTimeout(() => loader.classList.add('hidden'), 400);
  }

  initSidebar();
  initModals();
  initToasts();
  initCounters();
  initSearch();
  initDjangoMessages();
  initDeleteConfirm();
});

// ── Sidebar ──────────────────────────────────────────
function initSidebar() {
  const toggle = document.getElementById('sidebar-toggle');
  const sidebar = document.getElementById('sidebar');
  const mainContent = document.getElementById('main-content');
  const overlay = document.getElementById('mobile-overlay');
  if (!sidebar) return;

  const isMobile = () => window.innerWidth < 768;

  // Restore desktop collapsed state
  if (localStorage.getItem('sidebar-collapsed') === 'true' && !isMobile()) {
    sidebar.classList.add('collapsed');
    mainContent && mainContent.classList.add('expanded');
  }

  function openMobile() {
    sidebar.classList.add('mobile-open');
    overlay && overlay.classList.add('active');
    toggle && toggle.classList.add('open');
    document.body.style.overflow = 'hidden';
  }

  function closeMobile() {
    sidebar.classList.remove('mobile-open');
    overlay && overlay.classList.remove('active');
    toggle && toggle.classList.remove('open');
    document.body.style.overflow = '';
  }

  toggle && toggle.addEventListener('click', () => {
    if (isMobile()) {
      sidebar.classList.contains('mobile-open') ? closeMobile() : openMobile();
    } else {
      const collapsed = sidebar.classList.toggle('collapsed');
      mainContent && mainContent.classList.toggle('expanded', collapsed);
      localStorage.setItem('sidebar-collapsed', collapsed);
    }
  });

  // Close sidebar on nav link click (mobile)
  sidebar.querySelectorAll('.nav-item').forEach(link => {
    link.addEventListener('click', () => {
      if (isMobile()) closeMobile();
    });
  });

  overlay && overlay.addEventListener('click', closeMobile);

  window.addEventListener('resize', () => {
    if (!isMobile()) closeMobile();
  }, { passive: true });
}

// ── Modals ───────────────────────────────────────────
function initModals() {
  document.querySelectorAll('[data-modal]').forEach(btn => {
    btn.addEventListener('click', () => openModal(btn.dataset.modal));
  });

  document.querySelectorAll('.modal-close, [data-close-modal]').forEach(btn => {
    btn.addEventListener('click', () => {
      const modal = btn.closest('.modal-overlay');
      modal && closeModal(modal.id);
    });
  });

  document.querySelectorAll('.modal-overlay').forEach(overlay => {
    overlay.addEventListener('click', e => {
      if (e.target === overlay) closeModal(overlay.id);
    });
  });

  document.addEventListener('keydown', e => {
    if (e.key === 'Escape') {
      document.querySelectorAll('.modal-overlay.active').forEach(m => closeModal(m.id));
    }
  });
}

function openModal(id) {
  const modal = document.getElementById(id);
  if (modal) {
    modal.classList.add('active');
    document.body.style.overflow = 'hidden';
  }
}

function closeModal(id) {
  const modal = document.getElementById(id);
  if (modal) {
    modal.classList.remove('active');
    document.body.style.overflow = '';
  }
}

window.openModal = openModal;
window.closeModal = closeModal;

// ── Toasts ───────────────────────────────────────────
function initToasts() {
  if (!document.getElementById('toast-container')) {
    const c = document.createElement('div');
    c.id = 'toast-container';
    document.body.appendChild(c);
  }
}

function showToast(message, type = 'info', title = '') {
  const container = document.getElementById('toast-container');
  if (!container) return;

  const icons = {
    success: `<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><path d="M22 11.08V12a10 10 0 1 1-5.93-9.14"/><polyline points="22 4 12 14.01 9 11.01"/></svg>`,
    error:   `<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><circle cx="12" cy="12" r="10"/><line x1="15" y1="9" x2="9" y2="15"/><line x1="9" y1="9" x2="15" y2="15"/></svg>`,
    warning: `<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><path d="M10.29 3.86L1.82 18a2 2 0 0 0 1.71 3h16.94a2 2 0 0 0 1.71-3L13.71 3.86a2 2 0 0 0-3.42 0z"/><line x1="12" y1="9" x2="12" y2="13"/><line x1="12" y1="17" x2="12.01" y2="17"/></svg>`,
    info:    `<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><circle cx="12" cy="12" r="10"/><line x1="12" y1="8" x2="12" y2="12"/><line x1="12" y1="16" x2="12.01" y2="16"/></svg>`,
  };

  const defaultTitles = { success: 'Успешно', error: 'Ошибка', warning: 'Внимание', info: 'Информация' };

  const toast = document.createElement('div');
  toast.className = `toast ${type}`;
  toast.innerHTML = `
    <span class="toast-icon">${icons[type] || icons.info}</span>
    <div class="toast-body">
      <div class="toast-title">${title || defaultTitles[type]}</div>
      <div class="toast-msg">${message}</div>
    </div>
    <button class="toast-dismiss" onclick="this.closest('.toast').remove()">×</button>
  `;

  container.appendChild(toast);
  setTimeout(() => toast.style.opacity = '0', 4000);
  setTimeout(() => toast.remove(), 4400);
}

window.showToast = showToast;

// ── Show Django messages as toasts ───────────────────
function initDjangoMessages() {
  document.querySelectorAll('[data-django-message]').forEach(el => {
    const type = el.dataset.djangoMessage;
    const msg = el.textContent.trim();
    if (msg) showToast(msg, type === 'error' ? 'error' : type === 'warning' ? 'warning' : 'success');
    el.remove();
  });
}

// ── Delete Confirm ───────────────────────────────────
function initDeleteConfirm() {
  document.querySelectorAll('[data-confirm]').forEach(btn => {
    btn.addEventListener('click', e => {
      const msg = btn.dataset.confirm || 'Вы уверены?';
      if (!confirm(msg)) e.preventDefault();
    });
  });
}

// ── Animated Counters ────────────────────────────────
function initCounters() {
  const counters = document.querySelectorAll('[data-count]');
  if (!counters.length) return;

  const observer = new IntersectionObserver(entries => {
    entries.forEach(entry => {
      if (entry.isIntersecting) {
        animateCounter(entry.target);
        observer.unobserve(entry.target);
      }
    });
  }, { threshold: 0.5 });

  counters.forEach(c => observer.observe(c));
}

function animateCounter(el) {
  const target = parseInt(el.dataset.count, 10);
  const duration = 1200;
  const start = performance.now();
  const update = ts => {
    const elapsed = ts - start;
    const progress = Math.min(elapsed / duration, 1);
    const value = Math.round(easeOutQuart(progress) * target);
    el.textContent = value.toLocaleString('ru');
    if (progress < 1) requestAnimationFrame(update);
  };
  requestAnimationFrame(update);
}

function easeOutQuart(t) { return 1 - Math.pow(1 - t, 4); }

// ── Live Search ──────────────────────────────────────
function initSearch() {
  const searchInput = document.getElementById('live-search');
  const searchTarget = document.getElementById('search-target');
  if (!searchInput || !searchTarget) return;

  searchInput.addEventListener('input', () => {
    const q = searchInput.value.toLowerCase().trim();
    const rows = searchTarget.querySelectorAll('[data-search-item]');
    let visible = 0;
    rows.forEach(row => {
      const text = row.textContent.toLowerCase();
      const show = !q || text.includes(q);
      row.style.display = show ? '' : 'none';
      if (show) visible++;
    });
    const empty = searchTarget.querySelector('.search-empty');
    if (empty) empty.style.display = visible === 0 ? '' : 'none';
  });
}

// ── Navbar scroll effect (landing) ───────────────────
const landNav = document.querySelector('.land-nav');
if (landNav) {
  window.addEventListener('scroll', () => {
    landNav.classList.toggle('scrolled', window.scrollY > 20);
  }, { passive: true });
}

// ── Active nav highlight ──────────────────────────────
document.querySelectorAll('.nav-item').forEach(item => {
  if (item.href && window.location.pathname.startsWith(new URL(item.href, location.origin).pathname)) {
    item.classList.add('active');
  }
});
