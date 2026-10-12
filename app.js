// EduPulse AI Client Controller
let allStudents = [];
let selectedStudent = null;
let currentRiskFilter = "All";
let deptChartInstance = null;
let trajectoryChartInstance = null;

// Initialize when DOM is ready
document.addEventListener("DOMContentLoaded", async () => {
  if (window.lucide) {
    lucide.createIcons();
  }
  await loadOverview();
  await loadStudents();
});

// 1. Load Overview Metrics & Charts
async function loadOverview() {
  try {
    const res = await fetch("/api/overview");
    const data = await res.json();

    // Fill KPIs
    document.getElementById("kpi-total").innerText = data.kpis.total_students;
    document.getElementById("kpi-high-risk").innerText = data.kpis.high_risk_count;
    document.getElementById("kpi-high-risk-pct").innerText = `${data.kpis.high_risk_pct}%`;
    document.getElementById("kpi-attendance").innerText = `${data.kpis.avg_attendance}%`;
    document.getElementById("kpi-gpa").innerText = data.kpis.avg_gpa;

    // Render Department Distribution Chart
    renderDeptChart(data.department_analytics);

    // Render Bottleneck Courses
    renderBottlenecks(data.bottleneck_courses);
  } catch (err) {
    console.error("Error loading overview:", err);
  }
}

function renderDeptChart(deptData) {
  const ctx = document.getElementById("deptChart").getContext("2d");
  if (deptChartInstance) {
    deptChartInstance.destroy();
  }

  const labels = deptData.map(d => {
    return d.department.replace("CSE - ", "");
  });

  const highData = deptData.map(d => d.high_risk_count);
  const totalData = deptData.map(d => d.total_students);
  const onTrackData = totalData.map((tot, i) => tot - highData[i]);

  deptChartInstance = new Chart(ctx, {
    type: "bar",
    data: {
      labels: labels,
      datasets: [
        {
          label: "Critical High Risk",
          data: highData,
          backgroundColor: "#EF4444",
          borderRadius: 6,
        },
        {
          label: "On Track / Moderate",
          data: onTrackData,
          backgroundColor: "#93C5FD",
          borderRadius: 6,
        }
      ]
    },
    options: {
      responsive: true,
      maintainAspectRatio: false,
      scales: {
        x: { stacked: true, grid: { display: false } },
        y: { stacked: true, beginAtZero: true, grid: { color: "#F1F5F9" } }
      },
      plugins: {
        legend: { position: "top", labels: { boxWidth: 12, font: { size: 11, family: "Inter" } } }
      }
    }
  });
}

function renderBottlenecks(courses) {
  const container = document.getElementById("bottlenecks-list");
  if (!courses || courses.length === 0) {
    container.innerHTML = `<div class="text-xs text-slate-400">No bottleneck warnings detected.</div>`;
    return;
  }

  container.innerHTML = courses.map(c => `
    <div class="p-2.5 rounded-lg border border-slate-100 bg-slate-50 flex items-center justify-between text-xs">
      <div>
        <div class="font-bold text-slate-900 flex items-center space-x-1.5">
          <span class="text-rose-600 font-mono">${c.code}</span>
          <span>${c.name}</span>
        </div>
        <div class="text-[11px] text-slate-500 mt-0.5">
          Avg Internal Score: <span class="font-semibold text-slate-700">${c.avg_score}%</span>
        </div>
      </div>
      <div class="text-right">
        <span class="inline-block px-2 py-0.5 rounded-full font-bold text-[10px] bg-rose-100 text-rose-700">
          ${c.struggle_rate}% at-risk
        </span>
      </div>
    </div>
  `).join("");
}

// 2. Load Students Table
async function loadStudents() {
  try {
    const res = await fetch("/api/students");
    const data = await res.json();
    allStudents = data.students;
    renderStudentTable(allStudents);
  } catch (err) {
    console.error("Error loading students:", err);
  }
}

function renderStudentTable(students) {
  const tbody = document.getElementById("studentTableBody");
  document.getElementById("matchedCount").innerText = `Showing ${students.length} students`;

  if (students.length === 0) {
    tbody.innerHTML = `<tr><td colspan="8" class="text-center py-8 text-slate-400">No students matching active filters.</td></tr>`;
    return;
  }

  tbody.innerHTML = students.map(s => {
    const risk = s.risk_assessment.level;
    let badgeClass = "bg-emerald-50 text-emerald-700 border-emerald-200";
    let badgeIcon = "check-circle";
    if (risk === "High") {
      badgeClass = "bg-rose-50 text-rose-700 border-rose-200 font-bold";
      badgeIcon = "alert-circle";
    } else if (risk === "Medium") {
      badgeClass = "bg-amber-50 text-amber-700 border-amber-200";
      badgeIcon = "alert-triangle";
    }

    const gpaDelta = s.metrics.gpa_delta;
    let deltaHtml = `<span class="text-slate-400 text-[10px]">steady</span>`;
    if (gpaDelta < 0) {
      deltaHtml = `<span class="text-rose-600 text-[10px] font-semibold flex items-center">▼ ${Math.abs(gpaDelta)}</span>`;
    } else if (gpaDelta > 0) {
      deltaHtml = `<span class="text-emerald-600 text-[10px] font-semibold flex items-center">▲ ${gpaDelta}</span>`;
    }

    const att = s.metrics.attendance_rate;
    const attColor = att < 75 ? "text-rose-600 font-bold" : "text-slate-700";

    const prob = s.risk_assessment.dropout_probability;
    const probBarColor = prob > 60 ? "bg-rose-500" : (prob > 30 ? "bg-amber-500" : "bg-emerald-500");

    return `
      <tr class="table-row-hover transition">
        <td class="py-3 px-4">
          <div class="flex items-center space-x-2.5">
            <div class="w-7 h-7 rounded-full flex items-center justify-center text-white text-[11px] font-bold" style="background-color: ${s.avatar_color}">
              ${s.name.split(" ").map(n => n[0]).join("")}
            </div>
            <div>
              <div class="font-semibold text-slate-900">${s.name}</div>
              <div class="text-[10px] text-slate-400 font-mono">${s.id}</div>
            </div>
          </div>
        </td>
        <td class="py-3 px-4">
          <div class="text-slate-800 font-medium">${s.department.replace("Engineering", "Eng.")}</div>
          <div class="text-[10px] text-slate-400">Year ${s.year} (Sem ${s.semester})</div>
        </td>
        <td class="py-3 px-4">
          <div class="font-bold text-slate-900">${s.metrics.current_gpa}</div>
          ${deltaHtml}
        </td>
        <td class="py-3 px-4">
          <span class="${attColor}">${att}%</span>
          <div class="w-16 bg-slate-100 h-1 rounded-full mt-1 overflow-hidden">
            <div class="${att < 75 ? 'bg-rose-500' : 'bg-emerald-500'} h-full" style="width: ${Math.min(100, att)}%"></div>
          </div>
        </td>
        <td class="py-3 px-4">
          <div class="text-slate-700 font-medium">${s.metrics.lms_logins_weekly} logins/wk</div>
          <div class="text-[10px] text-slate-400">${s.metrics.assignment_submission_rate}% assignments</div>
        </td>
        <td class="py-3 px-4">
          <span class="inline-flex items-center px-2 py-0.5 rounded-full text-[11px] border ${badgeClass}">
            ${risk}
          </span>
        </td>
        <td class="py-3 px-4">
          <div class="flex items-center space-x-2">
            <span class="font-mono font-bold text-slate-800">${prob}%</span>
            <div class="w-14 bg-slate-100 h-1.5 rounded-full overflow-hidden">
              <div class="${probBarColor} h-full rounded-full" style="width: ${prob}%"></div>
            </div>
          </div>
        </td>
        <td class="py-3 px-4 text-right">
          <button onclick="openStudentModal('${s.id}')" class="px-2.5 py-1.5 bg-blue-50 hover:bg-blue-100 text-blue-700 rounded-md font-semibold text-[11px] transition">
            Inspect 360°
          </button>
        </td>
      </tr>
    `;
  }).join("");

  if (window.lucide) lucide.createIcons();
}

// 3. Filter Handlers
function setRiskFilter(risk) {
  currentRiskFilter = risk;
  document.querySelectorAll(".filter-btn").forEach(btn => {
    if (btn.dataset.risk === risk) {
      btn.className = "filter-btn text-xs px-3 py-1 rounded-full font-medium transition bg-slate-900 text-white";
    } else {
      btn.className = "filter-btn text-xs px-3 py-1 rounded-full font-medium transition bg-slate-100 text-slate-600 hover:bg-slate-200";
    }
  });
  applyFilters();
}

function applyFilters() {
  const search = document.getElementById("searchInput").value.toLowerCase();
  const dept = document.getElementById("deptFilter").value;
  const lowAtt = document.getElementById("lowAttCheck").checked;

  const filtered = allStudents.filter(s => {
    const matchSearch = !search || s.name.toLowerCase().includes(search) || s.id.toLowerCase().includes(search) || s.email.toLowerCase().includes(search);
    const matchRisk = currentRiskFilter === "All" || s.risk_assessment.level === currentRiskFilter;
    const matchDept = dept === "All" || s.department === dept;
    const matchAtt = !lowAtt || s.metrics.attendance_rate < 75.0;

    return matchSearch && matchRisk && matchDept && matchAtt;
  });

  renderStudentTable(filtered);
}

// 4. Student 360° Modal
async function openStudentModal(studentId) {
  try {
    const res = await fetch(`/api/students/${studentId}`);
    const s = await res.json();
    selectedStudent = s;

    // Header Info
    const avatar = document.getElementById("modalAvatar");
    avatar.style.backgroundColor = s.avatar_color;
    avatar.innerText = s.name.split(" ").map(n => n[0]).join("");

    document.getElementById("modalName").innerText = s.name;
    document.getElementById("modalId").innerText = `ID: ${s.id}`;
    document.getElementById("modalDept").innerText = s.department;
    document.getElementById("modalSem").innerText = `Semester ${s.semester}`;
    document.getElementById("modalEmail").innerText = s.email;

    // Risk badge
    const badge = document.getElementById("modalRiskBadge");
    const risk = s.risk_assessment.level;
    badge.innerText = `${risk} Risk (${s.risk_assessment.dropout_probability}% Probability)`;
    if (risk === "High") {
      badge.className = "text-xs px-2.5 py-0.5 rounded-full font-bold bg-rose-100 text-rose-700 border border-rose-200";
    } else if (risk === "Medium") {
      badge.className = "text-xs px-2.5 py-0.5 rounded-full font-bold bg-amber-100 text-amber-700 border border-amber-200";
    } else {
      badge.className = "text-xs px-2.5 py-0.5 rounded-full font-bold bg-emerald-100 text-emerald-700 border border-emerald-200";
    }

    // XAI Root Causes
    const xaiList = document.getElementById("modalXaiList");
    xaiList.innerHTML = s.risk_assessment.top_risk_factors.map(f => `<li>${f}</li>`).join("");

    // Metrics
    document.getElementById("modalAttendance").innerText = `${s.metrics.attendance_rate}%`;
    document.getElementById("modalLabAttendance").innerText = `${s.metrics.lab_attendance}%`;
    document.getElementById("modalAssignmentRate").innerText = `${s.metrics.assignment_submission_rate}%`;
    document.getElementById("modalLmsLogins").innerText = `${s.metrics.lms_logins_weekly} visits`;
    document.getElementById("modalWellbeing").innerText = `${s.metrics.wellbeing_score} / 10 ${s.metrics.wellbeing_score <= 4 ? '(Elevated Stress Warning)' : '(Good)'}`;

    const delta = s.metrics.gpa_delta;
    document.getElementById("modalGpaDelta").innerText = delta < 0 ? `${delta} pts drop` : `+${delta} pts gain`;
    document.getElementById("modalGpaDelta").className = delta < 0 ? "text-xs font-bold text-rose-600" : "text-xs font-bold text-emerald-600";

    // Trajectory Chart
    renderTrajectoryChart(s.gpa_trajectory);

    // Enrolled Courses Table
    const cTable = document.getElementById("modalCourseTable");
    cTable.innerHTML = s.courses.map(c => `
      <tr class="table-row-hover">
        <td class="py-2.5 px-3">
          <span class="font-mono font-bold text-slate-800">${c.code}</span>
          <span class="ml-1 text-slate-700">${c.name}</span>
        </td>
        <td class="py-2.5 px-3">${c.credits}</td>
        <td class="py-2.5 px-3 font-bold ${c.current_score < 60 ? 'text-rose-600' : 'text-slate-800'}">${c.current_score}%</td>
        <td class="py-2.5 px-3 ${c.attendance < 75 ? 'text-rose-600 font-bold' : 'text-slate-700'}">${c.attendance}%</td>
        <td class="py-2.5 px-3">
          ${c.is_bottleneck ? '<span class="text-[10px] px-1.5 py-0.5 bg-rose-50 text-rose-600 border border-rose-200 rounded font-semibold">Bottleneck</span>' : '<span class="text-[10px] text-slate-400">Standard</span>'}
        </td>
      </tr>
    `).join("");

    // Reset intervention view
    document.getElementById("interventionOutput").classList.add("hidden");

    // Show modal
    document.getElementById("studentModal").classList.remove("hidden");
    if (window.lucide) lucide.createIcons();
  } catch (err) {
    console.error("Error opening student modal:", err);
  }
}

function closeStudentModal() {
  document.getElementById("studentModal").classList.add("hidden");
  selectedStudent = null;
}

function renderTrajectoryChart(history) {
  const ctx = document.getElementById("studentTrajectoryChart").getContext("2d");
  if (trajectoryChartInstance) {
    trajectoryChartInstance.destroy();
  }

  const labels = history.map(h => h.semester);
  const values = history.map(h => h.gpa);

  trajectoryChartInstance = new Chart(ctx, {
    type: "line",
    data: {
      labels: labels,
      datasets: [{
        label: "Semester GPA",
        data: values,
        borderColor: "#2563EB",
        backgroundColor: "rgba(37, 99, 235, 0.1)",
        borderWidth: 2.5,
        fill: true,
        tension: 0.3,
        pointBackgroundColor: "#2563EB",
        pointRadius: 4
      }]
    },
    options: {
      responsive: true,
      maintainAspectRatio: false,
      scales: {
        y: { min: 3.0, max: 10.0, grid: { color: "#F1F5F9" } },
        x: { grid: { display: false } }
      },
      plugins: {
        legend: { display: false }
      }
    }
  });
}

// 5. Generate AI Intervention Plan
async function generateInterventionPlan() {
  if (!selectedStudent) return;

  const btn = document.getElementById("btnGeneratePlan");
  const originalHtml = btn.innerHTML;
  btn.innerHTML = `<span class="inline-block animate-spin mr-1">⏳</span> Synthesizing Plan...`;
  btn.disabled = true;

  try {
    const res = await fetch(`/api/students/${selectedStudent.id}/intervention`, { method: "POST" });
    const data = await res.json();
    const plan = data.intervention;

    // Display Plan
    document.getElementById("planDiagnosis").innerText = plan.diagnosis_summary;

    const grid = document.getElementById("fourWeekGrid");
    grid.innerHTML = plan.four_week_plan.map(w => `
      <div class="p-3 bg-white rounded-xl border border-slate-200 shadow-sm text-xs">
        <div class="font-bold text-blue-700 flex items-center space-x-1 mb-1">
          <span>${w.week}</span>
        </div>
        <div class="font-semibold text-slate-800 mb-1.5">${w.focus}</div>
        <ul class="list-disc list-inside space-y-1 text-slate-600">
          ${w.action_items.map(a => `<li>${a}</li>`).join("")}
        </ul>
      </div>
    `).join("");

    document.getElementById("emailDraftText").value = plan.advisor_email_draft;
    document.getElementById("interventionOutput").classList.remove("hidden");
    if (window.lucide) lucide.createIcons();
  } catch (err) {
    console.error("Error generating plan:", err);
    alert("Could not generate plan. Please try again.");
  } finally {
    btn.innerHTML = originalHtml;
    btn.disabled = false;
  }
}

function copyEmailDraft() {
  const copyText = document.getElementById("emailDraftText");
  copyText.select();
  navigator.clipboard.writeText(copyText.value);
  alert("Advisor email draft copied to clipboard!");
}

// 6. What-If Simulator
function openSimulatorModal() {
  document.getElementById("simulatorModal").classList.remove("hidden");
  runSimulation();
}

function closeSimulatorModal() {
  document.getElementById("simulatorModal").classList.add("hidden");
}

async function runSimulation() {
  const att = parseFloat(document.getElementById("simAtt").value);
  const mid = parseFloat(document.getElementById("simMid").value);
  const ass = parseFloat(document.getElementById("simAss").value);
  const log = parseInt(document.getElementById("simLog").value);

  document.getElementById("simAttVal").innerText = `${att}%`;
  document.getElementById("simMidVal").innerText = `${mid}%`;
  document.getElementById("simAssVal").innerText = `${ass}%`;
  document.getElementById("simLogVal").innerText = `${log} visits`;

  try {
    const res = await fetch("/api/simulate", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({
        attendance_rate: att,
        lab_attendance: att,
        assignment_submission_rate: ass,
        lms_logins_weekly: log,
        midterm_avg: mid,
        current_gpa: (mid / 10),
        gpa_delta: 0.0,
        wellbeing_score: 7,
        fee_overdue: false,
        first_gen: false
      })
    });
    const data = await res.json();

    const box = document.getElementById("simResultBox");
    const levelEl = document.getElementById("simLevel");
    const probEl = document.getElementById("simProb");
    const badgeEl = document.getElementById("simBadge");

    levelEl.innerText = `${data.level} Risk`;
    probEl.innerText = `(${data.dropout_probability}% Dropout Risk)`;

    if (data.level === "High") {
      box.className = "mt-4 p-4 rounded-xl border border-rose-200 bg-rose-50 flex items-center justify-between";
      levelEl.className = "text-lg font-bold text-rose-700";
      badgeEl.className = "px-3 py-1 bg-rose-600 text-white text-xs font-bold rounded-lg shadow-sm";
      badgeEl.innerText = "Critical Action Needed";
    } else if (data.level === "Medium") {
      box.className = "mt-4 p-4 rounded-xl border border-amber-200 bg-amber-50 flex items-center justify-between";
      levelEl.className = "text-lg font-bold text-amber-700";
      badgeEl.className = "px-3 py-1 bg-amber-500 text-white text-xs font-bold rounded-lg shadow-sm";
      badgeEl.innerText = "Targeted Coaching Required";
    } else {
      box.className = "mt-4 p-4 rounded-xl border border-emerald-200 bg-emerald-50 flex items-center justify-between";
      levelEl.className = "text-lg font-bold text-emerald-700";
      badgeEl.className = "px-3 py-1 bg-emerald-600 text-white text-xs font-bold rounded-lg shadow-sm";
      badgeEl.innerText = "Student On Track";
    }
  } catch (err) {
    console.error("Simulation error:", err);
  }
}

// 7. AI Copilot Drawer
function toggleCopilot() {
  const drawer = document.getElementById("copilotDrawer");
  drawer.classList.toggle("translate-x-full");
}

async function askCopilot(question) {
  document.getElementById("copilotInput").value = question;
  await handleCopilotSubmit(new Event("submit"));
}

async function handleCopilotSubmit(e) {
  e.preventDefault();
  const input = document.getElementById("copilotInput");
  const query = input.value.trim();
  if (!query) return;

  const msgs = document.getElementById("copilotMessages");

  // Append user bubble
  msgs.innerHTML += `
    <div class="flex justify-end">
      <div class="bg-blue-600 text-white p-2.5 rounded-xl max-w-[85%] rounded-br-none">
        ${query}
      </div>
    </div>
  `;
  input.value = "";
  msgs.scrollTop = msgs.scrollHeight;

  // Append loading bubble
  const loaderId = "loader-" + Date.now();
  msgs.innerHTML += `
    <div id="${loaderId}" class="flex justify-start">
      <div class="bg-slate-100 text-slate-500 p-2.5 rounded-xl max-w-[85%] rounded-bl-none animate-pulse">
        Thinking...
      </div>
    </div>
  `;
  msgs.scrollTop = msgs.scrollHeight;

  try {
    const res = await fetch("/api/copilot/chat", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ query: query })
    });
    const data = await res.json();
    document.getElementById(loaderId)?.remove();

    let contentHtml = `<div class="font-medium mb-1 whitespace-pre-line">${data.summary}</div>`;
    if (data.students && data.students.length > 0) {
      contentHtml += `
        <div class="mt-2 space-y-1.5 border-t border-slate-200 pt-2">
          ${data.students.map(s => `
            <div class="flex items-center justify-between text-[11px] bg-white p-1.5 rounded border border-slate-200">
              <span class="font-bold text-slate-800">${s.name} (${s.id})</span>
              <span class="font-mono text-rose-600 font-bold">${s.metrics.attendance_rate}% att</span>
            </div>
          `).join("")}
        </div>
      `;
    }

    msgs.innerHTML += `
      <div class="flex justify-start">
        <div class="bg-slate-100 text-slate-800 p-2.5 rounded-xl max-w-[85%] rounded-bl-none border border-slate-200">
          ${contentHtml}
        </div>
      </div>
    `;
    msgs.scrollTop = msgs.scrollHeight;
  } catch (err) {
    document.getElementById(loaderId)?.remove();
    msgs.innerHTML += `
      <div class="flex justify-start">
        <div class="bg-rose-50 text-rose-700 p-2.5 rounded-xl max-w-[85%] border border-rose-200">
          Error processing copilot query. Please try again.
        </div>
      </div>
    `;
  }
}
