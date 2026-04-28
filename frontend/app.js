/* app.js — CivicPulse SPA Logic (Alpine.js) */
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
        if(d.state!=='CIVIC_EDUCATION') {
            this.showOnboarding=false;
            this.tab = 'journey';
        }
        this.speak(d.message);
      } catch(e){ this.message='Error checking eligibility.'; }
      this.loading=false;
    },

    async submitOnboarding() {
      if (!this.age || !this.location) return;
      const year = new Date().getFullYear() - this.age;
      this.dob = `${year}-01-01`;
      await this.checkEligibility();
    },

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

    async loadCandidates() {
      try {
        const r = await fetch(API+'/api/journey/candidates',{method:'POST',
          headers:{'Content-Type':'application/json'},
          body:JSON.stringify({session_id:this.sessionId,constituency:this.constituency||this.location})});
        const d = await r.json();
        this.state=d.state; this.message=d.message;
        this.candidates=d.candidate_cards||[]; this.constituency=d.constituency||'';
        this.tab='candidates';
        this.speak(d.message);
      } catch(e){ this.message='Error loading candidates.'; }
    },

    async castVote(candidate) {
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

    async toggleSimple() {
      try {
        const r = await fetch(API+'/api/journey/simple-mode',{method:'POST',
          headers:{'Content-Type':'application/json'},
          body:JSON.stringify({session_id:this.sessionId})});
        const d = await r.json();
        this.simpleMode=d.simple_mode; this.message=d.message;
      } catch(e){}
    },

    toggleContrast() { this.highContrast=!this.highContrast; document.documentElement.classList.toggle('dark'); },

    toggleVoice() {
      this.voiceAssist=!this.voiceAssist;
      if(this.voiceAssist && 'speechSynthesis' in window) this.speak('Voice assist enabled.');
    },

    speak(text) {
      if(!this.voiceAssist||!('speechSynthesis' in window)) return;
      window.speechSynthesis.cancel();
      const u=new SpeechSynthesisUtterance(text); u.rate=0.9; u.lang='en-IN';
      window.speechSynthesis.speak(u);
    },

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

    jargonTooltip(text) {
      if(!text) return text;
      let result=text;
      const sorted=Object.keys(this.jargonMap).sort((a,b)=>b.length-a.length);
      for(const term of sorted){
        const re=new RegExp('\\b'+term.replace(/[.*+?^${}()|[\]\\]/g,'\\$&')+'\\b','gi');
        result=result.replace(re, m => {
          const plain=this.jargonMap[term.toLowerCase()]||this.jargonMap[term]||m;
          return `<span class="jargon-term" title="${plain}">${m}</span>`;
        });
      }
      return result;
    },

    get stepperSteps() {
      const states=['ELIGIBILITY_CHECK','REGISTRATION_VERIFIED','CANDIDATE_RESEARCH','POLLING_SIMULATION','POLLING_READY'];
      const labels=['Check Eligibility','Verify Registration','Know Your Candidates','Cast Mock Vote','Election Day Ready'];
      const icons=['person_search','fact_check','groups','touch_app','event'];
      const idx=states.indexOf(this.state);
      return labels.map((l,i)=>({label:l,icon:icons[i],done:i<idx,active:i===idx,locked:i>idx}));
    },

    get isEligible() { return this.state!=='UNINITIALIZED'&&this.state!=='ELIGIBILITY_CHECK'&&this.state!=='CIVIC_EDUCATION'; },
    get countdown() { return '🗳️ Voting is TOMORROW!'; }
  };
}
