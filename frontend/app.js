/** @module CivicPulseApp */
/** @description Main Alpine.js application for CivicPulse */
var API = '';
var _tabRendered = { journey: true, evm: false, candidates: false, resources: false };

/**
 * @description Main Alpine.js component
 * @returns {Object} Alpine data object
 */
function civicPulse() {
  return {
    tab: 'journey', sessionId: null, state: 'UNINITIALIZED', path: null,
    simpleMode: false, loading: false, message: '',
    age: null, dob: '', location: '', isFirstTime: false,
    candidates: [], constituency: '', checklist: [], calendarLinks: [],
    pollingInfo: null, directionsUrl: '', boothAddress: '',
    evmVoted: false, vvpatVisible: false, vvpatCandidate: null, vvpatTimer: 0,
    selectedEVMCandidate: null, evmFocusIndex: -1,
    highContrast: false, voiceAssist: false,
    civicTips: [], registrationSteps: [], deadlines: {},
    showOnboarding: true, urgentWB: false,
    countingDay: '04 May 2026', candidatesLoaded: false,
    // Auth state
    authUser: null, authPhotoURL: '', authDisplayName: '',
    // AI chat state
    aiOpen: false, aiInput: '', aiMessages: [], aiTyping: false,
    // Translate state
    selectedLang: CONSTANTS.DEFAULT_LANGUAGE, languages: [],
    // Maps
    mapsMode: 'driving', showMapsEmbed: false, mapsEmbedUrl: '',
    // Skeleton
    showSkeleton: false,
    // A1: AI Insights per candidate
    candidateInsights: {},
    candidateInsightsLoading: {},
    // A2: Natural Language Search
    candidateSearchQuery: '',
    candidateSearchResults: null,
    allCandidates: [],
    // A3: Sentiment Analysis
    sentimentScores: [],
    sentimentLoading: false,
    // A4: Live Civic Activity
    civicActivity: { evmCompleted: 0, calendarAdded: 0, activeJourneys: 0 },
    // A5: Calendar API
    calendarAdding: false,
    // Candidates loading state
    candidatesLoading: false,
    candidatesLoadingMsg: '',
    candidatesFallback: false,

    jargonMap: {
      'constituency':'your voting area','electoral roll':'the official voter list',
      'EPIC number':'Voter ID number','EPIC':'Voter ID card','VVPAT':'Voting Receipt Machine',
      'EVM':'Electronic Voting Machine','nomination filing':'candidate application',
      'nomination':'candidate application','poll day':'voting day',
      'counting day':'the day votes are counted','MCC':'election conduct rules',
      'NOTA':'None Of The Above','presiding officer':'the official in charge at your polling booth',
      'qualifying date':'the cutoff date to be old enough to vote',
      'model code of conduct':'rules candidates and parties must follow during elections',
      'affidavit':'sworn legal declaration by the candidate',
    },

    /**
     * @description Initialize all modules and start journey session
     */
    async init() {
      var self = this;
      // Init analytics
      AnalyticsModule.init();
      // Init translate
      TranslateModule.init();
      this.languages = TranslateModule.getLanguages();
      this.selectedLang = TranslateModule.getCurrent();
      // Init auth
      AuthModule.init(function(user) {
        if (user) {
          self.authUser = user;
          self.authPhotoURL = user.photoURL || '';
          self.authDisplayName = user.displayName || 'User';
          AuthModule.loadProgress().then(function(data) {
            if (data) {
              if (data.state) self.state = data.state;
              if (data.tab) self.tab = data.tab;
              if (data.checklist) self.checklist = data.checklist;
              if (data.candidates) { self.candidates = data.candidates; self.allCandidates = data.candidates; self.candidatesLoaded = true; }
              if (data.evmVoted) self.evmVoted = data.evmVoted;
              if (data.state && data.state !== 'UNINITIALIZED' && data.state !== 'ELIGIBILITY_CHECK') {
                self.showOnboarding = false;
              }
            }
          });
        } else {
          self.authUser = null; self.authPhotoURL = ''; self.authDisplayName = '';
        }
      });
      // Init AI
      AIModule.init();
      // A4: Init Realtime Database
      RealtimeModule.init();
      RealtimeModule.onChange(function(counters) {
        self.civicActivity = Object.assign({}, counters);
      });
      RealtimeModule.increment('activeJourneys');
      // Start session
      try {
        var d = await apiFetch(API + '/api/journey/start', { method: 'POST' });
        this.sessionId = d.session_id; this.state = d.state; this.message = d.message;
      } catch (e) { this.message = 'Could not connect to server.'; showToast('Connection issue. Some features may be offline.', 'error'); }
      try {
        var cl = await apiFetch(API + '/api/services/calendar-links');
        this.calendarLinks = cl;
      } catch (e) {}
      // Update title
      this._updateTitle();
    },

    /**
     * @description Handle tab change with lazy rendering and analytics
     * @param {string} newTab - Tab name
     */
    switchTab: debounce(function(newTab) {
      if (!_tabRendered[newTab]) {
        this.showSkeleton = true;
        _tabRendered[newTab] = true;
        var self = this;
        setTimeout(function() { self.showSkeleton = false; }, CONSTANTS.SKELETON_DELAY_MS);
      }
      this.tab = newTab;
      this._updateTitle();
      announce(newTab.charAt(0).toUpperCase() + newTab.slice(1) + ' tab opened');
      AnalyticsModule.track('tab_changed', { tab_name: newTab });
      this._saveProgress();
    }, CONSTANTS.TAB_SWITCH_DEBOUNCE_MS),

    /**
     * @description Update document title based on current tab
     */
    _updateTitle: function() {
      var titles = {
        journey: 'CivicPulse — Your Voter Journey',
        candidates: 'CivicPulse — Candidate Discovery',
        evm: 'CivicPulse — EVM Simulator',
        resources: 'CivicPulse — Election Readiness'
      };
      document.title = titles[this.tab] || 'CivicPulse — Election Readiness';
    },

    /**
     * @description Save progress to Firestore/localStorage
     */
    _saveProgress: function() {
      AuthModule.saveProgress({
        state: this.state, tab: this.tab, checklist: this.checklist,
        candidates: this.candidates, evmVoted: this.evmVoted,
        candidatesLoaded: this.candidatesLoaded
      });
    },

    /** @description Check eligibility with validation */
    async checkEligibility() {
      if (!Validator.isNonEmptyString(this.dob) || !Validator.isValidState(this.location)) return;
      this.loading = true;
      try {
        var d = await apiFetch(API + '/api/journey/eligibility', {
          method: 'POST', headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify({ session_id: this.sessionId, dob: this.dob, location: this.location })
        });
        if (!d) throw new Error('Empty response');
        this._applyEligibility(d);
      } catch (e) {
        Logger.error('checkEligibility failed:', e.message);
        showToast('Could not check eligibility', 'error');
      }
      this.loading = false;
    },

    /** @description Apply eligibility response @param {Object} d */
    _applyEligibility(d) {
      this.state = d.state; this.path = d.path; this.message = d.message;
      this.age = d.age; this.deadlines = d.deadlines || {};
      if (d.civic_tips) this.civicTips = d.civic_tips;
      if (d.path === 'URGENT_POLLING') this.urgentWB = true;
      this.showOnboarding = false; this.tab = 'journey';
      AnalyticsModule.track('journey_step_completed', { step: 'eligibility' });
      this._saveProgress(); this.speak(d.message);
    },

    /** @description Submit onboarding form with validation */
    async submitOnboarding() {
      var ageNum = Validator.sanitizeAge(this.age);
      if (!Validator.isValidAge(ageNum) || !Validator.isValidState(this.location)) {
        showToast('Please enter a valid age and location', 'error');
        return;
      }
      this.age = ageNum;
      this.dob = (new Date().getFullYear() - ageNum) + '-01-01';
      await this.checkEligibility();
    },

    /** @description Verify registration @param {boolean} isRegistered */
    async verifyRegistration(isRegistered) {
      this.loading = true;
      try {
        var d = await apiFetch(API + '/api/journey/registration', {
          method: 'POST', headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify({ session_id: this.sessionId, is_registered: isRegistered })
        });
        this.state = d.state; this.message = d.message;
        if (d.registration_steps) this.registrationSteps = d.registration_steps;
        if (d.state === 'CANDIDATE_RESEARCH') {
          this.constituency = this.location;
          await this.loadCandidates();
        }
        AnalyticsModule.track('journey_step_completed', { step: 'registration' });
        this._saveProgress();
        this.speak(d.message);
      } catch (e) { this.message = 'Error verifying registration.'; showToast('Verification failed', 'error'); }
      this.loading = false;
    },

    /** @description Load candidates via Google Civic API */
    async loadCandidates() {
      this.candidatesLoading = true;
      this.candidatesFallback = false;
      this.candidatesLoadingMsg = 'Fetching candidates via Google Civic API...';
      announce('Fetching candidates via Google Civic API', 'polite');
      try {
        var d = await apiFetch(API + '/api/journey/candidates', {
          method: 'POST', headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify({ session_id: this.sessionId, constituency: this.constituency || this.location })
        });
        if (!d) throw new Error('Empty response');
        this._applyCandidateData(d);
      } catch (e) {
        Logger.error('loadCandidates failed:', e.message);
        this._loadFallbackCandidates();
      }
      this.candidatesLoading = false;
      this.candidatesLoadingMsg = '';
    },

    /** @description Apply candidate data from API response */
    _applyCandidateData(d) {
      this.state = d.state; this.message = d.message;
      this.candidates = d.candidate_cards || [];
      this.constituency = d.constituency || '';
      this.allCandidates = this.candidates.slice();
      this.candidatesLoaded = true;
      if (d._source === 'fallback_sample') {
        this.candidatesFallback = true;
        announce('Live data unavailable. Showing sample candidates.', 'polite');
      } else {
        announce('Candidates loaded from Google Civic Information API', 'polite');
      }
      this.switchTab('candidates');
      AnalyticsModule.track('journey_step_completed', { step: 'candidates', source: d._source || 'unknown' });
      this._saveProgress();
      this.speak(d.message);
      this._loadAllCandidateInsights();
    },

    /** @description Load hardcoded fallback candidates when API fails */
    _loadFallbackCandidates() {
      this.candidatesFallback = true;
      this.candidates = [
        { name: 'Arun Sharma', party: 'National Progress Party', manifesto_points: ['Improve local infrastructure', 'Better healthcare facilities', 'Increase employment opportunities'] },
        { name: 'Priya Deshmukh', party: "People's Democratic Front", manifesto_points: ['Digital literacy for all', 'Women safety initiatives', 'Clean energy push'] },
        { name: 'Rahul Kumar', party: 'Independent', manifesto_points: ['Anti-corruption measures', 'Youth skill development', 'Agricultural reform'] }
      ];
      this.allCandidates = this.candidates.slice();
      this.candidatesLoaded = true;
      this.switchTab('candidates');
      announce('Live data unavailable. Showing sample candidates.', 'polite');
      showToast('Live data unavailable — showing sample candidates.', 'info');
      this._loadAllCandidateInsights();
    },

    /**
     * @description A1 — Load AI insights for all candidates
     */
    async _loadAllCandidateInsights() {
      var self = this;
      for (var i = 0; i < this.candidates.length; i++) {
        var cand = this.candidates[i];
        var key = cand.name || ('cand_' + i);
        self.candidateInsightsLoading[key] = true;
        (function(candidate, k) {
          AIModule.analyzeCandidate(candidate).then(function(insight) {
            self.candidateInsights[k] = insight;
            self.candidateInsightsLoading[k] = false;
          });
        })(cand, key);
      }
    },

    /**
     * @description A1 — Get insight for a candidate
     * @param {Object} cand - Candidate object
     * @returns {Object|null} insight
     */
    getInsight(cand) {
      var key = cand.name || 'unknown';
      return this.candidateInsights[key] || null;
    },

    /**
     * @description A1 — Check if insight is loading
     * @param {Object} cand - Candidate object
     * @returns {boolean}
     */
    isInsightLoading(cand) {
      var key = cand.name || 'unknown';
      return this.candidateInsightsLoading[key] || false;
    },

    /**
     * @description A1 — Get tone badge color class
     * @param {string} tone - Positive|Neutral|Critical
     * @returns {string}
     */
    toneBadgeClass(tone) {
      if (tone === 'Positive') return 'bg-green-100 text-green-800 border-green-300';
      if (tone === 'Critical') return 'bg-amber-100 text-amber-800 border-amber-300';
      return 'bg-gray-100 text-gray-700 border-gray-300';
    },

    /**
     * @description A2 — Debounced natural language candidate search
     */
    searchCandidatesNL: debounce(async function() {
      var query = this.candidateSearchQuery.trim();
      if (!query) {
        this.candidates = this.allCandidates.slice();
        this.candidateSearchResults = null;
        return;
      }
      var self = this;
      var ids = await AIModule.searchCandidates(query, this.allCandidates);
      this.candidateSearchResults = ids;
      this.candidates = ids.map(function(id) { return self.allCandidates[id]; }).filter(Boolean);
      AnalyticsModule.track('ai_candidate_search', { query: query, results: ids.length });
    }, CONSTANTS.DEBOUNCE_DELAY),

    /**
     * @description A3 — Run sentiment analysis on candidate manifestos
     */
    async runSentimentAnalysis() {
      if (this.candidates.length < 2) return;
      this.sentimentLoading = true;
      this.sentimentScores = await SentimentModule.analyzeManifestos(this.candidates);
      this.sentimentLoading = false;
    },

    /**
     * @description A3 — Get sentiment bar width percentage
     * @param {number} score - Score from -1 to 1
     * @returns {number} percentage 0-100
     */
    sentimentBarWidth(score) {
      return Math.round(((score + 1) / 2) * 100);
    },

    /**
     * @description A3 — Get sentiment bar color
     * @param {number} score - Score from -1 to 1
     * @returns {string}
     */
    sentimentBarColor(score) {
      if (score > 0.25) return 'bg-green-500';
      if (score < -0.25) return 'bg-red-500';
      return 'bg-yellow-500';
    },

    /**
     * @description A5 — Add counting day to Google Calendar via API
     */
    async addToGoogleCalendar() {
      this.calendarAdding = true;
      var candidateNames = this.candidates.map(function(c) { return c.name; }).join(', ');
      await CalendarModule.addCountingDayEvent({
        boothAddress: this.boothAddress,
        candidateNames: candidateNames
      });
      this.calendarAdding = false;
    },

    /** @description Cast mock vote @param {Object} candidate */
    async castVote(candidate) {
      if (this.evmVoted) return;
      if (!candidate) { showToast('Please select a candidate first', 'info'); return; }
      this.evmVoted = true; this.vvpatCandidate = candidate; this.playBeep();
      this._startVVPAT();
      announce('Mock vote cast for ' + candidate.name, 'assertive');
      try {
        var d = await apiFetch(API + '/api/journey/simulate', {
          method: 'POST', headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify({ session_id: this.sessionId })
        });
        if (!d) throw new Error('Empty response');
        this.state = d.state; this.message = d.message;
        this.checklist = d.checklist || [];
        await this.loadPollingInfo();
        RealtimeModule.increment('evmCompleted');
        AnalyticsModule.track('evm_vote_cast');
        this._saveProgress(); this.speak('Vote cast successfully!');
      } catch (e) {
        Logger.error('castVote failed:', e.message);
        showToast('Vote recorded locally', 'info');
      }
    },

    /** @description Start VVPAT countdown display */
    _startVVPAT() {
      this.vvpatVisible = true;
      this.vvpatTimer = CONSTANTS.VVPAT_DISPLAY_SECONDS;
      var self = this;
      var iv = setInterval(function() {
        self.vvpatTimer--;
        if (self.vvpatTimer <= 0) { clearInterval(iv); self.vvpatVisible = false; }
      }, 1000);
    },

    /** @description Select candidate in EVM via keyboard @param {Object} cand */
    selectEVMCandidate(cand) { this.selectedEVMCandidate = cand; },

    /** @description D3: Full roving tabindex EVM keyboard @param {KeyboardEvent} event */
    handleEVMKeyboard(event) {
      if (!this.candidates.length) return;
      var max = this.candidates.length - 1;
      var handled = true;
      if (event.key === 'ArrowDown' || event.key === 'ArrowRight') {
        this.evmFocusIndex = Math.min(this.evmFocusIndex + 1, max);
      } else if (event.key === 'ArrowUp' || event.key === 'ArrowLeft') {
        this.evmFocusIndex = Math.max(this.evmFocusIndex - 1, 0);
      } else if (event.key === 'Home') {
        this.evmFocusIndex = 0;
      } else if (event.key === 'End') {
        this.evmFocusIndex = max;
      } else if (event.key === 'Enter' || event.key === ' ') {
        if (this.selectedEVMCandidate) this.castVote(this.selectedEVMCandidate);
      } else { handled = false; }
      if (handled) {
        event.preventDefault();
        this.selectedEVMCandidate = this.candidates[this.evmFocusIndex];
        this._focusEVMOption();
      }
    },

    /** @description Focus the current EVM radio option */
    _focusEVMOption() {
      var el = document.querySelector('[data-evm-index="' + this.evmFocusIndex + '"]');
      if (el) el.focus();
    },

    /** @description Load polling info */
    async loadPollingInfo() {
      try {
        var pi = await apiFetch(API + '/api/services/polling-info/' + encodeURIComponent(this.location));
        this.pollingInfo = pi;
        if (pi && pi.pollingLocations && pi.pollingLocations[0]) {
          var loc = pi.pollingLocations[0];
          this.boothAddress = loc.address.locationName + ', ' + loc.address.line1 + ', ' + loc.address.city;
          var d2 = await apiFetch(API + '/api/services/directions', {
            method: 'POST', headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ origin: this.location, destination: this.boothAddress })
          });
          this.directionsUrl = d2.directions_url || '';
          this.mapsEmbedUrl = 'https://www.google.com/maps/embed/v1/directions?key=' + CONFIG.MAPS_API_KEY +
            '&origin=' + encodeURIComponent(this.location) + '&destination=' + encodeURIComponent(this.boothAddress) +
            '&mode=' + this.mapsMode;
          this.showMapsEmbed = true;
          AnalyticsModule.track('booth_route_opened');
        }
      } catch (e) { Logger.error('Polling info error:', e); }
    },

    /** @description Toggle maps direction mode @param {string} mode */
    setMapsMode(mode) {
      this.mapsMode = mode;
      if (this.boothAddress) {
        this.mapsEmbedUrl = 'https://www.google.com/maps/embed/v1/directions?key=' + CONFIG.MAPS_API_KEY +
          '&origin=' + encodeURIComponent(this.location) + '&destination=' + encodeURIComponent(this.boothAddress) +
          '&mode=' + mode;
      }
    },

    /** @description Complete journey */
    async completeJourney() {
      try {
        var d = await apiFetch(API + '/api/journey/complete', {
          method: 'POST', headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify({ session_id: this.sessionId })
        });
        this.state = d.state; this.message = d.message;
        this._saveProgress();
        this.speak(d.message);
      } catch (e) { showToast('Could not complete journey', 'error'); }
    },

    /** @description Toggle simple mode */
    async toggleSimple() {
      try {
        var d = await apiFetch(API + '/api/journey/simple-mode', {
          method: 'POST', headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify({ session_id: this.sessionId })
        });
        this.simpleMode = d.simple_mode; this.message = d.message;
      } catch (e) { showToast('Could not toggle mode', 'error'); }
    },

    /** @description D4: Toggle high contrast with persistence */
    toggleContrast() {
      this.highContrast = !this.highContrast;
      document.documentElement.classList.toggle('dark');
      document.body.classList.toggle('high-contrast');
      localStorage.setItem('hc-mode', this.highContrast ? 'true' : 'false');
      announce(this.highContrast ? 'High contrast mode enabled' : 'High contrast mode disabled', 'polite');
    },

    /** @description Toggle voice assist */
    toggleVoice() {
      this.voiceAssist = !this.voiceAssist;
      if (this.voiceAssist && 'speechSynthesis' in window) this.speak('Voice assist enabled.');
    },

    /** @description Speak text @param {string} text */
    speak(text) {
      if (!this.voiceAssist || !('speechSynthesis' in window)) return;
      window.speechSynthesis.cancel();
      var u = new SpeechSynthesisUtterance(text); u.rate = 0.9; u.lang = 'en-IN';
      window.speechSynthesis.speak(u);
    },

    /** @description Play beep sound */
    playBeep() {
      try {
        var ctx = new (window.AudioContext || window.webkitAudioContext)();
        var osc = ctx.createOscillator(); var gain = ctx.createGain();
        osc.connect(gain); gain.connect(ctx.destination);
        osc.frequency.value = CONSTANTS.BEEP_FREQUENCY; osc.type = 'sine';
        gain.gain.setValueAtTime(0.3, ctx.currentTime);
        gain.gain.exponentialRampToValueAtTime(0.01, ctx.currentTime + CONSTANTS.BEEP_DURATION);
        osc.start(ctx.currentTime); osc.stop(ctx.currentTime + CONSTANTS.BEEP_DURATION);
      } catch (e) {}
    },

    /** @description Download ICS file */
    async downloadCountingDayICS() {
      try {
        var r = await fetch(API + '/api/services/calendar-ics');
        var blob = await r.blob();
        var url = URL.createObjectURL(blob);
        var a = document.createElement('a'); a.href = url; a.download = 'counting_day_2026.ics';
        document.body.appendChild(a); a.click();
        document.body.removeChild(a); URL.revokeObjectURL(url);
        RealtimeModule.increment('calendarAdded');
        AnalyticsModule.track('calendar_reminder_added');
      } catch (e) { showToast('Could not download calendar file', 'error'); }
    },

    /** @description Jargon tooltip @param {string} text @returns {string} */
    jargonTooltip(text) {
      if (!text) return text;
      var result = text;
      var self = this;
      var sorted = Object.keys(this.jargonMap).sort(function(a, b) { return b.length - a.length; });
      for (var i = 0; i < sorted.length; i++) {
        var term = sorted[i];
        var re = new RegExp('\\b' + term.replace(/[.*+?^${}()|[\]\\]/g, '\\$&') + '\\b', 'gi');
        result = result.replace(re, function(m) {
          var plain = self.jargonMap[term.toLowerCase()] || self.jargonMap[term] || m;
          return '<span class="jargon-term" title="Official term: ' + sanitizeHTML(m) + '">' + sanitizeHTML(plain) + '</span>';
        });
      }
      return result;
    },

    // === AI Chat Methods ===

    /** @description Open AI chat drawer with D1 focus trap */
    openAIChat() {
      this.aiOpen = true;
      AIModule.setIsOpen(true);
      AnalyticsModule.track('ai_chat_opened');
      this.$nextTick(function() {
        var drawer = document.getElementById('ai-chat-drawer');
        if (drawer) FocusManager.trap(drawer);
      });
    },

    /** @description Close AI chat drawer with D1 focus release */
    closeAIChat() {
      var drawer = document.getElementById('ai-chat-drawer');
      if (drawer) FocusManager.release(drawer);
      this.aiOpen = false;
      AIModule.setIsOpen(false);
      var btn = document.getElementById('ai-chat-toggle');
      if (btn) btn.focus();
    },

    /** @description Send AI chat message */
    async sendAIMessage() {
      var text = this.aiInput.trim();
      if (!text) return;
      this.aiMessages.push({ role: 'user', text: sanitizeHTML(text) });
      this.aiInput = '';
      this.aiTyping = true;
      this._scrollAIChat();
      var reply = await AIModule.sendMessage(text);
      this.aiTyping = false;
      if (reply) {
        this.aiMessages.push({ role: 'ai', text: reply });
        this._scrollAIChat();
      }
    },

    /** @description Clear AI chat */
    clearAIChat() {
      this.aiMessages = [];
      AIModule.clearChat();
    },

    /** @description Scroll AI chat to bottom */
    _scrollAIChat() {
      var self = this;
      this.$nextTick(function() {
        var el = document.getElementById('ai-chat-messages');
        if (el) el.scrollTop = el.scrollHeight;
      });
    },

    /** @description Format AI message @param {string} text @returns {string} */
    formatAIMessage(text) {
      if (!text) return '';
      return sanitizeHTML(text)
        .replace(/\*\*(.*?)\*\*/g, '<strong>$1</strong>')
        .replace(/\*(.*?)\*/g, '<em>$1</em>')
        .replace(/^[-•]\s+(.+)/gm, '<li>$1</li>')
        .replace(/(<li>.*<\/li>)/s, '<ul class="list-disc ml-4">$1</ul>')
        .replace(/\n/g, '<br>');
    },

    /** @description Handle AI chat keyboard @param {KeyboardEvent} e */
    handleAIChatKeydown(e) {
      if (e.key === 'Escape') { this.closeAIChat(); e.preventDefault(); return; }
      // Focus trap
      if (e.key === 'Tab') {
        var drawer = document.getElementById('ai-chat-drawer');
        if (!drawer) return;
        var focusable = drawer.querySelectorAll('button, input, [tabindex]:not([tabindex="-1"])');
        if (focusable.length === 0) return;
        var first = focusable[0]; var last = focusable[focusable.length - 1];
        if (e.shiftKey && document.activeElement === first) { last.focus(); e.preventDefault(); }
        else if (!e.shiftKey && document.activeElement === last) { first.focus(); e.preventDefault(); }
      }
    },

    // === Translate Methods ===

    /** @description Change language with validation @param {string} lang */
    changeLanguage: debounce(function(lang) {
      if (!Validator.isValidLanguageCode(lang)) return;
      this.selectedLang = lang;
      TranslateModule.translatePage(lang);
    }, CONSTANTS.DEBOUNCE_DELAY),

    // === Auth Methods ===

    /** @description Google sign in */
    async googleSignIn() { await AuthModule.signIn(); },

    /** @description Google sign out */
    async googleSignOut() {
      await AuthModule.signOut();
      this.authUser = null; this.authPhotoURL = ''; this.authDisplayName = '';
    },

    /** @description Stepper steps getter @returns {Array} */
    get stepperSteps() {
      var states = ['ELIGIBILITY_CHECK', 'REGISTRATION_VERIFIED', 'CANDIDATE_RESEARCH', 'POLLING_SIMULATION', 'POLLING_READY'];
      var labels = ['Check Eligibility', 'Verify Registration', 'Know Your Candidates', 'Cast Mock Vote', 'Election Day Ready'];
      var icons = ['person_search', 'fact_check', 'groups', 'touch_app', 'event'];
      var idx = states.indexOf(this.state);
      return labels.map(function(l, i) { return { label: l, icon: icons[i], done: i < idx, active: i === idx, locked: i > idx }; });
    },

    /** @description Eligibility check @returns {boolean} */
    get isEligible() {
      return this.state !== 'UNINITIALIZED' && this.state !== 'ELIGIBILITY_CHECK' && this.state !== 'CIVIC_EDUCATION';
    },

    /** @description Countdown text @returns {string} */
    get countdown() {
      var today = new Date(); var counting = new Date(2026, 4, 4);
      var diff = Math.ceil((counting - today) / (1000 * 60 * 60 * 24));
      if (diff === 1) return '📊 Counting day is TOMORROW!';
      if (diff === 0) return '📊 TODAY is counting day!';
      if (diff > 0) return '📊 ' + diff + ' days until counting day.';
      return '📊 Results have been announced.';
    }
  };
}
