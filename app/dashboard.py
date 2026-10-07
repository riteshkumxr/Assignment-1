DASHBOARD_HTML = """<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="UTF-8">
  <meta name="viewport" content="width=device-width, initial-scale=1.0">
  <title>Bulk Certificate Generator - Live Dashboard</title>
  <script src="https://cdn.tailwindcss.com"></script>
  <link rel="stylesheet" href="https://cdnjs.cloudflare.com/ajax/libs/font-awesome/6.4.0/css/all.min.css">
  <style>
    @keyframes pulse-subtle { 0%, 100% { opacity: 1; } 50% { opacity: 0.85; } }
    .pulse-custom { animation: pulse-subtle 2s infinite ease-in-out; }
  </style>
</head>
<body class="bg-slate-50 text-slate-800 min-h-screen">
  <!-- Navbar -->
  <header class="bg-slate-900 border-b border-slate-800 text-white shadow-md">
    <div class="max-w-7xl mx-auto px-4 py-4 flex items-center justify-between">
      <div class="flex items-center space-x-3">
        <div class="w-10 h-10 rounded-lg bg-amber-500 flex items-center justify-center text-slate-950 font-bold text-xl shadow">
          <i class="fa-solid fa-award"></i>
        </div>
        <div>
          <h1 class="text-xl font-bold tracking-tight">CertGen Pro</h1>
          <p class="text-xs text-slate-400">Bulk Certificate Generation & Verification Engine</p>
        </div>
      </div>
      <div class="flex items-center space-x-3">
        <a href="/docs" target="_blank" class="px-3 py-1.5 text-xs font-semibold bg-slate-800 hover:bg-slate-700 text-slate-200 rounded-md border border-slate-700 transition flex items-center gap-1.5">
          <i class="fa-solid fa-book"></i> Interactive Docs (/docs)
        </a>
        <a href="/health" target="_blank" class="px-3 py-1.5 text-xs font-semibold bg-emerald-950/60 text-emerald-400 border border-emerald-800/60 rounded-md flex items-center gap-1.5">
          <span class="w-2 h-2 rounded-full bg-emerald-500 animate-ping"></span> Live & Healthy
        </a>
      </div>
    </div>
  </header>

  <!-- Main Container -->
  <main class="max-w-7xl mx-auto px-4 py-8 grid grid-cols-1 lg:grid-cols-12 gap-8">
    
    <!-- Left Column: Generator Form -->
    <div class="lg:col-span-5 space-y-6">
      <div class="bg-white rounded-xl shadow-sm border border-slate-200 p-6">
        <h2 class="text-lg font-bold text-slate-900 mb-1 flex items-center gap-2">
          <i class="fa-solid fa-sliders text-amber-600"></i> Job Configuration
        </h2>
        <p class="text-xs text-slate-500 mb-5">Define the event credentials and recipient batch.</p>

        <form id="generateForm" class="space-y-4">
          <div>
            <label class="block text-xs font-semibold text-slate-700 mb-1 uppercase tracking-wider">Event / Course Title</label>
            <input type="text" id="eventTitle" required class="w-full text-sm px-3.5 py-2.5 bg-slate-50 border border-slate-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-amber-500 focus:bg-white transition" value="Advanced Cloud Architecture & Systems Design">
          </div>

          <div>
            <label class="block text-xs font-semibold text-slate-700 mb-1 uppercase tracking-wider">Issuing Organization</label>
            <input type="text" id="issuerName" required class="w-full text-sm px-3.5 py-2.5 bg-slate-50 border border-slate-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-amber-500 focus:bg-white transition" value="Google DeepMind Academy">
          </div>

          <div>
            <label class="block text-xs font-semibold text-slate-700 mb-1 uppercase tracking-wider">Issue Date</label>
            <input type="date" id="issueDate" class="w-full text-sm px-3.5 py-2.5 bg-slate-50 border border-slate-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-amber-500 focus:bg-white transition">
          </div>

          <div>
            <div class="flex items-center justify-between mb-1">
              <label class="block text-xs font-semibold text-slate-700 uppercase tracking-wider">Recipients JSON</label>
              <button type="button" onclick="loadSampleData()" class="text-xs text-amber-600 hover:text-amber-700 font-medium">Reset Sample</button>
            </div>
            <textarea id="recipientsJson" rows="8" required class="w-full text-xs font-mono px-3.5 py-2.5 bg-slate-900 text-slate-200 border border-slate-700 rounded-lg focus:outline-none focus:ring-2 focus:ring-amber-500 transition"></textarea>
            <p class="text-[11px] text-slate-500 mt-1">Accepts a JSON array of recipients with name, email, and custom metadata.</p>
          </div>

          <button type="submit" id="submitBtn" class="w-full py-3 px-4 bg-amber-500 hover:bg-amber-600 text-slate-950 font-bold rounded-lg shadow-sm hover:shadow transition flex items-center justify-center gap-2">
            <i class="fa-solid fa-bolt"></i> Generate Certificates in Bulk
          </button>
        </form>
      </div>
    </div>

    <!-- Right Column: Status & Real-time Progress -->
    <div class="lg:col-span-7 space-y-6">
      
      <!-- Progress Card -->
      <div id="progressCard" class="bg-white rounded-xl shadow-sm border border-slate-200 p-6 hidden">
        <div class="flex items-center justify-between mb-4">
          <div>
            <h2 class="text-base font-bold text-slate-900 flex items-center gap-2">
              <i class="fa-solid fa-spinner fa-spin text-amber-500" id="statusSpinner"></i>
              Job Status: <span id="jobStatusBadge" class="px-2.5 py-0.5 rounded-full text-xs font-bold uppercase tracking-wide bg-amber-100 text-amber-800">PENDING</span>
            </h2>
            <p class="text-xs text-slate-500 mt-0.5">Job ID: <span id="displayJobId" class="font-mono text-slate-700"></span></p>
          </div>
          <div id="zipDownloadContainer" class="hidden">
            <a id="zipDownloadBtn" href="#" class="px-3.5 py-2 bg-emerald-600 hover:bg-emerald-700 text-white text-xs font-bold rounded-lg shadow transition flex items-center gap-2">
              <i class="fa-solid fa-file-zipper"></i> Download ZIP
            </a>
          </div>
        </div>

        <!-- Metric Badges -->
        <div class="grid grid-cols-4 gap-3 mb-4">
          <div class="bg-slate-50 border border-slate-200 rounded-lg p-3 text-center">
            <span class="block text-xs font-semibold text-slate-500 uppercase">Total</span>
            <span id="metricTotal" class="text-xl font-bold text-slate-800">0</span>
          </div>
          <div class="bg-blue-50 border border-blue-200 rounded-lg p-3 text-center">
            <span class="block text-xs font-semibold text-blue-600 uppercase">Processed</span>
            <span id="metricProcessed" class="text-xl font-bold text-blue-800">0</span>
          </div>
          <div class="bg-emerald-50 border border-emerald-200 rounded-lg p-3 text-center">
            <span class="block text-xs font-semibold text-emerald-600 uppercase">Success</span>
            <span id="metricSuccess" class="text-xl font-bold text-emerald-800">0</span>
          </div>
          <div class="bg-rose-50 border border-rose-200 rounded-lg p-3 text-center">
            <span class="block text-xs font-semibold text-rose-600 uppercase">Failed</span>
            <span id="metricFailed" class="text-xl font-bold text-rose-800">0</span>
          </div>
        </div>

        <!-- Progress Bar -->
        <div class="w-full bg-slate-200 rounded-full h-3 mb-2 overflow-hidden">
          <div id="progressBar" class="bg-amber-500 h-3 rounded-full transition-all duration-300" style="width: 0%"></div>
        </div>
        <p id="progressPercent" class="text-xs text-right text-slate-500 font-medium">0%</p>

        <!-- Recipients Table -->
        <div class="mt-6 border-t border-slate-100 pt-5">
          <h3 class="text-xs font-bold uppercase tracking-wider text-slate-700 mb-3 flex items-center justify-between">
            <span>Recipient Certificates</span>
            <span id="recipientCount" class="text-slate-400 font-normal"></span>
          </h3>
          <div class="overflow-x-auto max-h-96 border border-slate-200 rounded-lg">
            <table class="w-full text-left text-xs">
              <thead class="bg-slate-100 text-slate-600 uppercase border-b border-slate-200 font-semibold sticky top-0">
                <tr>
                  <th class="px-3 py-2.5">Recipient</th>
                  <th class="px-3 py-2.5">Email</th>
                  <th class="px-3 py-2.5">Status</th>
                  <th class="px-3 py-2.5 text-right">Actions</th>
                </tr>
              </thead>
              <tbody id="recipientsTableBody" class="divide-y divide-slate-100">
                <!-- Injected via JavaScript -->
              </tbody>
            </table>
          </div>
        </div>

      </div>

      <!-- Welcome Placeholder Card -->
      <div id="placeholderCard" class="bg-white rounded-xl shadow-sm border border-slate-200 p-10 text-center">
        <div class="w-16 h-16 mx-auto rounded-full bg-amber-100 text-amber-600 flex items-center justify-center text-2xl mb-4">
          <i class="fa-solid fa-file-pdf"></i>
        </div>
        <h3 class="text-base font-bold text-slate-800">Ready to Generate</h3>
        <p class="text-xs text-slate-500 max-w-sm mx-auto mt-1 mb-5">
          Submit the form on the left to trigger the bulk generator. You will see live real-time progress and download links here.
        </p>
        <button onclick="document.getElementById('generateForm').dispatchEvent(new Event('submit'))" class="px-4 py-2 bg-slate-900 hover:bg-slate-800 text-white text-xs font-semibold rounded-lg shadow-sm transition">
          Generate Demo Batch (3 Certificates)
        </button>
      </div>

    </div>
  </main>

  <script>
    const sampleRecipients = [
      {
        "name": "Ada Lovelace",
        "email": "ada.lovelace@computing.org",
        "custom_data": {"grade": "A+", "honors": "Pioneer of Computation"}
      },
      {
        "name": "Alan Turing",
        "email": "alan.turing@bletchley.org",
        "custom_data": {"grade": "A+", "distinction": "First Class"}
      },
      {
        "name": "Grace Hopper",
        "email": "grace.hopper@navy.mil",
        "custom_data": {"grade": "A", "credits": "4.0"}
      }
    ];

    function loadSampleData() {
      document.getElementById('recipientsJson').value = JSON.stringify(sampleRecipients, null, 2);
    }

    // Set today's date
    document.getElementById('issueDate').value = new Date().toISOString().split('T')[0];
    loadSampleData();

    let activePollingInterval = null;

    document.getElementById('generateForm').addEventListener('submit', async function(e) {
      e.preventDefault();
      const submitBtn = document.getElementById('submitBtn');
      submitBtn.disabled = true;
      submitBtn.innerHTML = '<i class="fa-solid fa-circle-notch fa-spin"></i> Submitting Batch...';

      let recipients;
      try {
        recipients = JSON.parse(document.getElementById('recipientsJson').value);
      } catch (err) {
        alert("Invalid JSON format in recipients field: " + err.message);
        submitBtn.disabled = false;
        submitBtn.innerHTML = '<i class="fa-solid fa-bolt"></i> Generate Certificates in Bulk';
        return;
      }

      const payload = {
        event_title: document.getElementById('eventTitle').value.trim(),
        issuer_name: document.getElementById('issuerName').value.trim(),
        issue_date: document.getElementById('issueDate').value,
        recipients: recipients
      };

      try {
        const response = await fetch('/api/v1/jobs', {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify(payload)
        });

        if (!response.ok) {
          const errorData = await response.json();
          alert("Submission error: " + JSON.stringify(errorData.detail || errorData));
          submitBtn.disabled = false;
          submitBtn.innerHTML = '<i class="fa-solid fa-bolt"></i> Generate Certificates in Bulk';
          return;
        }

        const job = await response.json();
        startPolling(job.id);

      } catch (err) {
        alert("Network error: " + err.message);
      } finally {
        submitBtn.disabled = false;
        submitBtn.innerHTML = '<i class="fa-solid fa-bolt"></i> Generate Certificates in Bulk';
      }
    });

    function startPolling(jobId) {
      if (activePollingInterval) clearInterval(activePollingInterval);

      document.getElementById('placeholderCard').classList.add('hidden');
      document.getElementById('progressCard').classList.remove('hidden');
      document.getElementById('displayJobId').textContent = jobId;

      pollJob(jobId);
      activePollingInterval = setInterval(() => pollJob(jobId), 700);
    }

    async function pollJob(jobId) {
      try {
        const res = await fetch(`/api/v1/jobs/${jobId}`);
        if (!res.ok) return;

        const job = await res.json();

        // Update counts
        document.getElementById('metricTotal').textContent = job.total_recipients;
        document.getElementById('metricProcessed').textContent = job.processed_count;
        document.getElementById('metricSuccess').textContent = job.success_count;
        document.getElementById('metricFailed').textContent = job.failed_count;

        // Progress bar
        const pct = job.total_recipients > 0 ? Math.round((job.processed_count / job.total_recipients) * 100) : 0;
        document.getElementById('progressBar').style.width = pct + '%';
        document.getElementById('progressPercent').textContent = pct + '%';

        // Badge & Spinner
        const badge = document.getElementById('jobStatusBadge');
        badge.textContent = job.status;
        const spinner = document.getElementById('statusSpinner');

        if (job.status === 'COMPLETED') {
          badge.className = 'px-2.5 py-0.5 rounded-full text-xs font-bold uppercase tracking-wide bg-emerald-100 text-emerald-800';
          spinner.className = 'fa-solid fa-circle-check text-emerald-600';
          clearInterval(activePollingInterval);
        } else if (job.status === 'PARTIALLY_COMPLETED') {
          badge.className = 'px-2.5 py-0.5 rounded-full text-xs font-bold uppercase tracking-wide bg-amber-100 text-amber-800';
          spinner.className = 'fa-solid fa-triangle-exclamation text-amber-600';
          clearInterval(activePollingInterval);
        } else if (job.status === 'FAILED') {
          badge.className = 'px-2.5 py-0.5 rounded-full text-xs font-bold uppercase tracking-wide bg-rose-100 text-rose-800';
          spinner.className = 'fa-solid fa-circle-xmark text-rose-600';
          clearInterval(activePollingInterval);
        } else {
          badge.className = 'px-2.5 py-0.5 rounded-full text-xs font-bold uppercase tracking-wide bg-blue-100 text-blue-800';
          spinner.className = 'fa-solid fa-spinner fa-spin text-blue-600';
        }

        // ZIP button
        const zipContainer = document.getElementById('zipDownloadContainer');
        const zipBtn = document.getElementById('zipDownloadBtn');
        if (job.download_zip_url) {
          zipContainer.classList.remove('hidden');
          zipBtn.href = job.download_zip_url;
        } else {
          zipContainer.classList.add('hidden');
        }

        // Render Table
        renderTable(job.recipients);

      } catch (e) {
        console.error("Polling error:", e);
      }
    }

    function renderTable(recipients) {
      const tbody = document.getElementById('recipientsTableBody');
      tbody.innerHTML = '';

      if (!recipients || recipients.length === 0) {
        tbody.innerHTML = '<tr><td colspan="4" class="px-3 py-4 text-center text-slate-400">Waiting for recipients...</td></tr>';
        return;
      }

      recipients.forEach(r => {
        const tr = document.createElement('tr');
        tr.className = "hover:bg-slate-50/80 transition";

        let statusBadge = '';
        let actionBtn = '';

        if (r.status === 'COMPLETED') {
          statusBadge = '<span class="inline-flex items-center px-2 py-0.5 rounded text-[11px] font-semibold bg-emerald-100 text-emerald-800"><i class="fa-solid fa-check mr-1"></i> Completed</span>';
          actionBtn = `<a href="${r.download_url}" target="_blank" class="px-2.5 py-1 bg-slate-900 hover:bg-slate-800 text-white rounded font-medium text-[11px] shadow-sm transition inline-flex items-center gap-1"><i class="fa-solid fa-download"></i> PDF</a>`;
        } else if (r.status === 'FAILED') {
          statusBadge = `<span class="inline-flex items-center px-2 py-0.5 rounded text-[11px] font-semibold bg-rose-100 text-rose-800" title="${r.error_message || ''}"><i class="fa-solid fa-xmark mr-1"></i> Failed</span>`;
          actionBtn = `<span class="text-[11px] text-rose-600 font-mono" title="${r.error_message || ''}">Error</span>`;
        } else {
          statusBadge = '<span class="inline-flex items-center px-2 py-0.5 rounded text-[11px] font-semibold bg-blue-100 text-blue-800"><i class="fa-solid fa-spinner fa-spin mr-1"></i> Working</span>';
          actionBtn = `<span class="text-[11px] text-slate-400">Pending</span>`;
        }

        tr.innerHTML = `
          <td class="px-3 py-2.5 font-medium text-slate-900">${r.recipient_name}</td>
          <td class="px-3 py-2.5 text-slate-600 font-mono text-[11px]">${r.recipient_email}</td>
          <td class="px-3 py-2.5">${statusBadge}</td>
          <td class="px-3 py-2.5 text-right">${actionBtn}</td>
        `;
        tbody.appendChild(tr);
      });
    }
  </script>
</body>
</html>
"""
