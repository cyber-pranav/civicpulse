/* app.js — CivicPulse SPA Logic (Alpine.js) */
/* v2.0 — Post-election context, Counting Day, enhanced EVM simulator */
const API = '';

function civicPulse() {
  return {
    tab: 'journey', sessionId: null, state: 'UNINITIALIZED', path: null,
    simpleMode: false, loading: false, message: '',
    age: null, dob: '', location: '', isFirstTime: false,
    candidates: [], constituency: '', checklist: [], calendarLinks: [],
    pollingInfo: null, directionsUrl: '', boothAddress: '',
    evmVoted: false, vvpatVisible: false, vvpatCandidate: null, vvpatTimer: 0,
    highContrast: false, voiceAssist: false, speechSynth: null,
    civicTips: [], registrationSteps: [], deadlines: {},
    showOnboarding: true, urgentWB: false,
    countingDay: '04 May 2026',
    candidatesLoaded: false,

    /**
     * Jargon map — maps government terms to plain-language equivalents.
     * Used by jargonTooltip() to wrap terms in hoverable <span> tags.
     */
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
     * Initialize the app — start a journey session and fetch calendar links.
     */
    async init() {
      try {
        const r = await fetch(API+'/api/journey/start',{method:'POST'});
        const d = await r.json();
        this.sessionId = d.session_id; this.state = d.state; this.message = d.message;
      } catch(e){ this.message = 'Could not connect to server.'; }
      try {
        const r = await fetch(API+'/api/services/calendar-links');
        this.calendarLinks = await r.json();
      } catch(e){}
    },

    /**
     * Stage 1 — Check eligibility using DOB and location.
     */
    async checkEligibility() {
      if(!this.dob||!this.location) return;
      this.loading = true;
      try {
        const r = await fetch(API+'/api/journey/eligibility',{method:'POST',
          headers:{'Content-Type':'application/json'},
          body:JSON.stringify({session_id:this.sessionId,dob:this.dob,location:this.location})});
        const d = await r.json();
        this.state=d.state; this.path=d.path; this.message=d.message;
        this.age=d.age; this.deadlines=d.deadlines||{};
        if(d.civic_tips) this.civicTips=d.civic_tips;
        if(d.path==='URGENT_POLLING') this.urgentWB=true;
        this.showOnboarding=false;
        this.tab = 'journey';
        this.speak(d.message);
      } catch(e){ this.message='Error checking eligibility.'; }
      this.loading=false;
    },

    /**
     * Submit the onboarding form — compute DOB from age and check eligibility.
     */
    async submitOnboarding() {
      if (!this.age || !this.location) return;
      const year = new Date().getFullYear() - this.age;
      this.dob = `${year}-01-01`;
      await this.checkEligibility();
    },

    /**
     * Stage 2 — Verify voter registration status.
     */
    async verifyRegistration(isRegistered) {
      this.loading=true;
      try {
        const r = await fetch(API+'/api/journey/registration',{method:'POST',
          headers:{'Content-Type':'application/json'},
          body:JSON.stringify({session_id:this.sessionId,is_registered:isRegistered})});
        const d = await r.json();
        this.state=d.state; this.message=d.message;
        if(d.registration_steps) this.registrationSteps=d.registration_steps;
        if(d.state==='CANDIDATE_RESEARCH'){
          this.constituency = this.location;
          await this.loadCandidates();
        }
        this.speak(d.message);
      } catch(e){ this.message='Error verifying registration.'; }
      this.loading=false;
    },

    /**
     * Stage 3 — Load candidate cards from the backend (Civic API or mock).
     */
    async loadCandidates() {
      try {
        const r = await fetch(API+'/api/journey/candidates',{method:'POST',
          headers:{'Content-Type':'application/json'},
          body:JSON.stringify({session_id:this.sessionId,constituency:this.constituency||this.location})});
        const d = await r.json();
        this.state=d.state; this.message=d.message;
        this.candidates=d.candidate_cards||[]; this.constituency=d.constituency||'';
        this.candidatesLoaded = true;
        this.tab='candidates';
        this.speak(d.message);
      } catch(e){ this.message='Error loading candidates.'; }
    },

    /**
     * Stage 4 — Cast a mock vote in the EVM simulator.
     * Triggers a beep sound and 7-second VVPAT slip animation.
     */
    async castVote(candidate) {
      if(this.evmVoted) return; // Prevent double-voting
      this.evmVoted=true; this.vvpatCandidate=candidate; this.playBeep();
      this.vvpatVisible=true; this.vvpatTimer=7;
      const iv=setInterval(()=>{this.vvpatTimer--;if(this.vvpatTimer<=0){clearInterval(iv);this.vvpatVisible=false;}},1000);
      try {
        const r = await fetch(API+'/api/journey/simulate',{method:'POST',
          headers:{'Content-Type':'application/json'},
          body:JSON.stringify({session_id:this.sessionId})});
        const d = await r.json();
        this.state=d.state; this.message=d.message;
        this.checklist=d.checklist||[];
        await this.loadPollingInfo();
        this.speak('Vote cast successfully!');
      } catch(e){}
    },

    /**
     * Load polling station info and generate booth directions URL.
     */
    async loadPollingInfo() {
      try {
        const r = await fetch(API+'/api/services/polling-info/'+encodeURIComponent(this.location));
        this.pollingInfo = await r.json();
        if(this.pollingInfo?.pollingLocations?.[0]){
          const loc=this.pollingInfo.pollingLocations[0];
          this.boothAddress=`${loc.address.locationName}, ${loc.address.line1}, ${loc.address.city}`;
          const r2 = await fetch(API+'/api/services/directions',{method:'POST',
            headers:{'Content-Type':'application/json'},
            body:JSON.stringify({origin:this.location,destination:this.boothAddress})});
          const d2 = await r2.json();
          this.directionsUrl=d2.directions_url||'';
        }
      } catch(e){}
    },

    /**
     * Finalize the journey → RESULTS_WAITING state.
     */
    async completeJourney() {
      try {
        const r = await fetch(API+'/api/journey/complete',{method:'POST',
          headers:{'Content-Type':'application/json'},
          body:JSON.stringify({session_id:this.sessionId})});
        const d = await r.json();
        this.state=d.state; this.message=d.message;
        this.speak(d.message);
      } catch(e){}
    },

    /**
     * Toggle Emergency Simple Mode (≤ 15 word responses).
     */
    async toggleSimple() {
      try {
        const r = await fetch(API+'/api/journey/simple-mode',{method:'POST',
          headers:{'Content-Type':'application/json'},
          body:JSON.stringify({session_id:this.sessionId})});
        const d = await r.json();
        this.simpleMode=d.simple_mode; this.message=d.message;
      } catch(e){}
    },

    /**
     * Toggle high-contrast mode for accessibility.
     */
    toggleContrast() { this.highContrast=!this.highContrast; document.documentElement.classList.toggle('dark'); },

    /**
     * Toggle voice assist using Web Speech API.
     */
    toggleVoice() {
      this.voiceAssist=!this.voiceAssist;
      if(this.voiceAssist && 'speechSynthesis' in window) this.speak('Voice assist enabled.');
    },

    /**
     * Speak text aloud using the Web Speech Synthesis API.
     * @param {string} text - Text to speak.
     */
    speak(text) {
      if(!this.voiceAssist||!('speechSynthesis' in window)) return;
      window.speechSynthesis.cancel();
      const u=new SpeechSynthesisUtterance(text); u.rate=0.9; u.lang='en-IN';
      window.speechSynthesis.speak(u);
    },

    /**
     * Play a confirmation beep using the Web Audio API.
     * Triggered when a mock vote is cast in the EVM simulator.
     */
    playBeep() {
      try {
        const ctx=new(window.AudioContext||window.webkitAudioContext)();
        const osc=ctx.createOscillator(); const gain=ctx.createGain();
        osc.connect(gain); gain.connect(ctx.destination);
        osc.frequency.value=880; osc.type='sine';
        gain.gain.setValueAtTime(0.3,ctx.currentTime);
        gain.gain.exponentialRampToValueAtTime(0.01,ctx.currentTime+0.3);
        osc.start(ctx.currentTime); osc.stop(ctx.currentTime+0.3);
      } catch(e){}
    },

    /**
     * Download a .ics file for the Counting Day reminder.
     */
    async downloadCountingDayICS() {
      try {
        const r = await fetch(API+'/api/services/calendar-ics');
        const blob = await r.blob();
        const url = URL.createObjectURL(blob);
        const a = document.createElement('a');
        a.href = url; a.download = 'counting_day_2026.ics';
        document.body.appendChild(a); a.click();
        document.body.removeChild(a); URL.revokeObjectURL(url);
      } catch(e){ alert('Could not download calendar file.'); }
    },

    /**
     * Wrap jargon terms in hoverable <span> tags showing the simplified term.
     * The original government jargon appears on hover/tap via the title attribute.
     * @param {string} text - Text to process.
     * @returns {string} HTML with jargon terms wrapped in tooltip spans.
     */
    jargonTooltip(text) {
      if(!text) return text;
      let result=text;
      const sorted=Object.keys(this.jargonMap).sort((a,b)=>b.length-a.length);
      for(const term of sorted){
        const re=new RegExp('\\b'+term.replace(/[.*+?^${}()|[\]\\]/g,'\\$&')+'\\b','gi');
        result=result.replace(re, m => {
          const plain=this.jargonMap[term.toLowerCase()]||this.jargonMap[term]||m;
          return `<span class="jargon-term" title="Official term: ${m}" data-jargon="${m}">${plain}</span>`;
        });
      }
      return result;
    },

    /**
     * Compute the vertical stepper steps based on current journey state.
     * Icons: ✓ (done), number (active), 🔒 (locked).
     */
    get stepperSteps() {
      const states=['ELIGIBILITY_CHECK','REGISTRATION_VERIFIED','CANDIDATE_RESEARCH','POLLING_SIMULATION','POLLING_READY'];
      const labels=['Check Eligibility','Verify Registration','Know Your Candidates','Cast Mock Vote','Election Day Ready'];
      const icons=['person_search','fact_check','groups','touch_app','event'];
      const idx=states.indexOf(this.state);
      return labels.map((l,i)=>({label:l,icon:icons[i],done:i<idx,active:i===idx,locked:i>idx}));
    },

    /**
     * Whether the user has passed eligibility and can access journey features.
     */
    get isEligible() { return this.state!=='UNINITIALIZED'&&this.state!=='ELIGIBILITY_CHECK'&&this.state!=='CIVIC_EDUCATION'; },

    /**
     * Dynamic countdown string reflecting post-election context.
     */
    get countdown() {
      const today = new Date(2026, 4, 2); // May 2, 2026
      const counting = new Date(2026, 4, 4); // May 4, 2026
      const diff = Math.ceil((counting - today) / (1000*60*60*24));
      if(diff === 1) return '📊 Counting day is TOMORROW!';
      if(diff === 0) return '📊 TODAY is counting day!';
      if(diff > 0) return `📊 ${diff} days until counting day.`;
      return '📊 Results have been announced.';
    }
  };
}
