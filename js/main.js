/* ===============================================
   GOWSHIK S - Portfolio JavaScript
   Professional Developer Portfolio
   =============================================== */

document.addEventListener('DOMContentLoaded', () => {
  initThemeToggle();
  initNavbarScroll();
  initMobileNav();
  initScrollSpy();
  initScrollReveal();
  initSmoothScroll();
  initIframeLoader();
  initYear();
});

// ====== THEME TOGGLE ======
function initThemeToggle() {
  const themeToggle = document.getElementById('themeToggle');
  const prefersDark = window.matchMedia('(prefers-color-scheme: dark)');
  
  // Check for saved theme or use system preference
  const savedTheme = localStorage.getItem('theme');
  if (savedTheme) {
    document.documentElement.setAttribute('data-theme', savedTheme);
  } else if (!prefersDark.matches) {
    document.documentElement.setAttribute('data-theme', 'light');
  }
  
  themeToggle?.addEventListener('click', () => {
    const currentTheme = document.documentElement.getAttribute('data-theme');
    const newTheme = currentTheme === 'light' ? 'dark' : 'light';
    
    document.documentElement.setAttribute('data-theme', newTheme);
    localStorage.setItem('theme', newTheme);
    
    // Add rotation animation
    themeToggle.style.transform = 'rotate(360deg)';
    setTimeout(() => {
      themeToggle.style.transform = '';
    }, 300);
  });
}

// ====== NAVBAR SCROLL EFFECT ======
function initNavbarScroll() {
  const navbar = document.querySelector('.navbar');
  let lastScroll = 0;
  
  window.addEventListener('scroll', () => {
    const currentScroll = window.pageYOffset;
    
    if (currentScroll > 50) {
      navbar.classList.add('scrolled');
    } else {
      navbar.classList.remove('scrolled');
    }
    
    lastScroll = currentScroll;
  });
}

// ====== MOBILE NAVIGATION ======
function initMobileNav() {
  const menuBtn = document.getElementById('navMenuBtn');
  const navLinks = document.getElementById('navLinks');
  
  menuBtn?.addEventListener('click', () => {
    navLinks.classList.toggle('active');
    menuBtn.setAttribute('aria-expanded', navLinks.classList.contains('active'));
  });
  
  // Close menu when clicking a link
  navLinks?.querySelectorAll('a').forEach(link => {
    link.addEventListener('click', () => {
      navLinks.classList.remove('active');
      menuBtn?.setAttribute('aria-expanded', 'false');
    });
  });
  
  // Close menu when clicking outside
  document.addEventListener('click', (e) => {
    if (!navLinks?.contains(e.target) && !menuBtn?.contains(e.target)) {
      navLinks?.classList.remove('active');
      menuBtn?.setAttribute('aria-expanded', 'false');
    }
  });
}

// ====== SCROLL SPY ======
function initScrollSpy() {
  const sections = document.querySelectorAll('section[id]');
  const navLinks = document.querySelectorAll('.nav-links a');
  
  const observerOptions = {
    root: null,
    rootMargin: '-20% 0px -80% 0px',
    threshold: 0
  };
  
  const observer = new IntersectionObserver((entries) => {
    entries.forEach(entry => {
      if (entry.isIntersecting) {
        const id = entry.target.getAttribute('id');
        navLinks.forEach(link => {
          link.classList.remove('active');
          if (link.getAttribute('href') === `#${id}`) {
            link.classList.add('active');
          }
        });
      }
    });
  }, observerOptions);
  
  sections.forEach(section => observer.observe(section));
}

// ====== SCROLL REVEAL ======
function initScrollReveal() {
  const revealElements = document.querySelectorAll('.reveal');
  
  const observerOptions = {
    root: null,
    threshold: 0.1,
    rootMargin: '0px 0px -50px 0px'
  };
  
  const observer = new IntersectionObserver((entries) => {
    entries.forEach((entry, index) => {
      if (entry.isIntersecting) {
        // Add stagger delay for grouped elements
        setTimeout(() => {
          entry.target.classList.add('active');
        }, index * 100);
      }
    });
  }, observerOptions);
  
  revealElements.forEach(el => observer.observe(el));
}

// ====== SMOOTH SCROLL ======
function initSmoothScroll() {
  document.querySelectorAll('a[href^="#"]').forEach(anchor => {
    anchor.addEventListener('click', function(e) {
      e.preventDefault();
      const targetId = this.getAttribute('href');
      const targetElement = document.querySelector(targetId);
      
      if (targetElement) {
        const navHeight = document.querySelector('.navbar')?.offsetHeight || 0;
        const targetPosition = targetElement.offsetTop - navHeight;
        
        window.scrollTo({
          top: targetPosition,
          behavior: 'smooth'
        });
      }
    });
  });
}

// ====== IFRAME LOADER ======
function initIframeLoader() {
  const iframes = document.querySelectorAll('.project-iframe');
  
  iframes.forEach(iframe => {
    // Add loading state
    const wrapper = iframe.closest('.project-iframe-wrapper');
    const placeholder = wrapper?.querySelector('.project-placeholder');
    
    iframe.addEventListener('load', () => {
      iframe.style.opacity = '1';
      if (placeholder) {
        placeholder.style.display = 'none';
      }
    });
    
    iframe.addEventListener('error', () => {
      if (placeholder) {
        placeholder.innerHTML = `
          <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
            <circle cx="12" cy="12" r="10"></circle>
            <line x1="12" y1="8" x2="12" y2="12"></line>
            <line x1="12" y1="16" x2="12.01" y2="16"></line>
          </svg>
          <span>Preview unavailable</span>
        `;
      }
    });
  });
}

// ====== FOOTER YEAR ======
function initYear() {
  const yearEl = document.getElementById('year');
  if (yearEl) {
    yearEl.textContent = new Date().getFullYear();
  }
}

// ====== PARALLAX EFFECT (Optional) ======
function initParallax() {
  const parallaxElements = document.querySelectorAll('[data-parallax]');
  
  window.addEventListener('scroll', () => {
    const scrollY = window.pageYOffset;
    
    parallaxElements.forEach(el => {
      const speed = parseFloat(el.dataset.parallax) || 0.5;
      el.style.transform = `translateY(${scrollY * speed}px)`;
    });
  });
}

// ====== TYPING EFFECT (Optional) ======
class TypeWriter {
  constructor(element, words, wait = 3000) {
    this.element = element;
    this.words = words;
    this.wait = parseInt(wait, 10);
    this.wordIndex = 0;
    this.txt = '';
    this.isDeleting = false;
    this.type();
  }
  
  type() {
    const current = this.wordIndex % this.words.length;
    const fullTxt = this.words[current];
    
    if (this.isDeleting) {
      this.txt = fullTxt.substring(0, this.txt.length - 1);
    } else {
      this.txt = fullTxt.substring(0, this.txt.length + 1);
    }
    
    this.element.innerHTML = `<span class="txt">${this.txt}</span>`;
    
    let typeSpeed = 100;
    
    if (this.isDeleting) {
      typeSpeed /= 2;
    }
    
    if (!this.isDeleting && this.txt === fullTxt) {
      typeSpeed = this.wait;
      this.isDeleting = true;
    } else if (this.isDeleting && this.txt === '') {
      this.isDeleting = false;
      this.wordIndex++;
      typeSpeed = 500;
    }
    
    setTimeout(() => this.type(), typeSpeed);
  }
}

// ====== CURSOR EFFECT (Optional) ======
function initCustomCursor() {
  const cursor = document.createElement('div');
  cursor.className = 'custom-cursor';
  document.body.appendChild(cursor);
  
  const cursorDot = document.createElement('div');
  cursorDot.className = 'cursor-dot';
  document.body.appendChild(cursorDot);
  
  document.addEventListener('mousemove', (e) => {
    cursor.style.left = e.clientX + 'px';
    cursor.style.top = e.clientY + 'px';
    cursorDot.style.left = e.clientX + 'px';
    cursorDot.style.top = e.clientY + 'px';
  });
  
  // Add hover effect on interactive elements
  const interactiveElements = document.querySelectorAll('a, button, .project-card');
  interactiveElements.forEach(el => {
    el.addEventListener('mouseenter', () => {
      cursor.classList.add('hover');
    });
    el.addEventListener('mouseleave', () => {
      cursor.classList.remove('hover');
    });
  });
}
