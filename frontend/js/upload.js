document.addEventListener('DOMContentLoaded', () => {
  // Initialize navigation icons
  lucide.createIcons();

  const txInput = document.getElementById('transactionFile');
  const invInput = document.getElementById('invoiceFile');
  const txLabel = document.getElementById('txLabel');
  const invLabel = document.getElementById('invLabel');
  const uploadForm = document.getElementById('uploadForm');
  
  // Progress Elements
  const loadingOverlay = document.getElementById('loadingOverlay');
  const progressBarFill = document.getElementById('progressBarFill');
  const reaperWrapper = document.getElementById('reaperWrapper');
  const loadingStatusText = document.getElementById('loadingStatusText');

  // Dynamic audit status messages corresponding to visual timeline percentages
  const auditStatuses = [
    { limit: 15, text: "PARSING LEDGER SCHEMAS..." },
    { limit: 35, text: "EVALUATING STRUCTURING THRESHOLD CHECKS..." },
    { limit: 55, text: "CROSS-REFERENCING TRANSACTION TO INVOICE MATCHES..." },
    { limit: 75, text: "QUERYING GEMMA LLM EXPLAINER AGENTS..." },
    { limit: 90, text: "COMPILING THREAT VECTORS & RISK CATEGORIES..." },
    { limit: 95, text: "PACKAGING COMPLIANCE AUDIT OVERVIEWS..." }
  ];

  // Update selection titles dynamically
  txInput.addEventListener('change', (e) => {
    const file = e.target.files[0];
    txLabel.innerText = file ? file.name : "Choose transaction.csv";
  });

  invInput.addEventListener('change', (e) => {
    const file = e.target.files[0];
    invLabel.innerText = file ? file.name : "Choose invoices.csv";
  });

  // Form Submit Action
  uploadForm.addEventListener('submit', async (e) => {
    e.preventDefault();

    const txFile = txInput.files[0];
    const invFile = invInput.files[0];

    if (!txFile || !invFile) {
      alert("Please select both transaction and invoice CSV datasets.");
      return;
    }

    const formData = new FormData();
    formData.append('transaction_csv', txFile);
    formData.append('invoice_csv', invFile);

    localStorage.removeItem('sentinel_active_records');

    // Fade-in the loading screen
    loadingOverlay.classList.remove('hidden');

    let currentProgress = 0;
    
    // Smooth visual bar incremental counter
    const progressTimer = setInterval(() => {
      if (currentProgress < 95) {
        currentProgress += Math.floor(Math.random() * 4) + 2;
        if (currentProgress > 95) currentProgress = 95;
        
        updateLoadingState(currentProgress);
      }
    }, 120);

    function updateLoadingState(percent) {
      progressBarFill.style.width = `${percent}%`;
      reaperWrapper.style.left = `${percent}%`;

      const matchedStatus = auditStatuses.find(status => percent <= status.limit);
      if (matchedStatus) {
        loadingStatusText.innerText = matchedStatus.text;
      }
    }

    try {
      // Connect to your active backend engine
      const response = await fetch(`${API_BASE_URL}/upload`, {
        method: 'POST',
        body: formData
      });

      if (!response.ok) {
        const errorBody = await response.json().catch(() => ({}));
        throw new Error(errorBody.detail || 'The pipeline could not process these CSV files.');
      }

      await response.json();

      // Complete progress loop instantly on successful api return
      clearInterval(progressTimer);
      updateLoadingState(100);
      loadingStatusText.innerText = "COMPLIANCE THREAT REPORT SECURED!";
      
      setTimeout(() => {
        window.location.href = "dashboard.html";
      }, 700);

    } catch (error) {
      console.error('Upload failed:', error);
      clearInterval(progressTimer);
      loadingOverlay.classList.add('hidden');
      alert(error.message || 'Unable to reach the backend. Start the API and try again.');
    }
  });
});
