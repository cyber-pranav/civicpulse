/**
 * @module AnalyticsModule
 * @description Google Analytics 4 event tracking
 */
var AnalyticsModule = (function() {
  // ─── Private state ───────────────────────────
  var _isInitialized = false;

  // ─── Private helpers ─────────────────────────
  /**
   * @description Inject GA4 script tag into head
   * @returns {void}
   */
  var _injectScript = function() {
    var s = document.createElement('script');
    s.id = 'ga4-script'; s.async = true;
    s.src = 'https://www.googletagmanager.com/gtag/js?id=' + CONFIG.GA_MEASUREMENT_ID;
    document.head.appendChild(s);
  };

  /**
   * @description Configure gtag dataLayer
   * @returns {void}
   */
  var _configureGtag = function() {
    window.dataLayer = window.dataLayer || [];
    window.gtag = function() { window.dataLayer.push(arguments); };
    window.gtag('js', new Date());
    window.gtag('config', CONFIG.GA_MEASUREMENT_ID, { send_page_view: true });
  };

  // ─── Public API ──────────────────────────────
  /**
   * @description Initialize GA4
   * @returns {void}
   */
  var init = function() {
    if (_isInitialized) return;
    if (document.getElementById('ga4-script')) return;
    _injectScript();
    _configureGtag();
    _isInitialized = true;
  };

  /**
   * @description Track a custom event
   * @param {string} name - Event name
   * @param {Object} params - Event parameters
   * @returns {void}
   */
  var track = function(name, params) {
    if (window.gtag) window.gtag('event', name, params || {});
  };

  /**
   * @description Alias for track
   * @param {string} name - Event name
   * @param {Object} params - Event parameters
   * @returns {void}
   */
  var trackEvent = function(name, params) { track(name, params); };

  /**
   * @description Cleans up module
   * @returns {void}
   */
  var destroy = function() { _isInitialized = false; };

  return { init: init, destroy: destroy, track: track, trackEvent: trackEvent };
})();

/**
 * @module TranslateModule
 * @description Google Translate API integration for multilingual UI
 */
var TranslateModule = (function() {
  // ─── Private state ───────────────────────────
  var _isInitialized = false;
  var _currentLang = CONSTANTS.DEFAULT_LANGUAGE;
  var _originalTexts = new Map();

  // ─── Private helpers ─────────────────────────
  /**
   * @description Collect translatable text nodes
   * @returns {Object} { texts: string[], elements: Element[] }
   */
  var _collectTexts = function() {
    var els = document.querySelectorAll('h1,h2,h3,p,span,a,button,label,li');
    var texts = [], elements = [];
    els.forEach(function(el) {
      if (el.closest('.cp-chat-drawer') || el.closest('#candidate-compare')) return;
      if (el.children.length > 0 && el.tagName !== 'BUTTON' && el.tagName !== 'A') return;
      var t = el.textContent.trim();
      if (t && t.length > 1 && t.length < 500) {
        if (!_originalTexts.has(el)) _originalTexts.set(el, t);
        texts.push(t); elements.push(el);
      }
    });
    return { texts: texts, elements: elements };
  };

  /**
   * @description Send a batch to Translate API
   * @param {string[]} batch - Texts to translate
   * @param {string} lang - Target language
   * @returns {Promise<string[]>} Translated texts
   */
  var _translateBatch = async function(batch, lang) {
    try {
      var body = { q: batch, target: lang, source: CONSTANTS.DEFAULT_LANGUAGE, format: 'text' };
      var resp = await fetch(CONFIG.TRANSLATE_URL + '?key=' + CONFIG.TRANSLATE_API_KEY, {
        method: 'POST', headers: { 'Content-Type': 'application/json' }, body: JSON.stringify(body)
      });
      if (!resp.ok) throw new Error('Translate API error');
      var data = await resp.json();
      var tr = data.data && data.data.translations ? data.data.translations : [];
      return tr.map(function(t) { return t.translatedText; });
    } catch (e) {
      Logger.error('TranslateModule._translateBatch failed:', e.message);
      return batch;
    }
  };

  /**
   * @description Restore original English text
   * @returns {void}
   */
  var _restoreEnglish = function() {
    _originalTexts.forEach(function(text, el) { el.textContent = text; });
    _currentLang = CONSTANTS.DEFAULT_LANGUAGE;
    localStorage.setItem('cp_lang', CONSTANTS.DEFAULT_LANGUAGE);
    document.documentElement.setAttribute('lang', CONSTANTS.DEFAULT_LANGUAGE);
  };

  // ─── Public API ──────────────────────────────
  /**
   * @description Initializes the module
   * @returns {void}
   */
  var init = function() {
    if (_isInitialized) return;
    _isInitialized = true;
    var saved = localStorage.getItem('cp_lang');
    if (saved && saved !== CONSTANTS.DEFAULT_LANGUAGE) {
      _currentLang = saved;
      setTimeout(function() { translatePage(saved); }, 500);
    }
  };

  /**
   * @description Translate page to target language
   * @param {string} lang - Target language code
   * @returns {Promise<void>}
   */
  var translatePage = async function(lang) {
    if (!Validator.isValidLanguageCode(lang)) return;
    if (lang === CONSTANTS.DEFAULT_LANGUAGE) { _restoreEnglish(); announce('Language changed to English'); return; }
    var collected = _collectTexts();
    if (collected.texts.length === 0) return;
    try {
      for (var i = 0; i < collected.texts.length; i += CONSTANTS.TRANSLATE_BATCH_SIZE) {
        var batch = collected.texts.slice(i, i + CONSTANTS.TRANSLATE_BATCH_SIZE);
        var batchEls = collected.elements.slice(i, i + CONSTANTS.TRANSLATE_BATCH_SIZE);
        var translated = await _translateBatch(batch, lang);
        translated.forEach(function(t, idx) { if (batchEls[idx]) batchEls[idx].textContent = t; });
      }
      _currentLang = lang;
      localStorage.setItem('cp_lang', lang);
      document.documentElement.setAttribute('lang', lang);
      AnalyticsModule.track('language_changed', { language: lang });
      announce('Language changed to ' + lang);
    } catch (e) {
      Logger.error('TranslateModule.translatePage failed:', e.message);
      showToast('Translation service unavailable', 'error');
    }
  };

  /** @returns {Array} Available languages */
  var getLanguages = function() { return [
    { code: 'en', label: 'English' }, { code: 'hi', label: '\u0939\u093F\u0928\u094D\u0926\u0940 (Hindi)' },
    { code: 'bn', label: '\u09AC\u09BE\u0982\u09B2\u09BE (Bengali)' }, { code: 'ta', label: '\u0BA4\u0BAE\u0BBF\u0BB4\u0BCD (Tamil)' },
    { code: 'te', label: '\u0C24\u0C46\u0C32\u0C41\u0C17\u0C41 (Telugu)' }, { code: 'mr', label: '\u092E\u0930\u093E\u0920\u0940 (Marathi)' },
    { code: 'pa', label: '\u0A2A\u0A70\u0A1C\u0A3E\u0A2C\u0A40 (Punjabi)' }
  ]; };
  /** @returns {string} Current language code */
  var getCurrent = function() { return _currentLang; };
  /** @returns {void} */
  var destroy = function() { _isInitialized = false; _originalTexts.clear(); };

  return { init: init, destroy: destroy, getLanguages: getLanguages, getCurrent: getCurrent, translatePage: translatePage };
})();

/**
 * @module AuthModule
 * @description Firebase Auth + Firestore progress sync
 */
var AuthModule = (function() {
  var _isInitialized = false;
  var _user = null;
  var _db = null;
  var _accessToken = null;

  /**
   * @description Load progress from localStorage
   * @returns {Object|null}
   */
  var _loadLocal = function() {
    try { var d = localStorage.getItem('cp_progress'); return d ? JSON.parse(d) : null; }
    catch (e) { return null; }
  };

  /**
   * @description Save progress to localStorage
   * @param {Object} data
   * @returns {void}
   */
  var _saveLocal = function(data) {
    try { localStorage.setItem('cp_progress', JSON.stringify(data)); } catch (e) {}
  };

  /**
   * @description Initialize Firebase Auth
   * @param {Function} onAuthChange - Callback
   * @returns {void}
   */
  var init = function(onAuthChange) {
    if (_isInitialized) return;
    _isInitialized = true;
    try {
      if (typeof firebase === 'undefined') { Logger.warn('Firebase not loaded'); return; }
      if (!firebase.apps.length) firebase.initializeApp(CONFIG.FIREBASE_CONFIG);
      _db = firebase.firestore();
      firebase.auth().onAuthStateChanged(function(u) {
        _user = u;
        if (onAuthChange) onAuthChange(u);
        if (u) loadProgress();
      });
    } catch (e) { Logger.error('AuthModule.init failed:', e.message); }
  };

  /**
   * @description Sign in with Google + calendar scopes
   * @returns {Promise<void>}
   */
  var signIn = async function() {
    try {
      var provider = new firebase.auth.GoogleAuthProvider();
      provider.addScope(CONSTANTS.CALENDAR_SCOPES);
      var result = await firebase.auth().signInWithPopup(provider);
      if (result.credential) _accessToken = result.credential.accessToken;
      announce('Signed in as ' + (result.user.displayName || 'User'));
    } catch (e) {
      Logger.error('AuthModule.signIn failed:', e.message);
      showToast('Sign-in failed. Please try again.', 'error');
    }
  };

  /**
   * @description Sign out
   * @returns {Promise<void>}
   */
  var signOut = async function() {
    try { await firebase.auth().signOut(); _accessToken = null; announce('Signed out'); }
    catch (e) { Logger.error('AuthModule.signOut failed:', e.message); showToast('Sign-out failed', 'error'); }
  };

  /** @returns {Object|null} */
  var getUser = function() { return _user; };
  /** @returns {string|null} */
  var getAccessToken = function() { return _accessToken; };

  /**
   * @description Load progress from Firestore
   * @returns {Promise<Object|null>}
   */
  var loadProgress = async function() {
    if (!_user || !_db) return _loadLocal();
    try {
      var doc = await _db.collection(CONSTANTS.FIRESTORE_COLLECTION).doc(_user.uid).get();
      if (doc.exists) return doc.data();
      return _loadLocal();
    } catch (e) {
      Logger.error('AuthModule.loadProgress failed:', e.message);
      return _loadLocal();
    }
  };

  /**
   * @description Save progress to Firestore
   * @param {Object} data
   * @returns {Promise<void>}
   */
  var saveProgress = async function(data) {
    _saveLocal(data);
    if (!_user || !_db) return;
    try {
      await _db.collection(CONSTANTS.FIRESTORE_COLLECTION).doc(_user.uid).set(data, { merge: true });
    } catch (e) { Logger.error('AuthModule.saveProgress failed:', e.message); }
  };

  var destroy = function() { _isInitialized = false; _user = null; _db = null; _accessToken = null; };

  return { init: init, destroy: destroy, signIn: signIn, signOut: signOut, getUser: getUser,
           getAccessToken: getAccessToken, loadProgress: loadProgress, saveProgress: saveProgress };
})();

/**
 * @module RealtimeModule
 * @description Firebase Realtime Database for live civic activity counters
 */
var RealtimeModule = (function() {
  var _isInitialized = false;
  var _rtdb = null;
  var _counters = { evmCompleted: 0, calendarAdded: 0, activeJourneys: 0 };
  var _listeners = [];

  /**
   * @description Listen to a counter path
   * @param {string} key - Counter key
   * @returns {void}
   */
  var _listen = function(key) {
    if (!_rtdb) return;
    _rtdb.ref(CONSTANTS.REALTIME_DB_PATH + '/' + key).on('value', function(snap) {
      _counters[key] = snap.val() || 0;
      _listeners.forEach(function(fn) { fn(_counters); });
    });
  };

  var init = function() {
    if (_isInitialized) return;
    _isInitialized = true;
    try {
      if (typeof firebase === 'undefined' || !firebase.database) return;
      _rtdb = firebase.database();
      _listen('evmCompleted'); _listen('calendarAdded'); _listen('activeJourneys');
    } catch (e) { Logger.error('RealtimeModule.init failed:', e.message); }
  };

  /**
   * @description Increment a counter
   * @param {string} key
   * @returns {void}
   */
  var increment = function(key) {
    if (!_rtdb) return;
    _rtdb.ref(CONSTANTS.REALTIME_DB_PATH + '/' + key).transaction(function(c) { return (c || 0) + 1; });
  };

  /** @returns {Object} */
  var getCounters = function() { return _counters; };
  /**
   * @param {Function} fn - Listener
   * @returns {void}
   */
  var onChange = function(fn) { _listeners.push(fn); };
  var destroy = function() { _isInitialized = false; _rtdb = null; _listeners = []; };

  return { init: init, destroy: destroy, increment: increment, getCounters: getCounters, onChange: onChange };
})();

/**
 * @module CalendarModule
 * @description Google Calendar API deep integration
 */
var CalendarModule = (function() {
  var _isInitialized = false;

  /**
   * @description Open fallback calendar URL link
   * @returns {void}
   */
  var _fallbackLink = function() {
    var url = 'https://www.google.com/calendar/render?action=TEMPLATE' +
      '&text=' + encodeURIComponent(CONSTANTS.COUNTING_DAY_LABEL) +
      '&dates=20260504T023000Z/20260504T123000Z' +
      '&details=' + encodeURIComponent('Counting Day for Indian Elections') +
      '&sf=true&output=xml';
    window.open(url, '_blank');
  };

  /**
   * @description Build the calendar event object
   * @param {Object} opts - { boothAddress, candidateNames }
   * @returns {Object} event
   */
  var _buildEvent = function(opts) {
    return {
      summary: CONSTANTS.COUNTING_DAY_LABEL,
      description: 'Counting Day for Indian Elections.\n' +
        (opts.boothAddress ? 'Booth: ' + opts.boothAddress + '\n' : '') +
        (opts.candidateNames ? 'Candidates: ' + opts.candidateNames : ''),
      start: { dateTime: CONSTANTS.COUNTING_DAY_DATE + 'T08:00:00+05:30', timeZone: 'Asia/Kolkata' },
      end: { dateTime: CONSTANTS.COUNTING_DAY_DATE + 'T18:00:00+05:30', timeZone: 'Asia/Kolkata' },
      reminders: { useDefault: false, overrides: [{ method: 'popup', minutes: 1440 }, { method: 'popup', minutes: 60 }] },
      colorId: CONSTANTS.GOOGLE_CALENDAR_COLOR_ID
    };
  };

  /**
   * @description Add Counting Day event via API
   * @param {Object} opts
   * @returns {Promise<boolean>}
   */
  var addCountingDayEvent = async function(opts) {
    opts = opts || {};
    var token = AuthModule.getAccessToken();
    if (!token) { _fallbackLink(); return false; }
    try {
      var resp = await fetch(CONSTANTS.CALENDAR_API_URL, {
        method: 'POST',
        headers: { 'Authorization': 'Bearer ' + token, 'Content-Type': 'application/json' },
        body: JSON.stringify(_buildEvent(opts))
      });
      if (!resp.ok) throw new Error('Calendar API ' + resp.status);
      showToast('Added to your Google Calendar', 'success');
      RealtimeModule.increment('calendarAdded');
      AnalyticsModule.track('calendar_event_created_api');
      return true;
    } catch (e) {
      Logger.error('CalendarModule.addCountingDayEvent failed:', e.message);
      _fallbackLink();
      return false;
    }
  };

  var init = function() { _isInitialized = true; };
  var destroy = function() { _isInitialized = false; };

  return { init: init, destroy: destroy, addCountingDayEvent: addCountingDayEvent };
})();

/**
 * @module SentimentModule
 * @description Google Cloud Natural Language API sentiment analysis
 */
var SentimentModule = (function() {
  var _isInitialized = false;

  /**
   * @description Extract manifesto text from candidate
   * @param {Object} cand
   * @returns {string}
   */
  var _getManifestoText = function(cand) {
    if (cand.manifesto && Array.isArray(cand.manifesto)) return cand.manifesto.join('. ');
    if (cand.manifesto_points && Array.isArray(cand.manifesto_points)) return cand.manifesto_points.join('. ');
    if (typeof cand.manifesto === 'string') return cand.manifesto;
    return (cand.name || '') + ' ' + (cand.party || '');
  };

  /**
   * @description Analyze sentiment of text
   * @param {string} text
   * @returns {Promise<Object>} { score, magnitude }
   */
  var analyzeSentiment = async function(text) {
    if (!Validator.isNonEmptyString(text) || text.trim().length < 10) return { score: 0, magnitude: 0 };
    try {
      var body = { document: { type: 'PLAIN_TEXT', content: text }, encodingType: 'UTF8' };
      var resp = await fetch(CONSTANTS.NL_API_URL + '?key=' + CONFIG.NL_API_KEY, {
        method: 'POST', headers: { 'Content-Type': 'application/json' }, body: JSON.stringify(body)
      });
      if (!resp.ok) throw new Error('NL API ' + resp.status);
      var data = await resp.json();
      if (!data.documentSentiment) throw new Error('Empty NL response');
      return { score: data.documentSentiment.score, magnitude: data.documentSentiment.magnitude };
    } catch (e) {
      Logger.error('SentimentModule.analyzeSentiment failed:', e.message);
      return { score: 0, magnitude: 0 };
    }
  };

  /**
   * @description Analyze all candidates' manifestos
   * @param {Array} candidates
   * @returns {Promise<Array>}
   */
  var analyzeManifestos = async function(candidates) {
    var results = [];
    for (var i = 0; i < candidates.length; i++) {
      var s = await analyzeSentiment(_getManifestoText(candidates[i]));
      results.push({ name: candidates[i].name, score: s.score, magnitude: s.magnitude });
    }
    AnalyticsModule.track('sentiment_analysis_completed', { candidate_count: results.length });
    return results;
  };

  var init = function() { _isInitialized = true; };
  var destroy = function() { _isInitialized = false; };

  return { init: init, destroy: destroy, analyzeSentiment: analyzeSentiment, analyzeManifestos: analyzeManifestos };
})();

/**
 * @module AIModule
 * @description Gemini AI chat, candidate analysis, NL search
 */
var AIModule = (function() {
  var _isInitialized = false;
  var _messages = [];
  var _isOpen = false;
  var _isTyping = false;
  var _timestamps = [];
  var _SYSTEM_PROMPT = "You are CivicPulse AI, an expert on Indian elections. Answer only civic/election questions.";

  /**
   * @description Check rate limit
   * @returns {boolean}
   */
  var _checkRateLimit = function() {
    var now = Date.now();
    _timestamps = _timestamps.filter(function(t) { return now - t < CONSTANTS.RATE_LIMIT_WINDOW_MS; });
    if (_timestamps.length >= CONSTANTS.RATE_LIMIT_MAX) {
      showToast('Please wait before sending another message', 'info');
      return false;
    }
    _timestamps.push(now);
    return true;
  };

  /**
   * @description Call Gemini API with prompt
   * @param {string} prompt
   * @returns {Promise<string>} Response text
   */
  var _callGemini = async function(prompt) {
    var resp = await fetch(CONFIG.GEMINI_URL + '?key=' + CONFIG.GEMINI_API_KEY, {
      method: 'POST', headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({
        contents: [{ role: 'user', parts: [{ text: prompt }] }],
        generationConfig: { maxOutputTokens: CONSTANTS.GEMINI_MAX_TOKENS }
      })
    });
    if (!resp.ok) throw new Error('Gemini API ' + resp.status);
    var data = await resp.json();
    return (data.candidates && data.candidates[0] && data.candidates[0].content)
      ? data.candidates[0].content.parts[0].text : '';
  };

  /**
   * @description Extract manifesto text from candidate
   * @param {Object} c
   * @returns {string}
   */
  var _getManifesto = function(c) {
    if (c.manifesto && Array.isArray(c.manifesto)) return c.manifesto.join(', ');
    if (c.manifesto_points && Array.isArray(c.manifesto_points)) return c.manifesto_points.join(', ');
    if (typeof c.manifesto === 'string') return c.manifesto;
    return c.name + ' of ' + c.party;
  };

  var init = function() { if (_isInitialized) return; _isInitialized = true; };

  /**
   * @description Send chat message to Gemini
   * @param {string} text
   * @returns {Promise<string|null>}
   */
  var sendMessage = async function(text) {
    if (!Validator.isNonEmptyString(text)) return null;
    if (!_checkRateLimit()) return null;
    var sanitized = sanitizeHTML(text.trim());
    _messages.push({ role: 'user', text: sanitized });
    _isTyping = true;
    try {
      var reply = await _callGemini(_SYSTEM_PROMPT + '\n\nUser: ' + sanitized);
      if (!reply) throw new Error('Empty Gemini response');
      _messages.push({ role: 'ai', text: reply });
      _isTyping = false;
      AnalyticsModule.track('ai_message_sent');
      return reply;
    } catch (e) {
      _isTyping = false;
      Logger.error('AIModule.sendMessage failed:', e.message);
      var errMsg = 'I am having trouble connecting. Please try again.';
      _messages.push({ role: 'ai', text: errMsg });
      showToast('AI assistant temporarily unavailable', 'error');
      return errMsg;
    }
  };

  /**
   * @description Analyze candidate manifesto for AI Insight
   * @param {Object} candidate
   * @returns {Promise<Object>}
   */
  var analyzeCandidate = async function(candidate) {
    var prompt = 'Analyze this election candidate\'s manifesto points: ' + _getManifesto(candidate) +
      '. Return a JSON object with fields: tone (Positive/Neutral/Critical), topTopics (3 strings), voterAppeal (1 sentence), redFlags (array or empty).';
    try {
      var text = await _callGemini(prompt);
      if (!text) throw new Error('Empty response');
      var match = text.match(/\{[\s\S]*\}/);
      if (match) {
        var p = JSON.parse(match[0]);
        return { tone: p.tone || 'Neutral', topTopics: p.topTopics || [], voterAppeal: p.voterAppeal || '', redFlags: p.redFlags || [] };
      }
      return { tone: 'Neutral', topTopics: [], voterAppeal: '', redFlags: [] };
    } catch (e) {
      Logger.error('AIModule.analyzeCandidate failed:', e.message);
      return { tone: 'Neutral', topTopics: [], voterAppeal: 'Analysis unavailable', redFlags: [] };
    }
  };

  /**
   * @description NL search for candidates
   * @param {string} query
   * @param {Array} candidates
   * @returns {Promise<Array>}
   */
  var searchCandidates = async function(query, candidates) {
    if (!Validator.isNonEmptyString(query) || !candidates.length) return candidates.map(function(_, i) { return i; });
    var list = candidates.map(function(c, i) { return { id: i, name: c.name, party: c.party }; });
    var prompt = "Given query: '" + sanitizeHTML(query) + "', candidates: " + JSON.stringify(list) + ". Return JSON array of matching IDs only.";
    try {
      var text = await _callGemini(prompt);
      if (!text) throw new Error('Empty response');
      var match = text.match(/\[[\s\S]*?\]/);
      return match ? JSON.parse(match[0]) : candidates.map(function(_, i) { return i; });
    } catch (e) {
      Logger.error('AIModule.searchCandidates failed:', e.message);
      return candidates.map(function(_, i) { return i; });
    }
  };

  var clearChat = function() { _messages = []; };
  var getMessages = function() { return _messages; };
  var getIsTyping = function() { return _isTyping; };
  var getIsOpen = function() { return _isOpen; };
  var setIsOpen = function(v) { _isOpen = v; };
  var checkRateLimit = function() { return _checkRateLimit(); };
  var getTimestamps = function() { return _timestamps; };
  var setTimestamps = function(t) { _timestamps = t; };
  var destroy = function() { _isInitialized = false; _messages = []; _isOpen = false; _isTyping = false; _timestamps = []; };

  return { init: init, destroy: destroy, sendMessage: sendMessage, analyzeCandidate: analyzeCandidate,
    searchCandidates: searchCandidates, clearChat: clearChat, getMessages: getMessages,
    getIsTyping: getIsTyping, getIsOpen: getIsOpen, setIsOpen: setIsOpen,
    checkRateLimit: checkRateLimit, getTimestamps: getTimestamps, setTimestamps: setTimestamps };
})();
