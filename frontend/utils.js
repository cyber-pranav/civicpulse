/** @module Utils */
/** @description Shared utilities, config, logging, validation, accessibility helpers */

// ─── Configuration ─────────────────────────────
/** @type {Object} Application configuration */
var CONFIG = {
  GEMINI_API_KEY: 'AIzaSyBfakeKeyPlaceholder',
  GEMINI_URL: 'https://generativelanguage.googleapis.com/v1beta/models/' + CONSTANTS.GEMINI_MODEL + ':generateContent',
  TRANSLATE_API_KEY: 'AIzaSyBfakeKeyPlaceholder',
  TRANSLATE_URL: 'https://translation.googleapis.com/language/translate/v2',
  NL_API_KEY: 'AIzaSyBfakeKeyPlaceholder',
  FIREBASE_CONFIG: {
    apiKey: "AIzaSyBfakeKeyPlaceholder",
    authDomain: "civicpulse-app.firebaseapp.com",
    projectId: "civicpulse-app",
    storageBucket: "civicpulse-app.appspot.com",
    messagingSenderId: "123456789",
    appId: "1:123456789:web:abcdef",
    measurementId: "G-XXXXXXXXXX",
    databaseURL: "https://civicpulse-app-default-rtdb.firebaseio.com"
  },
  GA_MEASUREMENT_ID: 'G-XXXXXXXXXX',
  MAPS_API_KEY: 'AIzaSyBfakeKeyPlaceholder',
  RATE_LIMIT_MAX: CONSTANTS.RATE_LIMIT_MAX,
  RATE_LIMIT_WINDOW: CONSTANTS.RATE_LIMIT_WINDOW_MS
};

/** @type {boolean} Debug mode flag */
var DEBUG = window.location.search.indexOf('debug=true') !== -1;

// ─── Logger ────────────────────────────────────
/**
 * @description Logger utility — silent unless ?debug=true
 * @type {Object}
 */
var Logger = {
  /** @param {...*} args @returns {void} */
  log: function() { if (DEBUG) console.log.apply(console, arguments); },
  /** @param {...*} args @returns {void} */
  debug: function() { if (DEBUG) console.debug.apply(console, arguments); },
  /** @param {...*} args @returns {void} */
  warn: function() { if (DEBUG) console.warn.apply(console, arguments); },
  /** @param {...*} args @returns {void} */
  error: function() { if (DEBUG) console.error.apply(console, arguments); }
};

// ─── C5: Input Validation Layer ────────────────
/**
 * @description Input validation utility
 * @type {Object}
 */
var Validator = {
  /**
   * @description Check if age is valid integer 1–120
   * @param {number} age - Age value
   * @returns {boolean} validity
   */
  isValidAge: function(age) {
    return Number.isInteger(age) && age >= 1 && age <= 120;
  },
  /**
   * @description Check if state/location is valid
   * @param {string} state - State string
   * @returns {boolean} validity
   */
  isValidState: function(state) {
    return typeof state === 'string' && state.trim().length > 0;
  },
  /**
   * @description Check non-empty string
   * @param {string} str - Input string
   * @returns {boolean} validity
   */
  isNonEmptyString: function(str) {
    return typeof str === 'string' && str.trim().length > 0;
  },
  /**
   * @description Check valid language code
   * @param {string} code - Language code
   * @returns {boolean} validity
   */
  isValidLanguageCode: function(code) {
    return CONSTANTS.SUPPORTED_LANGUAGES.indexOf(code) !== -1;
  },
  /**
   * @description Sanitize age input to safe range
   * @param {*} input - Raw input
   * @returns {number} sanitized age
   */
  sanitizeAge: function(input) {
    return Math.min(120, Math.max(1, parseInt(input, 10) || 18));
  }
};

// ─── D1: Focus Manager ─────────────────────────
/**
 * @description Manages focus trapping for modals/drawers
 * @type {Object}
 */
var FocusManager = {
  /** @type {Function|null} */
  _trapped: null,
  /**
   * @description Trap focus within a container
   * @param {HTMLElement} containerEl - Container element
   * @returns {void}
   */
  trap: function(containerEl) {
    var sel = 'button, [href], input, select, textarea, [tabindex]:not([tabindex="-1"])';
    var focusable = containerEl.querySelectorAll(sel);
    var first = focusable[0];
    var last = focusable[focusable.length - 1];
    FocusManager._trapped = function(e) {
      if (e.key !== 'Tab') return;
      if (e.shiftKey) {
        if (document.activeElement === first) { e.preventDefault(); last.focus(); }
      } else {
        if (document.activeElement === last) { e.preventDefault(); first.focus(); }
      }
    };
    containerEl.addEventListener('keydown', FocusManager._trapped);
    if (first) first.focus();
  },
  /**
   * @description Release focus trap from a container
   * @param {HTMLElement} containerEl - Container element
   * @returns {void}
   */
  release: function(containerEl) {
    if (FocusManager._trapped) {
      containerEl.removeEventListener('keydown', FocusManager._trapped);
    }
    FocusManager._trapped = null;
  }
};

// ─── D2: Live Region Announcements ─────────────
/**
 * @description Announce a message to screen readers
 * @param {string} message - Text to announce
 * @param {string} priority - 'polite' or 'assertive'
 * @returns {void}
 */
function announce(message, priority) {
  priority = priority || 'polite';
  var id = priority === 'assertive' ? 'sr-assertive' : 'sr-announcer';
  var el = document.getElementById(id);
  if (!el) return;
  el.textContent = '';
  requestAnimationFrame(function() { el.textContent = message; });
}

// ─── Core Utilities ────────────────────────────
/**
 * @description Debounce a function call
 * @param {Function} fn - Function to debounce
 * @param {number} delay - Delay in milliseconds
 * @returns {Function} Debounced function
 */
function debounce(fn, delay) {
  var timer = null;
  return function() {
    var ctx = this, args = arguments;
    clearTimeout(timer);
    timer = setTimeout(function() { fn.apply(ctx, args); }, delay);
  };
}

/**
 * @description Sanitize HTML to prevent XSS attacks
 * @param {string} str - Raw HTML string
 * @returns {string} Sanitized string
 */
function sanitizeHTML(str) {
  if (!str) return '';
  return String(str)
    .replace(/<script[\s\S]*?<\/script>/gi, '')
    .replace(/<iframe[\s\S]*?<\/iframe>/gi, '')
    .replace(/on\w+\s*=\s*["'][^"']*["']/gi, '')
    .replace(/on\w+\s*=\s*\S+/gi, '')
    .replace(/javascript\s*:/gi, '');
}

/**
 * @description Format a date string for Indian locale
 * @param {string|Date} d - Date to format
 * @returns {string} Formatted date
 */
function formatDate(d) {
  try {
    var dt = new Date(d);
    return dt.toLocaleDateString('en-IN', { year: 'numeric', month: 'long', day: 'numeric' });
  } catch (e) { return String(d); }
}

/**
 * @description Remove existing toasts from DOM
 * @returns {void}
 */
function _clearExistingToasts() {
  var existing = document.querySelectorAll('.cp-toast');
  existing.forEach(function(el) { el.remove(); });
}

/**
 * @description Show a toast notification
 * @param {string} message - Toast message
 * @param {string} type - 'error' | 'success' | 'info'
 * @returns {void}
 */
function showToast(message, type) {
  type = type || 'info';
  _clearExistingToasts();
  var toast = document.createElement('div');
  toast.className = 'cp-toast cp-toast-' + type;
  toast.setAttribute('role', 'alert');
  toast.textContent = message;
  document.body.appendChild(toast);
  announce(message, 'polite');
  setTimeout(function() { toast.classList.add('cp-toast-show'); }, 10);
  setTimeout(function() {
    toast.classList.remove('cp-toast-show');
    setTimeout(function() { toast.remove(); }, CONSTANTS.SKELETON_DELAY_MS);
  }, CONSTANTS.TOAST_DURATION_MS);
}

// ─── API Fetch ─────────────────────────────────
/**
 * @description Try cache for GET request
 * @param {string} cacheKey - Cache key
 * @returns {*|null} Cached data or null
 */
function _tryGetCache(cacheKey) {
  try {
    var cached = sessionStorage.getItem(cacheKey);
    if (cached) { Logger.log('Cache hit'); return JSON.parse(cached); }
  } catch (e) { /* unavailable */ }
  return null;
}

/**
 * @description Store response in sessionStorage
 * @param {string} cacheKey - Cache key
 * @param {*} data - Data to cache
 * @returns {void}
 */
function _storeCache(cacheKey, data) {
  try { sessionStorage.setItem(cacheKey, JSON.stringify(data)); }
  catch (e) { /* full */ }
}

/**
 * @description Parse fetch response by content type
 * @param {Response} resp - Fetch response
 * @returns {Promise<*>} Parsed data
 */
async function _parseResponse(resp) {
  var ct = resp.headers.get('content-type') || '';
  if (ct.includes('application/json')) return resp.json();
  if (ct.includes('text/calendar')) return resp.blob();
  return resp.text();
}

/**
 * @description Fetch wrapper with caching and retry
 * @param {string} url - URL to fetch
 * @param {Object} options - Fetch options
 * @returns {Promise<*>} Response data
 */
async function apiFetch(url, options) {
  options = options || {};
  var method = (options.method || 'GET').toUpperCase();
  var cacheKey = 'apicache_' + url + (options.body || '');
  if (method === 'GET') {
    var cached = _tryGetCache(cacheKey);
    if (cached) return cached;
  }
  var attempts = 0;
  while (attempts <= CONSTANTS.API_RETRY_MAX) {
    try {
      var resp = await fetch(url, options);
      if (!resp.ok) throw new Error('HTTP ' + resp.status);
      var data = await _parseResponse(resp);
      if (method === 'GET') _storeCache(cacheKey, data);
      return data;
    } catch (err) {
      attempts++;
      if (attempts > CONSTANTS.API_RETRY_MAX) {
        Logger.error('apiFetch failed:', url, err.message);
        throw err;
      }
      await new Promise(function(r) { setTimeout(r, CONSTANTS.API_RETRY_DELAY_MS); });
    }
  }
}

// ─── Service Worker Registration ───────────────
if ('serviceWorker' in navigator) {
  window.addEventListener('load', function() {
    navigator.serviceWorker.register('/sw.js').then(function() {
      Logger.log('SW registered');
    }).catch(function(e) { Logger.warn('SW registration failed', e); });
  });
}

// ─── B2: Performance Monitoring ────────────────
window.addEventListener('load', function() {
  var nav = performance.getEntriesByType('navigation')[0];
  var paint = performance.getEntriesByName('first-contentful-paint')[0];
  Logger.debug('Page load time:', nav.loadEventEnd - nav.startTime, 'ms');
  Logger.debug('FCP:', paint ? paint.startTime : 0, 'ms');
  if (nav.loadEventEnd - nav.startTime > CONSTANTS.SLOW_LOAD_THRESHOLD_MS) {
    Logger.warn('Slow load detected — check network tab');
  }
  AnalyticsModule.trackEvent('performance_measured', {
    load_time_ms: Math.round(nav.loadEventEnd - nav.startTime),
    fcp_ms: Math.round(paint ? paint.startTime : 0)
  });
});

// ─── D4: Restore high-contrast on load ─────────
window.addEventListener('DOMContentLoaded', function() {
  if (localStorage.getItem('hc-mode') === 'true') {
    document.body.classList.add('high-contrast');
  }
});
