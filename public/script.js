(() => {
  "use strict";
  const $ = (id) => document.getElementById(id);
  const navLabels = {overview:"Overview", analyze:"Analyze transaction", history:"Scan history", about:"How it works"};
  const modelNames = {isolation_forest:"Isolation Forest", svm:"One-Class SVM", xgboost:"XGBoost"};
  const disclaimer = "Educational research prototype trained on synthetic transactions. A result cannot establish whether a real payment is fraudulent or safe.";
  const API_BASE = String(window.UPI_CONFIG?.API_BASE_URL || "").trim().replace(/\/$/, "");
  const dateFormatter = new Intl.DateTimeFormat("en-IN", {day:"2-digit",month:"short",year:"numeric",hour:"2-digit",minute:"2-digit",hour12:true});
  const money = new Intl.NumberFormat("en-IN", {style:"currency",currency:"INR",maximumFractionDigits:2});
  const state = {mode:"checking",history:loadHistory(),last:null,preset:null,busy:false};
  let toastTimeout;

  function loadHistory() {
    try {
      const data = JSON.parse(sessionStorage.getItem("upi-sentinel-history") || "[]");
      return Array.isArray(data) ? data.filter((item) => item && Number.isFinite(item.amount) && typeof item.timestamp === "string" && typeof item.fraud_detected === "boolean" && Number.isFinite(item.fraud_votes)).slice(0,40) : [];
    } catch { return []; }
  }
  function saveHistory() {
    try { sessionStorage.setItem("upi-sentinel-history", JSON.stringify(state.history)); } catch { /* Browser storage may be unavailable. */ }
  }
  function fmtAmount(amount) { return money.format(amount); }
  function fmtDate(value) {
    const dt = new Date(value);
    return Number.isNaN(dt.getTime()) ? String(value) : dateFormatter.format(dt);
  }
  function dateLocal(date) {
    const pad = (n) => String(n).padStart(2,"0");
    return `${date.getFullYear()}-${pad(date.getMonth()+1)}-${pad(date.getDate())}T${pad(date.getHours())}:${pad(date.getMinutes())}`;
  }
  function svgIcon(name) {
    const s = document.createElementNS("http://www.w3.org/2000/svg", "svg");
    const use = document.createElementNS("http://www.w3.org/2000/svg", "use");
    use.setAttribute("href", `#icon-${name}`);
    s.append(use);
    return s;
  }
  function showToast(message) {
    const el = $("toast"); el.textContent = message; el.hidden = false;
    clearTimeout(toastTimeout); toastTimeout = setTimeout(() => { el.hidden = true; }, 3300);
  }
  function navigate(view) {
    if (!navLabels[view]) return;
    for (const [key] of Object.entries(navLabels)) {
      const page = $(`view-${key}`); const selected = key === view;
      page.hidden = !selected; page.classList.toggle("active", selected);
    }
    document.querySelectorAll("[data-view]").forEach((button) => {
      const active = button.dataset.view === view;
      button.classList.toggle("active", active);
      if (active) button.setAttribute("aria-current", "page"); else button.removeAttribute("aria-current");
    });
    $("breadcrumb-current").textContent = navLabels[view];
    $("sidebar").classList.remove("open"); $("sidebar-overlay").classList.remove("open");
    window.scrollTo({top:0,behavior:"instant"});
    if (view === "history") renderHistory();
  }
  function setMode(mode) {
    state.mode = mode;
    const b = $("connection-badge"), m = $("mode-banner-text"), a = $("mode-action");
    b.className = `connection ${mode === "live" ? "online" : mode === "demo" ? "demo" : "offline"}`;
    if (mode === "live") {
      $("connection-text").textContent = "ML engine online";
      m.textContent = "Live ML engine connected. Assessments are produced by the trained synthetic-data ensemble.";
      a.hidden = true;
    } else if (mode === "demo") {
      $("connection-text").textContent = "Guided demo";
      m.textContent = "DEMO MODE — illustrative sample outputs only. No machine-learning inference is running. Only the two preset examples can be previewed.";
      a.textContent = "Retry connection"; a.hidden = false;
    } else {
      $("connection-text").textContent = mode === "checking" ? "Checking engine" : "Engine unavailable";
      m.textContent = mode === "checking" ? "Connecting to the inference API…" : "The ML API is not reachable. Start the Flask backend to run real inference, or explore two clearly labeled demo scenarios.";
      a.textContent = "Try guided demo"; a.hidden = mode === "checking";
    }
  }
  async function checkHealth() {
    setMode("checking");
    const controller = new AbortController();
    const timer = setTimeout(() => controller.abort(), 7500);
    try {
      const response = await fetch(`${API_BASE}/api/health`, {signal: controller.signal, cache:"no-store"});
      if (!response.ok) throw Error(`HTTP ${response.status}`);
      const json = await response.json();
      if (json.status !== "ready") throw Error("Model not ready");
      setMode("live");
    } catch { setMode("offline"); } finally {clearTimeout(timer);}
  }
  function sample(which) {
    const d = new Date(); d.setDate(d.getDate()-1);
    d.setHours(which === "routine" ? 14 : 2, which === "routine" ? 25 : 10,0,0);
    $("amount").value = which === "routine" ? "1250" : "35000";
    $("timestamp").value = dateLocal(d);
    state.preset = {which,amount:Number($("amount").value),timestamp:$("timestamp").value};
    document.querySelectorAll("[data-sample]").forEach((el) => el.classList.toggle("selected",el.dataset.sample === which));
    $("form-error").hidden = true;
  }
  function validate() {
    const amount = Number($("amount").value);
    const timestamp = $("timestamp").value;
    if (!$("amount").value.trim() || !Number.isFinite(amount) || amount < .01 || amount > 10000000) throw new Error("Enter a valid amount between ₹0.01 and ₹1,00,00,000.");
    if (!/^\d{4}-\d\d-\d\dT\d\d:\d\d$/.test(timestamp) || Number.isNaN(new Date(timestamp).getTime())) throw new Error("Choose a valid transaction date and time.");
    return {amount, timestamp};
  }
  function demoResponse(which, request) {
    const anomaly = which === "unusual";
    const votes = anomaly ? 3 : 0;
    return {
      fraud_detected: anomaly, fraud_votes: votes, risk_level: anomaly ? "elevated" : "low",
      isolation_forest: anomaly ? "Potential Fraud" : "Normal",
      svm: anomaly ? "Potential Fraud" : "Normal",
      xgboost: anomaly ? "Potential Fraud" : "Normal",
      signals: anomaly ? ["Illustrative high-value amount for this demo scenario.","Illustrative overnight transaction time."] : ["Illustrative routine-sized payment.","Illustrative daytime transaction time."],
      input: request, source:"demo", disclaimer
    };
  }
  function showBusy(busy) {
    state.busy = busy;
    $("analyze-button").disabled = busy;
    $("analyze-button").querySelector("span").textContent = busy ? "Analyzing…" : "Analyze transaction";
    $("result-empty").hidden = busy || !!state.last;
    $("result-loading").hidden = !busy;
    $("result-content").hidden = busy || !state.last;
  }
  function showFormError(message) { const el=$("form-error"); el.textContent = message; el.hidden=false; }
  async function submitAnalysis(event) {
    event.preventDefault(); if (state.busy) return;
    let request;
    try {request = validate();} catch (e) {showFormError(e.message);return;}
    if (state.mode !== "live" && state.mode !== "demo") {showFormError("The ML engine is offline. Start your Flask API or select guided demo mode.");return;}
    if (state.mode === "demo" && (!state.preset || Number($("amount").value) !== state.preset.amount || $("timestamp").value !== state.preset.timestamp)) {
      showFormError("Guided demo only supports the two sample presets. Connect the live API to analyze custom amounts."); return;
    }
    $("form-error").hidden = true; state.last = null;showBusy(true);
    try {
      let result;
      if (state.mode === "demo") {
        result = demoResponse(state.preset.which,request);
      } else {
        const controller = new AbortController(); const timer = setTimeout(() => controller.abort(), 30000);
        try {
          const response = await fetch(`${API_BASE}/api/check_fraud`, {method:"POST",headers:{"Content-Type":"application/json"},body:JSON.stringify({amount:request.amount,timestamp:request.timestamp.replace("T"," ")}),signal:controller.signal});
          const json = await response.json().catch(() => ({}));
          if (!response.ok) throw new Error(json.error || `Analysis failed (HTTP ${response.status}).`);
          result = {...json,source:"live"};
        } finally {clearTimeout(timer);}
      }
      if (typeof result.fraud_detected !== "boolean" || !["Normal","Potential Fraud"].includes(result.isolation_forest) || !["Normal","Potential Fraud"].includes(result.svm) || !["Normal","Potential Fraud"].includes(result.xgboost)) throw new Error("The API returned an invalid model response.");
      const votes = [result.isolation_forest,result.svm,result.xgboost].filter((v) => v === "Potential Fraud").length;
      if (result.fraud_detected !== (votes >= 2)) throw new Error("The API returned inconsistent model votes.");
      state.last = {...result,fraud_votes:votes,amount:request.amount,timestamp:request.timestamp,checked_at:new Date().toISOString(),source:result.source};
      state.history.unshift(state.last);state.history = state.history.slice(0,40);saveHistory();
      renderResult();renderStats();renderRecent();renderHistory();
      showToast(result.source === "demo" ? "Illustrative demo result displayed." : "Live assessment completed.");
    } catch (e) {
      showFormError(e.name === "AbortError" ? "The API timed out. Check that your backend is running." : e.message || "Could not reach the ML API.");
    } finally {showBusy(false);}
  }
  function renderResult() {
    const r=state.last;if(!r)return;
    const elevated=r.fraud_detected, status=$("result-status");status.classList.toggle("elevated",elevated);
    $("result-title").textContent=elevated?"Elevated anomaly signal":"No majority anomaly signal";
    $("result-description").textContent=elevated?"At least two ensemble models flagged this pattern for closer review. This does not prove fraud.":"Fewer than two models flagged an anomaly. This does not guarantee the payment is safe.";
    $("result-source").textContent=r.source === "demo" ? "ILLUSTRATIVE DEMO" : "LIVE MODEL OUTPUT";
    $("risk-icon").replaceChildren(svgIcon(elevated?"alert":"check"));
    $("result-consensus").textContent=`${r.fraud_votes} of 3 anomaly votes`;
    const holder=$("model-votes");holder.replaceChildren();
    for (const [key,name] of Object.entries(modelNames)) {
      const anomaly=r[key] === "Potential Fraud";
      const row=document.createElement("div");row.className="vote-row";
      const label=document.createElement("span");label.className="vote-label";label.textContent=name;
      const signal=document.createElement("span");signal.className=`vote-state ${anomaly?"anomaly":""}`;signal.textContent=anomaly?"Anomaly flagged":"No anomaly";
      const bar=document.createElement("div");bar.className="vote-bar";const fill=document.createElement("span");if(anomaly)fill.classList.add("anomaly");bar.append(fill);
      row.append(label,signal,bar);holder.append(row);
    }
    const signals=$("result-signals");signals.replaceChildren();
    const items=Array.isArray(r.signals) && r.signals.length ? r.signals : ["Only amount and local transaction time were analyzed.","These indicators do not establish whether a payment is fraudulent."];
    for (const sentence of items.slice(0,4)) {const li=document.createElement("li");li.textContent=String(sentence);signals.append(li);}
    $("result-empty").hidden=true;$("result-content").hidden=false;
  }
  function renderStats() {
    const total=state.history.length,flagged=state.history.filter((r)=>r.fraud_detected).length;
    $("stat-total").textContent=String(total);$("stat-flagged").textContent=String(flagged);
    $("stat-rate").textContent=total?`${Math.round(100*flagged/total)}%`:"—";
    $("history-count").textContent=String(total);
    $("history-subtitle").textContent=`${total} assessment${total===1?"":"s"} in this session`;
  }
  function pillFor(r){const e=document.createElement("span");e.className=`pill ${r.fraud_detected?"elevated":"low"}`;e.textContent=r.fraud_detected?"Elevated":"Lower signal";return e;}
  function renderRecent() {
    const holder=$("recent-activity");holder.replaceChildren();
    if (!state.history.length) {
      const empty=document.createElement("div");empty.className="empty-mini";
      const symbol=document.createElement("div");symbol.className="empty-mini-icon";symbol.append(svgIcon("clock"));
      const title=document.createElement("strong");title.textContent="No activity yet";
      const subtitle=document.createElement("span");subtitle.textContent="Your transaction assessments will appear here.";
      empty.append(symbol,title,subtitle);holder.append(empty);return;
    }
    for (const r of state.history.slice(0,4)) {
      const row=document.createElement("div");row.className="recent-row";
      const icon=document.createElement("div");icon.className="recent-symbol";icon.append(svgIcon("search"));
      const main=document.createElement("div");main.className="recent-row-main";
      const amount=document.createElement("strong");amount.textContent=fmtAmount(r.amount);
      const when=document.createElement("span");when.textContent=`${fmtDate(r.checked_at || r.timestamp)} · ${r.source === "demo"?"Demo":"Live"}`;
      main.append(amount,when);row.append(icon,main,pillFor(r));holder.append(row);
    }
  }
  function renderHistory() {
    const body=$("history-body");body.replaceChildren();
    const filter=$("history-filter").value,query=$("history-search").value.trim().toLowerCase();
    const shown=state.history.filter((r) => (filter==="all" || (filter==="elevated"?r.fraud_detected:!r.fraud_detected)) && (!query || String(r.amount).includes(query) || String(r.timestamp).toLowerCase().includes(query) || fmtAmount(r.amount).toLowerCase().includes(query)));
    if (!shown.length) {const tr=document.createElement("tr"),td=document.createElement("td");td.colSpan=5;td.className="table-empty";td.textContent=state.history.length?"No assessments match the current filter.":"No screenings yet. Analyze a payment to populate this table.";tr.append(td);body.append(tr);return;}
    for (const r of shown){const tr=document.createElement("tr");const cells=[fmtDate(r.timestamp),fmtAmount(r.amount),null,`${r.fraud_votes} / 3`,r.source==="demo"?"Illustrative demo":"Live model"];for(const cell of cells){const td=document.createElement("td");if(cell===null)td.append(pillFor(r));else td.textContent=cell;tr.append(td);}body.append(tr);}
  }
  function exportCSV() {
    if (!state.history.length) {showToast("There are no screenings to export.");return;}
    const fields=["timestamp","amount_inr","risk_level","fraud_votes","isolation_forest","svm","xgboost","source"];
    const values=state.history.map((r)=>[r.timestamp,Number(r.amount).toFixed(2),r.fraud_detected?"elevated":"low",r.fraud_votes,r.isolation_forest,r.svm,r.xgboost,r.source]);
    const csv=[fields,...values].map((row)=>row.map((cell)=>`"${String(cell??"").replace(/"/g,'""')}"`).join(",")).join("\r\n");
    downloadBlob(new Blob(["\ufeff",csv],{type:"text/csv;charset=utf-8"}),"upi-sentinel-session.csv");
  }
  function downloadBlob(blob, filename) {
    const url=URL.createObjectURL(blob),a=document.createElement("a");a.href=url;a.download=filename;document.body.append(a);a.click();a.remove();setTimeout(()=>URL.revokeObjectURL(url),1000);
  }
  function reportText(r) {
    return `UPI SENTINEL — ${r.source === "demo"?"ILLUSTRATIVE DEMO":"LIVE ML"} ASSESSMENT\nTransaction: ${fmtAmount(r.amount)}\nTime: ${r.timestamp.replace("T"," ")}\nAssessment: ${r.fraud_detected?"Elevated anomaly signal":"No majority anomaly signal"}\nConsensus: ${r.fraud_votes}/3 anomaly votes\nIsolation Forest: ${r.isolation_forest}\nOne-Class SVM: ${r.svm}\nXGBoost: ${r.xgboost}\n${disclaimer}`;
  }
  async function copyReport() {
    if(!state.last)return;
    try {await navigator.clipboard.writeText(reportText(state.last));showToast("Assessment copied to clipboard.");}
    catch {showToast("Clipboard not available. Use Save PDF instead.");}
  }
  function printReport() {
    const r=state.last;if(!r)return;
    const report=document.createElement("article");report.id="print-report";
    const header=document.createElement("h1");header.textContent="UPI Sentinel — Transaction Assessment";report.append(header);
    const subtitle=document.createElement("p");subtitle.textContent=`${r.source === "demo"?"ILLUSTRATIVE DEMO — NOT AN ML PREDICTION":"LIVE ML RESULT"} · Generated ${fmtDate(r.checked_at)}`;report.append(subtitle);
    const h2=document.createElement("h2");h2.textContent="Screening summary";report.append(h2);
    const table=document.createElement("table");const rows=[["Transaction amount",fmtAmount(r.amount)],["Transaction timestamp",r.timestamp.replace("T"," ")],["Assessment",r.fraud_detected?"Elevated anomaly signal":"No majority anomaly signal"],["Ensemble consensus",`${r.fraud_votes} of 3 anomaly votes`],...Object.entries(modelNames).map(([key,name])=>[name,r[key]])];
    for(const [key,val] of rows){const tr=document.createElement("tr"),th=document.createElement("th"),td=document.createElement("td");th.textContent=key;td.textContent=val;tr.append(th,td);table.append(tr);}report.append(table);
    const note=document.createElement("p");note.className="print-note";note.textContent=disclaimer;report.append(note);
    document.body.append(report);document.body.classList.add("printing-report");
    const cleanup=()=>{report.remove();document.body.classList.remove("printing-report");window.removeEventListener("afterprint",cleanup);};
    window.addEventListener("afterprint",cleanup);window.print();setTimeout(()=>{if(report.isConnected)cleanup();},15000);
  }
  function ask(question) {
    const prompts={why:"Why was this flagged?",models:"How do the models vote?",next:"What should I do next?"};
    const log=$("assistant-log"),user=document.createElement("div"),bot=document.createElement("div");
    user.className="user-message";user.textContent=prompts[question];bot.className="assistant-message";
    if(question==="models") bot.textContent="Isolation Forest and One-Class SVM search for unusual patterns relative to synthetic routine transactions; XGBoost learns from synthetic labels. Each returns one vote. At least two anomaly votes produce an elevated signal. These votes are not calibrated fraud probabilities.";
    else if(question==="why") {const r=state.last;bot.textContent=!r?"Run an assessment first so I can describe its model votes. I cannot explain an uncomputed result.":r.fraud_detected?`${r.fraud_votes} of 3 models flagged this transaction's pattern. The displayed contextual indicators are descriptive, not proof of why a particular model predicted an anomaly. ${r.source==="demo"?"This result is a demo illustration.":"The models were trained on synthetic data."}`:`Only ${r.fraud_votes} of 3 models flagged the pattern, so there was no majority anomaly signal. This does not verify a merchant or guarantee transaction safety.`;}
    else bot.textContent="If a payment appears suspicious, do not share your UPI PIN or OTP; verify the recipient through a trusted channel before paying. If money has already been transferred fraudulently, contact your bank and use official cybercrime reporting channels promptly. This prototype cannot investigate or reverse transactions.";
    log.append(user,bot);log.scrollTop=log.scrollHeight;
  }
  function init() {
    let savedTheme = "light"; try { if (localStorage.getItem("upi-sentinel-theme") === "dark") savedTheme = "dark"; } catch { /* Private browsing can disable storage. */ }
    document.body.dataset.theme=savedTheme;$("theme-toggle").replaceChildren(svgIcon(savedTheme==="dark"?"sun":"moon"));
    $("theme-toggle").addEventListener("click",()=>{const next=document.body.dataset.theme==="dark"?"light":"dark";document.body.dataset.theme=next;$("theme-toggle").replaceChildren(svgIcon(next==="dark"?"sun":"moon"));try{localStorage.setItem("upi-sentinel-theme",next);}catch{}});
    document.querySelectorAll("[data-view]").forEach((el)=>el.addEventListener("click",()=>navigate(el.dataset.view)));
    document.querySelectorAll("[data-go]").forEach((el)=>el.addEventListener("click",()=>navigate(el.dataset.go)));
    $("open-menu").addEventListener("click",()=>{$("sidebar").classList.add("open");$("sidebar-overlay").classList.add("open");});
    $("close-menu").addEventListener("click",()=>{$("sidebar").classList.remove("open");$("sidebar-overlay").classList.remove("open");});
    $("sidebar-overlay").addEventListener("click",()=>{$("sidebar").classList.remove("open");$("sidebar-overlay").classList.remove("open");});
    document.querySelectorAll("[data-sample]").forEach((el)=>el.addEventListener("click",()=>sample(el.dataset.sample)));
    for (const id of ["amount","timestamp"]) $(id).addEventListener("input",()=>{document.querySelectorAll("[data-sample]").forEach((el)=>el.classList.remove("selected"));});
    $("analysis-form").addEventListener("submit",submitAnalysis);
    $("mode-action").addEventListener("click",()=>state.mode==="demo"?checkHealth():setMode("demo"));
    $("history-search").addEventListener("input",renderHistory);$("history-filter").addEventListener("change",renderHistory);
    $("clear-history").addEventListener("click",()=>{if(!state.history.length)return;if(window.confirm("Clear all assessments stored in this browser tab?")){state.history=[];saveHistory();renderHistory();renderRecent();renderStats();showToast("Session history cleared.");}});
    $("export-history").addEventListener("click",exportCSV);$("copy-report").addEventListener("click",copyReport);$("download-report").addEventListener("click",printReport);
    document.querySelectorAll("[data-question]").forEach((el)=>el.addEventListener("click",()=>ask(el.dataset.question)));
    $("footer-year").textContent=String(new Date().getFullYear());
    $("current-date").textContent=new Intl.DateTimeFormat("en-IN",{dateStyle:"full"}).format(new Date());
    const initial=new Date();initial.setMinutes(initial.getMinutes()-5);$("timestamp").value=dateLocal(initial);
    renderStats();renderRecent();renderHistory();checkHealth();
  }
  if(document.readyState==="loading")document.addEventListener("DOMContentLoaded",init);else init();
})();
