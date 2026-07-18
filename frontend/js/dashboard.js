document.addEventListener('DOMContentLoaded', () => {
  // Initialize icons
  lucide.createIcons();

  const tableBody = document.getElementById('queueTableBody');
  const gemmaCard = document.getElementById('gemmaAnalysisCard');
  const statTotal = document.getElementById('statTotal');
  const statHighRisk = document.getElementById('statHighRisk');
  const statRules = document.getElementById('statRules');
  const goToReportBtn = document.getElementById('goToReportBtn');

  let flaggedRecords = [];
  let selectedRecordId = null;

  function formatINR(amount) {
    return new Intl.NumberFormat('en-IN', {
      style: 'currency',
      currency: 'INR',
      maximumFractionDigits: 0,
    }).format(amount);
  }

  // Fetch flagged ledger items
  async function fetchFlaggedData() {
    try {
      const response = await fetch(`${API_BASE_URL}/flagged-records`);
      if (!response.ok) {
        throw new Error("Pipeline API fetch returned error states");
      }

      const data = await response.json();
      flaggedRecords = Array.isArray(data.records) ? data.records : [];
    } catch (error) {
      console.warn("Backend API offline. Clearing stale dashboard state.", error);
      flaggedRecords = [];
    }

    // Hold records in localStorage so report.html reads them directly
    localStorage.setItem('sentinel_active_records', JSON.stringify(flaggedRecords));

    renderDashboard();
  }

  // Populate UI
  function renderDashboard() {
    const total = flaggedRecords.length;
    const highRiskCount = flaggedRecords.filter(r => r.gemmaAnalysis.risk_score >= 80).length;
    const totalRules = flaggedRecords.reduce((sum, r) => sum + r.rules_triggered.length, 0);

    statTotal.innerText = total;
    statHighRisk.innerText = highRiskCount;
    statRules.innerText = totalRules;

    tableBody.innerHTML = '';

    if (total === 0) {
      tableBody.innerHTML = `
        <tr>
          <td colspan="5" class="py-12 text-center text-slate-500">
            <i data-lucide="check-circle" class="w-8 h-8 mx-auto mb-2 text-emerald-500"></i>
            All systems secure. Compliance queue cleared.
          </td>
        </tr>`;
      lucide.createIcons();
      return;
    }

    flaggedRecords.forEach((record) => {
      const score = record.gemmaAnalysis.risk_score;
      let scoreBadgeClass = 'bg-green-950/40 text-green-400 border-green-900/30';
      if (score >= 80) scoreBadgeClass = 'bg-red-950/40 text-red-400 border-red-900/30';
      else if (score >= 50) scoreBadgeClass = 'bg-yellow-950/40 text-yellow-400 border-yellow-900/30';

      const row = document.createElement('tr');
      row.className = `hover:bg-cyan-500/10 cursor-pointer transition-colors border-b border-slate-900 ${selectedRecordId === record.id ? 'bg-indigo-950/30 font-medium' : ''}`;
      
      row.innerHTML = `
        <td class="py-4 px-4 font-mono font-bold text-indigo-400">${record.id}</td>
        <td class="py-4 px-4">
          <div class="text-slate-500">From: <span class="text-slate-300 font-semibold">${record.sender}</span></div>
          <div class="text-slate-500">To: <span class="text-slate-300 font-semibold">${record.receiver}</span></div>
        </td>
        <td class="py-4 px-4 font-mono font-medium text-slate-300">${formatINR(record.amount)}</td>
        <td class="py-4 px-4">
          <div class="flex flex-wrap gap-1 max-w-[200px]">
            ${record.rules_triggered.map(r => `<span class="bg-black/40 text-slate-400 border border-slate-800 text-[10px] px-1.5 py-0.5 rounded font-medium">${r}</span>`).join('')}
          </div>
        </td>
        <td class="py-4 px-4 text-center">
          <span class="px-2.5 py-1 rounded-full text-xs font-bold border ${scoreBadgeClass}">${score}%</span>
        </td>
      `;

      row.addEventListener('click', () => {
        selectedRecordId = record.id;
        renderDashboard();
        renderGemmaAnalysis(record);
      });

      tableBody.appendChild(row);
    });

    lucide.createIcons();
  }

  // Populate Right-side Cyber HUD panel with Gemma's Reasoning
  function renderGemmaAnalysis(record) {
    let actionBadgeClass = 'bg-slate-900 text-slate-350 border border-slate-800';
    if (record.gemmaAnalysis.recommended_action === 'freeze') actionBadgeClass = 'bg-red-950/80 text-red-400 border border-red-900/50';
    else if (record.gemmaAnalysis.recommended_action === 'escalate') actionBadgeClass = 'bg-orange-950/80 text-orange-400 border border-orange-900/50';
    else if (record.gemmaAnalysis.recommended_action === 'request_documents') actionBadgeClass = 'bg-blue-950/80 text-blue-400 border border-blue-900/50';

    gemmaCard.innerHTML = `
      <div class="flex-1 space-y-5">
        <div class="flex justify-between items-center">
          <span class="text-xs font-mono font-bold text-slate-500">${record.id}</span>
          <span class="text-[10px] font-bold uppercase tracking-wider text-indigo-400 bg-indigo-950/60 border border-indigo-900/40 px-2 py-0.5 rounded">${record.gemmaAnalysis.risk_category}</span>
        </div>

        <div>
          <label class="text-[9px] text-slate-500 font-bold uppercase block mb-1 tracking-wider">Recommended Action</label>
          <span class="inline-flex items-center space-x-1.5 px-3 py-1 rounded-lg text-xs font-bold uppercase tracking-wide ${actionBadgeClass}">
            <i data-lucide="shield-alert" class="w-3.5 h-3.5"></i>
            <span>${record.gemmaAnalysis.recommended_action.replace('_', ' ')}</span>
          </span>
        </div>

        <div class="bg-black/50 border border-slate-800 p-4 rounded-xl space-y-2 relative">
          <div class="absolute top-0 right-0 w-2 h-2 border-t border-r border-cyan-400"></div>
          <div class="absolute bottom-0 left-0 w-2 h-2 border-b border-l border-cyan-400"></div>
          <label class="text-[9px] text-cyan-400 font-bold uppercase block tracking-wider">Gemma Forensic Diagnosis</label>
          <p class="text-xs text-slate-350 leading-relaxed font-normal">
            ${record.gemmaAnalysis.explanation}
          </p>
        </div>
      </div>

      <div class="pt-4 border-t border-slate-900">
        <button id="resolveBtn" class="w-full bg-gradient-to-r from-cyan-950 to-slate-950 hover:from-cyan-900 hover:to-slate-900 border border-cyan-500/30 text-cyan-400 py-3 rounded-xl text-xs font-bold tracking-widest uppercase transition flex items-center justify-center space-x-2">
          <i data-lucide="check-square" class="w-4 h-4"></i>
          <span>Approve Override &amp; Clear Flag</span>
        </button>
      </div>
    `;

    document.getElementById('resolveBtn').addEventListener('click', () => {
      resolveRecord(record.id);
    });

    lucide.createIcons();
  }

  function resolveRecord(id) {
    if (confirm(`Do you want to clear compliance flags for record ${id}?`)) {
      flaggedRecords = flaggedRecords.filter(r => r.id !== id);
      selectedRecordId = null;

      localStorage.setItem('sentinel_active_records', JSON.stringify(flaggedRecords));
      renderDashboard();
      
      gemmaCard.innerHTML = `
        <div class="flex-1 flex flex-col items-center justify-center text-center text-slate-500 py-12">
          <i data-lucide="check-circle" class="w-12 h-12 mb-3 text-emerald-500"></i>
          <p class="text-xs max-w-[200px] leading-relaxed">Alert resolved. Select another transaction item from the compliance queue.</p>
        </div>`;
      lucide.createIcons();
    }
  }

  goToReportBtn.addEventListener('click', () => {
    window.location.href = "report.html";
  });

  fetchFlaggedData();
});