<script setup lang="ts">
import {ref,onMounted,computed} from "vue";
import {api} from "./api";

const token=ref(localStorage.getItem("token")||"");
const user=ref<any>(JSON.parse(localStorage.getItem("user")||"null"));
const page=ref("Dashboard"), error=ref(""), busy=ref(false);
const dashboard=ref<any>({recent:[]}), customers=ref<any[]>([]), apps=ref<any[]>([]), audit=ref<any[]>([]);
const selected=ref<any>(null);
const login=ref({email:"admin@credora.ai",password:"Admin@123"});
const customer=ref({full_name:"",email:"",phone:"",annual_income:600000,employment_type:"Salaried"});
const loan=ref({customer_id:0,product:"Personal Loan",amount:300000,tenure_months:24,purpose:"",credit_score:720,monthly_debt:10000});
const doc=ref({document_type:"Bank Statement",file_name:"statement.pdf",extracted_summary:""});
const reviewNote=ref("");

const money=(v:number)=>new Intl.NumberFormat("en-IN",{style:"currency",currency:"INR",maximumFractionDigits:0}).format(v||0);
async function load(){
  if(!token.value)return;
  try{
    const [d,c,a]=await Promise.all([api.get("/dashboard"),api.get("/customers"),api.get("/applications")]);
    dashboard.value=d.data; customers.value=c.data; apps.value=a.data;
    if(!loan.value.customer_id && customers.value[0]) loan.value.customer_id=customers.value[0].id;
    if(page.value==="Audit") audit.value=(await api.get("/audit")).data;
  }catch(e:any){ if(e.response?.status===401) logout(); else error.value=e.response?.data?.detail||e.message }
}
async function signIn(){
  error.value=""; busy.value=true;
  try{const r=await api.post("/auth/login",login.value); token.value=r.data.access_token; user.value=r.data.user;
    localStorage.setItem("token",token.value); localStorage.setItem("user",JSON.stringify(user.value)); await load();
  }catch(e:any){error.value=e.response?.data?.detail||"Login failed"} finally{busy.value=false}
}
function logout(){localStorage.clear();token.value="";user.value=null}
async function addCustomer(){await api.post("/customers",customer.value); customer.value={full_name:"",email:"",phone:"",annual_income:600000,employment_type:"Salaried"}; await load()}
async function kyc(c:any){await api.patch(`/customers/${c.id}/kyc`,{status:c.kyc_status==="Verified"?"Pending":"Verified"}); await load()}
async function addLoan(){await api.post("/applications",loan.value); await load(); page.value="Applications"}
async function openApp(a:any){selected.value=(await api.get(`/applications/${a.id}`)).data; page.value="Case"}
async function addDoc(){await api.post("/documents",{application_id:selected.value.id,...doc.value}); await openApp(selected.value)}
async function verifyDoc(d:any){await api.patch(`/documents/${d.id}/verify`,{status:"Verified"}); await openApp(selected.value)}
async function risk(){const r=await api.post(`/risk/${selected.value.id}`); await openApp(selected.value); alert(`Risk: ${r.data.risk_band} (${r.data.risk_score}/100)\n${r.data.reasons.join("\n")}`)}
async function brief(){await api.post(`/underwriting/${selected.value.id}/brief`); await openApp(selected.value)}
async function decide(decision:string){await api.post(`/underwriting/${selected.value.id}/review`,{decision,note:reviewNote.value}); await openApp(selected.value); await load()}
async function notify(){const r=await api.post(`/notifications/${selected.value.id}`,{channel:"Email"}); alert(`${r.data.status}: ${r.data.message}`)}
function nav(p:string){page.value=p; selected.value=null; load()}
onMounted(load);
</script>


<template>
<div v-if="!token" class="login-page">
  <section class="login-story">
    <div class="wordmark light">CREDORA <i>AI</i></div>
    <div class="story-copy">
      <div class="eyebrow">AI-POWERED LENDING OPERATIONS</div>
      <h1>Credit decisions,<br><em>with context.</em></h1>
      <p>One workspace for onboarding, document intelligence, risk analysis and human-supervised underwriting.</p>
      <div class="flowline"><span>01 Onboard</span><span>02 Verify</span><span>03 Assess</span><span>04 Decide</span></div>
    </div>
    <div class="story-foot">PORTFOLIO FINTECH SYSTEM · SYNTHETIC DATA ONLY</div>
  </section>
  <section class="login-form-wrap">
    <div class="login-form">
      <div class="mobile-mark">CREDORA <i>AI</i></div>
      <div class="eyebrow dark">SECURE OPERATIONS CONSOLE</div>
      <h2>Welcome back.</h2><p class="sub">Sign in to continue to your lending workspace.</p>
      <label>Work email</label><input v-model="login.email" type="email">
      <label>Password</label><input v-model="login.password" type="password" @keyup.enter="signIn">
      <p v-if="error" class="error">{{error}}</p>
      <button class="ink-btn full" @click="signIn" :disabled="busy">{{busy?"Authenticating…":"Enter workspace →"}}</button>
      <div class="credentials"><b>Demo access</b><span>admin@credora.ai</span><span>Admin@123</span></div>
    </div>
  </section>
</div>

<div v-else class="workspace">
  <nav class="topnav">
    <div class="wordmark">CREDORA <i>AI</i></div>
    <div class="navlinks">
      <button v-for="p in ['Dashboard','Customers','Applications','New Application','Audit']" :class="{selected:page===p}" @click="nav(p)">{{p}}</button>
    </div>
    <div class="profile"><span><b>{{user?.name}}</b><small>{{user?.role}}</small></span><button @click="logout">↗</button></div>
  </nav>

  <main class="content">
    <div class="page-title">
      <div><div class="eyebrow dark">LENDING OPERATIONS / {{page.toUpperCase()}}</div><h1>{{page==='Dashboard'?'Decision intelligence':page}}</h1></div>
      <div class="live"><i></i> LIVE SYSTEM</div>
    </div>
    <p v-if="error" class="error">{{error}}</p>

    <section v-if="page==='Dashboard'">
      <div class="hero-grid">
        <div class="hero-card">
          <span class="kicker">PORTFOLIO EXPOSURE</span>
          <strong>{{money(dashboard.total_requested)}}</strong>
          <p>Total value of active loan requests in the workspace.</p>
          <div class="hero-actions"><button @click="nav('New Application')">New application →</button><button @click="nav('Applications')">Review queue</button></div>
        </div>
        <div class="score-grid">
          <article><span>Applications</span><b>{{dashboard.applications}}</b><small>All cases</small></article>
          <article><span>Under review</span><b>{{dashboard.under_review}}</b><small>Needs attention</small></article>
          <article><span>Approved</span><b>{{dashboard.approved}}</b><small>Human approved</small></article>
          <article class="risk"><span>High risk</span><b>{{dashboard.high_risk}}</b><small>Flagged cases</small></article>
        </div>
      </div>
      <div class="section-head"><div><span class="eyebrow dark">CASE QUEUE</span><h3>Recent applications</h3></div><button class="text-btn" @click="nav('Applications')">View all →</button></div>
      <div class="case-list">
        <div class="case-row header"><span>CASE</span><span>CUSTOMER</span><span>FACILITY</span><span>EXPOSURE</span><span>RISK</span><span>STATUS</span></div>
        <div class="case-row" v-for="a in dashboard.recent" @click="openApp(a)">
          <span class="mono">CR-{{String(a.id).padStart(4,'0')}}</span><span><b>{{a.customer_name}}</b></span><span>{{a.product}}</span><span>{{money(a.amount)}}</span>
          <span><i class="risk-dot" :class="(a.risk_band||'none').toLowerCase()"></i>{{a.risk_band||"Unscored"}}</span><span class="case-status">{{a.status}}</span>
        </div>
        <div v-if="!dashboard.recent?.length" class="empty-state">No lending cases yet. Start by onboarding a customer.</div>
      </div>
    </section>

    <section v-if="page==='Customers'" class="split-layout">
      <div class="editor-card">
        <span class="step">01</span><div class="eyebrow dark">CUSTOMER ONBOARDING</div><h2>Create a borrower profile</h2><p class="sub">Use synthetic information for this portfolio environment.</p>
        <label>Full name</label><input v-model="customer.full_name">
        <div class="two"><div><label>Email</label><input v-model="customer.email" type="email"></div><div><label>Phone</label><input v-model="customer.phone"></div></div>
        <div class="two"><div><label>Annual income</label><input v-model.number="customer.annual_income" type="number"></div><div><label>Employment</label><select v-model="customer.employment_type"><option>Salaried</option><option>Self-employed</option><option>Business</option></select></div></div>
        <button class="ink-btn" @click="addCustomer">Create borrower →</button>
      </div>
      <div><div class="section-head"><div><span class="eyebrow dark">BORROWER DIRECTORY</span><h3>{{customers.length}} customer{{customers.length===1?'':'s'}}</h3></div></div>
        <div class="borrower-card" v-for="c in customers"><div class="avatar">{{c.full_name?.charAt(0)}}</div><div class="grow"><b>{{c.full_name}}</b><small>{{c.email}} · {{money(c.annual_income)}} / yr</small></div><button class="kyc" :class="{verified:c.kyc_status==='Verified'}" @click="kyc(c)">{{c.kyc_status==='Verified'?'✓ KYC VERIFIED':'VERIFY KYC'}}</button></div>
        <div v-if="!customers.length" class="empty-state">No borrowers onboarded.</div>
      </div>
    </section>

    <section v-if="page==='New Application'">
      <div class="application-sheet">
        <div class="sheet-intro"><span class="step">02</span><div class="eyebrow">NEW CREDIT REQUEST</div><h2>Structure the facility.</h2><p>Capture the requested product, exposure and initial credit information.</p></div>
        <div class="sheet-form">
          <label>Borrower</label><select v-model.number="loan.customer_id"><option :value="0">Select borrower</option><option v-for="c in customers" :value="c.id">{{c.full_name}}</option></select>
          <div class="two"><div><label>Loan product</label><select v-model="loan.product"><option>Personal Loan</option><option>Home Loan</option><option>Business Loan</option><option>Auto Loan</option></select></div><div><label>Requested amount</label><input v-model.number="loan.amount" type="number"></div></div>
          <div class="three"><div><label>Tenure / months</label><input v-model.number="loan.tenure_months" type="number"></div><div><label>Credit score</label><input v-model.number="loan.credit_score" type="number"></div><div><label>Monthly debt</label><input v-model.number="loan.monthly_debt" type="number"></div></div>
          <label>Purpose</label><textarea v-model="loan.purpose" placeholder="Describe the purpose of the facility"></textarea>
          <button class="paper-btn" @click="addLoan" :disabled="!loan.customer_id">Submit for assessment →</button>
        </div>
      </div>
    </section>

    <section v-if="page==='Applications'">
      <div class="section-head"><div><span class="eyebrow dark">UNDERWRITING PIPELINE</span><h3>All credit cases</h3></div><button class="ink-btn small" @click="nav('New Application')">+ New case</button></div>
      <div class="app-grid">
        <article v-for="a in apps" class="app-card" @click="openApp(a)">
          <div class="app-top"><span class="mono">CR-{{String(a.id).padStart(4,'0')}}</span><span class="case-status">{{a.status}}</span></div>
          <h3>{{a.customer_name}}</h3><p>{{a.product}}</p><strong>{{money(a.amount)}}</strong>
          <div class="app-meta"><span>Credit <b>{{a.credit_score}}</b></span><span>Risk <b>{{a.risk_band||"Pending"}}</b></span><span>Term <b>{{a.tenure_months}}m</b></span></div>
          <div class="open-case">Open case file →</div>
        </article>
        <div v-if="!apps.length" class="empty-state">No applications in the pipeline.</div>
      </div>
    </section>

    <section v-if="page==='Case' && selected">
      <button class="text-btn back" @click="nav('Applications')">← Back to pipeline</button>
      <div class="case-banner">
        <div><span class="mono">CR-{{String(selected.id).padStart(4,'0')}}</span><h2>{{selected.customer_name}}</h2><p>{{selected.product}} · {{selected.tenure_months}} months</p></div>
        <div class="amount"><small>REQUESTED EXPOSURE</small><b>{{money(selected.amount)}}</b><span class="case-status">{{selected.status}}</span></div>
      </div>
      <div class="case-metrics"><div><small>CREDIT SCORE</small><b>{{selected.credit_score}}</b></div><div><small>RISK BAND</small><b>{{selected.risk_band||"Pending"}}</b></div><div><small>RISK INDEX</small><b>{{selected.risk_score??"—"}}<i v-if="selected.risk_score!=null"> / 100</i></b></div><div><small>HUMAN DECISION</small><b>{{selected.human_approved?'Approved':'Pending'}}</b></div></div>

      <div class="case-columns">
        <div class="case-panel">
          <div class="panel-number">A</div><div class="eyebrow dark">DOCUMENT INTELLIGENCE</div><h3>Evidence room</h3>
          <div v-for="d in selected.documents" class="document-row"><div><b>{{d.document_type}}</b><small>{{d.file_name}}</small></div><button :class="{done:d.verification_status==='Verified'}" @click="d.verification_status!=='Verified'&&verifyDoc(d)">{{d.verification_status==='Verified'?'✓ VERIFIED':'VERIFY'}}</button></div>
          <div class="add-doc"><label>Document type</label><select v-model="doc.document_type"><option>Bank Statement</option><option>Payslip</option><option>Identity Document</option><option>Tax Record</option><option>Invoice</option></select><label>File name</label><input v-model="doc.file_name"><label>Extraction note</label><textarea v-model="doc.extracted_summary"></textarea><button class="outline-btn" @click="addDoc">+ Add evidence</button></div>
        </div>

        <div class="case-panel ai-panel">
          <div class="panel-number">B</div><div class="eyebrow dark">DECISION INTELLIGENCE</div><h3>Underwriting cockpit</h3>
          <div class="analysis-actions"><button class="ink-btn" @click="risk">Run risk engine</button><button class="outline-btn" @click="brief">Generate AI brief</button></div>
          <div class="brief"><span>AI UNDERWRITING MEMO</span><p>{{selected.ai_summary||"No memo generated. Run the risk engine, verify evidence, then generate an underwriting brief."}}</p><small>Decision support only · Human review required</small></div>
          <label>Underwriter rationale</label><textarea v-model="reviewNote" placeholder="Document the reason for the final decision…"></textarea>
          <div class="decision-bar"><button class="approve" @click="decide('approve')">✓ Approve</button><button class="request" @click="decide('request_info')">? Request info</button><button class="decline" @click="decide('reject')">× Decline</button></div>
          <button class="notify" @click="notify">Send decision notification →</button>
        </div>
      </div>
    </section>

    <section v-if="page==='Audit'">
      <div class="audit-title"><span class="step">05</span><div><div class="eyebrow dark">GOVERNANCE & TRACEABILITY</div><h2>Decision audit trail</h2><p class="sub">Every material action captured with actor, entity and timestamp.</p></div></div>
      <div class="timeline"><div v-for="x in audit" class="event"><div class="event-dot"></div><div class="event-time">{{new Date(x.created_at).toLocaleString()}}</div><div><b>{{x.action.replaceAll('_',' ')}}</b><p>{{x.entity}} #{{x.entity_id}} · {{x.details||'No additional detail'}}</p><small>{{x.actor}}</small></div></div><div v-if="!audit.length" class="empty-state">No audit events recorded.</div></div>
    </section>
  </main>
</div>
</template>
