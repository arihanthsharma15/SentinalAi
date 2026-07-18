document.addEventListener('DOMContentLoaded', () => {
  // Initialize navigation icons
  lucide.createIcons();

  const reportContainer = document.getElementById('reportItemContainer');
  const timestampEl = document.getElementById('reportTimestamp');
  const countEl = document.getElementById('reportTotalCount');
  const actionEl = document.getElementById('reportPrimaryAction');
  const riskEl = document.getElementById('reportRiskLevel');

  const activeRecordsRaw = localStorage.getItem('sentinel_active_records');
  let records = [];

  function formatINR(amount) {
    return new Intl.NumberFormat('en-IN', {
      style: 'currency',
      currency: 'INR',
      maximumFractionDigits: 0,
    }).format(amount);
  }

  if (activeRecordsRaw) {
    records = JSON.parse(activeRecordsRaw);
  }

  // Set Report Metadata
  const now = new Date();
  timestampEl.innerText = `Generated: ${now.toLocaleDateString()} at ${now.toLocaleTimeString()}`;
  countEl.innerText = records.length;

  if (records.length > 0) {
    const actionsMap = {};
    let highestScore = 0;

    records.forEach(r => {
      const act = r.gemmaAnalysis.recommended_action;
      actionsMap[act] = (actionsMap[act] || 0) + 1;
      if (r.gemmaAnalysis.risk_score > highestScore) {
        highestScore = r.gemmaAnalysis.risk_score;
      }
    });

    const primaryAction = Object.keys(actionsMap).reduce((a, b) => actionsMap[a] > actionsMap[b] ? a : b);
    actionEl.innerText = primaryAction.replace('_', ' ');

    if (highestScore >= 80) {
      riskEl.innerText = "CRITICAL";
      riskEl.className = "text-2xl font-black text-red-500 mt-1";
    } else if (highestScore >= 50) {
      riskEl.innerText = "ELEVATED";
      riskEl.className = "text-2xl font-black text-amber-500 mt-1";
    } else {
      riskEl.innerText = "STANDARD";
      riskEl.className = "text-2xl font-black text-emerald-400 mt-1 glow-cyan";
    }
  } else {
    actionEl.innerText = "NONE";
    riskEl.innerText = "CLEAR";
    riskEl.className = "text-2xl font-black text-slate-400 mt-1";
  }

  renderReportLog();

  function renderReportLog() {
    reportContainer.innerHTML = '';

    if (records.length === 0) {
      reportContainer.innerHTML = `
        <div class="py-12 text-center text-slate-500">
          <p class="text-xs font-semibold">No active compliance violations require reporting in this batch.</p>
        </div>`;
      return;
    }

    records.forEach((record, index) => {
      const spacingClass = index === 0 ? 'pt-0' : 'pt-8';

      const itemCard = document.createElement('div');
      // Style formatted beautifully with cyberpunk borders on screen, clean outlines for printing
      itemCard.className = `${spacingClass} print-card space-y-4 bg-black/40 border border-slate-800 p-6 rounded-xl relative overflow-hidden`;

      itemCard.innerHTML = `
        <div class="flex flex-col sm:flex-row sm:items-center justify-between gap-2 border-b border-slate-900 pb-2">
          <div>
            <span class="text-xs font-mono font-bold text-indigo-400">${record.id}</span>
            <h3 class="text-md font-bold text-slate-200 mt-0.5 print:text-slate-900">Route: ${record.sender} &rarr; ${record.receiver}</h3>
          </div>
          <div class="text-left sm:text-right">
            <span class="text-sm font-mono font-bold block text-slate-200 print:text-slate-900">${formatINR(record.amount)}</span>
            <span class="text-[10px] font-bold uppercase tracking-wide text-slate-500">Risk Score: ${record.gemmaAnalysis.risk_score}%</span>
          </div>
        </div>

        <div class="grid grid-cols-1 md:grid-cols-2 gap-4 text-xs">
          <div>
            <span class="block text-[10px] text-slate-500 font-bold uppercase tracking-wider">Triggered Pipeline Flags:</span>
            <ul class="list-disc pl-4 mt-1 space-y-1 font-mono text-slate-400 print:text-slate-700">
              ${record.rules_triggered.map(rule => `<li>${rule}</li>`).join('')}
            </ul>
          </div>
          <div>
            <span class="block text-[10px] text-slate-500 font-bold uppercase tracking-wider">Recommended Action:</span>
            <span class="inline-block bg-slate-900 text-white font-mono px-2 py-0.5 rounded text-[10px] font-bold uppercase mt-1 tracking-wider border border-slate-800">
              ${record.gemmaAnalysis.recommended_action.replace('_', ' ')}
            </span>
          </div>
        </div>

        <div class="bg-black/50 border border-slate-850 p-4 rounded-xl relative">
          <div class="absolute top-0 right-0 w-2 h-2 border-t border-r border-cyan-500/30 print:hidden"></div>
          <div class="absolute bottom-0 left-0 w-2 h-2 border-b border-l border-cyan-500/30 print:hidden"></div>
          <span class="block text-[10px] text-cyan-400 font-bold uppercase tracking-wider mb-1.5 glow-cyan print:text-slate-800">Gemma Forensic Auditor Context</span>
          <p class="text-xs text-slate-400 leading-relaxed font-normal print:text-slate-700">
            ${record.gemmaAnalysis.explanation}
          </p>
        </div>
      `;

      reportContainer.appendChild(itemCard);
    });
  }
});