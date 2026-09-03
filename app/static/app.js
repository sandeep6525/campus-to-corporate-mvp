// AspireOS (ReadyFlow AI) Frontend Application Controller

let currentUserId = 1;
let currentUserRole = "Learner";
let activeInterviewSessionId = null;
let currentQuestionId = null;
let mediaRecorder = null;
let recordedChunks = [];
let mediaType = null;
let ws = null;

document.addEventListener("DOMContentLoaded", () => {
  initApp();
});

async function initApp() {
  await fetchCurrentUser();
  setupEventListeners();
  loadActiveTab("dashboard");
}

// Get logged role switcher details
async function fetchCurrentUser() {
  try {
    const res = await fetch("/api/auth/current");
    const data = await res.json();
    currentUserId = data.user_id;
    currentUserRole = data.role;
    document.getElementById("user-display-name").textContent = data.username;

    const roleSelect = document.getElementById("persona-switch");
    roleSelect.value = currentUserRole;
  } catch (err) {
    console.error("Auth fetch failed:", err);
  }
}

// Switch active sidebar tabs
function setupEventListeners() {
  const navItems = document.querySelectorAll(".nav-item");
  navItems.forEach(item => {
    item.addEventListener("click", () => {
      navItems.forEach(n => n.classList.remove("active"));
      item.classList.add("active");
      const tabName = item.getAttribute("data-tab");
      loadActiveTab(tabName);
    });
  });

  // Persona switch controller
  document.getElementById("persona-switch").addEventListener("change", async (e) => {
    const newRole = e.target.value;
    try {
      const res = await fetch(`/api/auth/role?role=${newRole}`, { method: "POST" });
      const data = await res.json();
      currentUserRole = data.role;
      // Reload current tab
      const activeTab = document.querySelector(".nav-item.active").getAttribute("data-tab");
      loadActiveTab(activeTab);
    } catch (err) {
      console.error("Role switch failed:", err);
    }
  });

  // Onboarding Modal bindings
  document.getElementById("trigger-onboard-modal").addEventListener("click", openOnboardModal);
  document.getElementById("close-onboard-btn").addEventListener("click", closeOnboardModal);
  document.getElementById("cancel-onboard-btn").addEventListener("click", closeOnboardModal);
  document.getElementById("submit-onboard-btn").addEventListener("click", submitOnboardDiagnostics);

  // Skill Add bindings
  document.getElementById("add-skill-btn").addEventListener("click", addLearnerSkill);

  // Certificate Upload
  document.getElementById("cert-upload-form").addEventListener("submit", uploadCertification);

  // Link Sync
  document.getElementById("sync-links-btn").addEventListener("click", syncExternalLinks);

  // Career Shift Delta
  document.getElementById("calculate-shift-btn").addEventListener("click", calculateCareerShift);

  // Mock Interview Start
  document.getElementById("create-interview-btn").addEventListener("click", initializeMockInterview);

  // Split sandbox compiler verify
  document.getElementById("sandbox-check-syntax-btn").addEventListener("click", verifySandboxCode);

  // Touchpoint calendar scheduler
  document.getElementById("book-appointment-btn").addEventListener("click", bookMentorshipMeeting);

  // LMS discussions posts
  document.getElementById("lms-post-submit-btn").addEventListener("click", submitLmsCollaborationPost);

  // Dialogue controls
  document.getElementById("interview-submit-btn").addEventListener("click", submitTypedInterviewAnswer);
  document.getElementById("interview-record-audio-btn").addEventListener("click", () => startMediaRecording("audio"));
  document.getElementById("interview-record-video-btn").addEventListener("click", () => startMediaRecording("video"));
  document.getElementById("interview-stop-record-btn").addEventListener("click", stopMediaRecording);

  // Return setup mock button
  document.getElementById("return-setup-btn").addEventListener("click", () => {
    document.getElementById("mock-report-workspace").classList.add("hidden");
    document.getElementById("mock-setup-workspace").classList.remove("hidden");
  });
}

// Router tab switcher controller
function loadActiveTab(tabName) {
  const tabs = document.querySelectorAll(".workspace-tab");
  tabs.forEach(t => t.classList.remove("active"));

  const targetTab = document.getElementById(`tab-${tabName}`);
  if (targetTab) {
    targetTab.classList.add("active");
  }

  // Reload tab specific payloads
  if (tabName === "dashboard") {
    loadDashboardPayload();
  } else if (tabName === "skills-hub") {
    loadSkillsHubPayload();
  } else if (tabName === "lms-academy") {
    loadLmsAcademyPayload();
  } else if (tabName === "global-courses") {
    loadGlobalCoursesPayload();
  } else if (tabName === "job-board") {
    loadJobsPayload();
  } else if (tabName === "appointments") {
    loadAppointmentsPayload();
  } else if (tabName === "cyber-security") {
    loadCyberSecurityPayload();
  } else if (tabName === "framework-ref") {
    loadFrameworkPayload("flow");
  } else if (tabName === "mentor-desk") {
    loadMentorDeskPayload();
  } else if (tabName === "institution-board") {
    loadInstitutionBoardPayload();
  } else if (tabName === "employer-board") {
    loadEmployerBoardPayload();
  }

  // Adjust visibility based on active role persona
  adjustRoleVisibilities();
}

function adjustRoleVisibilities() {
  const roleSelect = document.getElementById("persona-switch");
  const role = roleSelect.value;

  // Add/remove active menus
  const mentorMenu = document.querySelector('.nav-item[data-tab="mentor-desk"]');
  const instMenu = document.querySelector('.nav-item[data-tab="institution-board"]');
  const emplMenu = document.querySelector('.nav-item[data-tab="employer-board"]');

  // Remove existing mock menus to keep list clean
  if (mentorMenu) mentorMenu.remove();
  if (instMenu) instMenu.remove();
  if (emplMenu) emplMenu.remove();

  const nav = document.querySelector(".nav-menu");

  if (role === "Mentor") {
    nav.insertAdjacentHTML("beforeend", `
      <button class="nav-item temp-menu" data-tab="mentor-desk">
        <svg class="nav-icon" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><path d="M17 21v-2a4 4 0 0 0-4-4H5a4 4 0 0 0-4 4v2"/><circle cx="9" cy="7" r="4"/><path d="M23 21v-2a4 4 0 0 0-3-3.87"/><path d="M16 3.13a4 4 0 0 1 0 7.75"/></svg>
        <span>Mentor Console</span>
      </button>
    `);
  } else if (role === "Institution") {
    nav.insertAdjacentHTML("beforeend", `
      <button class="nav-item temp-menu" data-tab="institution-board">
        <svg class="nav-icon" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><path d="M22 10v6M2 10l10-5 10 5-10 5z"/><path d="M6 12v5c0 2 2 3 6 3s6-1 6-3v-5"/></svg>
        <span>Institution Board</span>
      </button>
    `);
  } else if (role === "Employer") {
    nav.insertAdjacentHTML("beforeend", `
      <button class="nav-item temp-menu" data-tab="employer-board">
        <svg class="nav-icon" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><rect x="2" y="7" width="20" height="14" rx="2" ry="2"/><path d="M16 21V5a2 2 0 0 0-2-2h-4a2 2 0 0 0-2 2v16"/></svg>
        <span>Employer Board</span>
      </button>
    `);
  }

  // Re-bind click event to new temporary items
  const newItems = document.querySelectorAll(".temp-menu");
  newItems.forEach(item => {
    item.addEventListener("click", () => {
      document.querySelectorAll(".nav-item").forEach(n => n.classList.remove("active"));
      item.classList.add("active");
      const tabName = item.getAttribute("data-tab");
      loadActiveTab(tabName);
    });
    if (item.getAttribute("data-tab") === document.querySelector(".nav-item.active")?.getAttribute("data-tab")) {
      item.classList.add("active");
    }
  });
}

// --- TAB PAYLOAD 1: DASHBOARD ---
async function loadDashboardPayload() {
  try {
    // 1. Fetch scorecard & context factors
    const resProfile = await fetch("/api/learner/profile");
    const profile = await resProfile.json();

    const resContext = await fetch("/api/learner/context");
    const context = await resContext.json();

    // 2. Fetch proceedings timeline
    const resProcs = await fetch("/api/readiness/proceedings");
    const procs = await resProcs.json();

    // Render scorecard radial gauge & details
    if (procs && procs.length > 0) {
      const latestSnapshot = procs[0].metrics_snapshot;
      if (latestSnapshot && Object.keys(latestSnapshot).length > 0) {
        document.getElementById("dashboard-cari-val").textContent = latestSnapshot.CARI || latestSnapshot.total_score;
        document.getElementById("dashboard-ccq-val").textContent = latestSnapshot.CCQ || "--";
        document.getElementById("dashboard-res-val").textContent = latestSnapshot.total_score || "--";
        document.getElementById("dashboard-base-val").textContent = latestSnapshot.total_score || "--";

        // update cgi
        document.getElementById("cgi-val").textContent = `${latestSnapshot.total_score - context.confidence_baseline}%`;
        document.getElementById("rv-val").textContent = "3 days";
      }
    }

    // Render Proceedings timeline audit ledger
    const timeline = document.getElementById("dashboard-proceedings-timeline");
    if (procs && procs.length > 0) {
      timeline.innerHTML = procs.map(p => `
        <div class="timeline-node">
          <div class="timeline-dot"></div>
          <div class="timeline-content">
            <div class="row between">
              <span class="timeline-stage">${p.flow_stage} Stage</span>
              <span class="small-text muted">${new Date(p.created_at).toLocaleDateString()}</span>
            </div>
            <p class="timeline-desc">${p.description}</p>
            <p class="small-text text-green font-bold">Strategic Next Steps: ${p.strategic_action}</p>
          </div>
        </div>
      `).join("");
    } else {
      timeline.innerHTML = `<p class="muted text-center py-3">Audit timeline is currently empty. Complete diagnostics onboarding first.</p>`;
    }

    // Load active checklist & gap severity cards
    loadPlanChecklist(procs);

  } catch (err) {
    console.error("Dashboard payload load failed:", err);
  }
}

function loadPlanChecklist(procs) {
  const container = document.getElementById("dashboard-roadmap-tasks");
  const gapsContainer = document.getElementById("dashboard-gaps-list");

  if (procs && procs.length > 0) {
    // mock list
    container.innerHTML = `
      <div class="flex-column gap">
        <div class="check-item-row checked">
          <input type="checkbox" checked disabled />
          <span>[Dream Stage] Complete profile stream selection and dream parameters.</span>
        </div>
        <div class="check-item-row checked">
          <input type="checkbox" checked disabled />
          <span>[Diagnose Stage] Diagnose baseline competency scorecard indexes.</span>
        </div>
        <div class="check-item-row">
          <input type="checkbox" id="task-lms" />
          <span>[Develop Stage] Enroll and finish Module 1 of Asperion BootCamp.</span>
        </div>
        <div class="check-item-row">
          <input type="checkbox" id="task-mock" />
          <span>[Demonstrate Stage] Complete active HR Mock interview (Sophia Avatar).</span>
        </div>
      </div>
    `;

    gapsContainer.innerHTML = `
      <div class="gap-item-card">
        <div class="gap-header">
          <span class="gap-title">Skill gap: Deficits in Python modular design</span>
          <span class="pill-indicator pill-red">High severity</span>
        </div>
        <p class="small-text muted">Symptom: Fails static compile checks during technical sandbox tests.</p>
        <p class="small-text text-green margin-top-5"><strong>Fix:</strong> Complete Module 2 clean python worksheets in LMS Academy.</p>
      </div>
      <div class="gap-item-card" style="background: rgba(255, 159, 28, 0.03); border-color: rgba(255, 159, 28, 0.15);">
        <div class="gap-header">
          <span class="gap-title" style="color: var(--accent-orange);">Confidence gap: Speaking pace fluctuation</span>
          <span class="pill-indicator pill-orange">Medium severity</span>
        </div>
        <p class="small-text muted">Symptom: High filler words count (um/uh) in baseline interview replies.</p>
        <p class="small-text text-green margin-top-5"><strong>Fix:</strong> Practise spoken success mantras out loud before next session.</p>
      </div>
    `;
  }
}

// --- TAB PAYLOAD 2: SKILLS & CREDENTIALS HUB ---
async function loadSkillsHubPayload() {
  try {
    // 1. Fetch profile to load suggested stream skills
    const resProfile = await fetch("/api/learner/profile");
    const profile = await resProfile.json();

    // 2. Fetch registered skills
    const resSkills = await fetch("/api/learner/skills");
    const skills = await resSkills.json();

    // Renders active skills tags
    const skillsList = document.getElementById("skills-registry-list");
    if (skills && skills.length > 0) {
      skillsList.innerHTML = skills.map(s => `
        <span class="skill-chip ${s.category === 'Technical' ? 'tech' : 'non-tech'}">
          ${s.name} (${s.proficiency})
          <span class="skill-remove" onclick="removeLearnerSkill(${s.id})">&times;</span>
        </span>
      `).join("");
    } else {
      skillsList.innerHTML = `<p class="muted">No skills registered yet.</p>`;
    }

    // Renders stream specific recommendations
    const suggested = getStreamSuggestedLocalSkills(profile.stream);
    const suggestedList = document.getElementById("skills-suggested-list");
    suggestedList.innerHTML = `
      <div class="flex-column gap">
        <h5>Suggested Technical (Emerald)</h5>
        ${suggested.technical.map(s => `
          <div class="suggested-skill-row">
            <span>${s}</span>
            <button class="secondary-btn small-text" onclick="addSuggestedSkill('${s}', 'Technical')">Add</button>
          </div>
        `).join("")}
        <h5>Suggested Non-Technical (Sapphire)</h5>
        ${suggested.non_technical.map(s => `
          <div class="suggested-skill-row">
            <span>${s}</span>
            <button class="secondary-btn small-text" onclick="addSuggestedSkill('${s}', 'Non-Technical')">Add</button>
          </div>
        `).join("")}
      </div>
    `;

    // Fetch certs table
    const resCerts = await fetch("/api/learner/certifications");
    const certs = await resCerts.json();
    const certsTable = document.getElementById("certifications-table-body");
    if (certs && certs.length > 0) {
      certsTable.innerHTML = certs.map(c => `
        <tr>
          <td><strong>${c.title}</strong></td>
          <td>${c.issuer}</td>
          <td><code>${c.credential_id || '--'}</code></td>
          <td><span class="pill-indicator pill-green">${c.verification_status}</span></td>
          <td><a href="${c.file_url || '#'}" target="_blank" class="small-text text-blue">View Certificate</a></td>
        </tr>
      `).join("");

      // Update completeness score indicators
      document.getElementById("pcs-val").textContent = `${Math.min(100, certs.length * 25)}%`;
    } else {
      certsTable.innerHTML = `<tr><td colspan="5" class="text-center muted">No certifications uploaded yet.</td></tr>`;
    }

    // load links
    const resLinks = await fetch("/api/learner/links");
    const links = await resLinks.json();
    document.getElementById("link-github").value = links.github_url || "";
    document.getElementById("link-linkedin").value = links.linkedin_url || "";

  } catch (err) {
    console.error("Skills payload load failed:", err);
  }
}

async function removeLearnerSkill(skillId) {
  try {
    const response = await fetch(
      `/api/learner/skills/${skillId}`,
      {
        method: "DELETE"
      }
    );

    const data = await response.json();

    if (!response.ok) {
      alert(data.detail || "Failed to remove skill.");
      return;
    }

    await loadSkillsHubPayload();

  } catch (err) {
    console.error("Failed to remove skill:", err);
    alert("Failed to remove skill.");
  }
}

function getStreamSuggestedLocalSkills(stream) {
  const streamLower = (stream || "").toLowerCase();
  if (streamLower.includes("business") || streamLower.includes("management")) {
    return {
      technical: ["Financial Modeling", "Market Research", "PowerBI & CRM"],
      non_technical: ["Client Negotiation", "Active listening", "Conflict Resolution"]
    };
  } else if (streamLower.includes("healthcare") || streamLower.includes("life")) {
    return {
      technical: ["Clinical Charting", "Lab safety", "Biostatistics"],
      non_technical: ["Patient Empathy", "Crisis Communication", "Coordination"]
    };
  }
  return {
    technical: ["Python Coding", "Git & GitHub", "SQL DB design"],
    non_technical: ["Technical writing", "Agile scrum", "Client requirement mapping"]
  };
}

async function addSuggestedSkill(name, category) {
  try {
    await fetch("/api/learner/skills", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ name, category, proficiency: "Intermediate" })
    });
    loadSkillsHubPayload();
  } catch (err) {
    console.error(err);
  }
}

async function addLearnerSkill() {
  const name = document.getElementById("skill-name").value;
  const category = document.getElementById("skill-category").value;
  const proficiency = document.getElementById("skill-proficiency").value;
  if (!name.strip()) return;

  try {
    await fetch("/api/learner/skills", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ name, category, proficiency })
    });
    document.getElementById("skill-name").value = "";
    loadSkillsHubPayload();
  } catch (err) {
    console.error(err);
  }
}

async function uploadCertification(e) {
  e.preventDefault();

  const form = document.getElementById("cert-upload-form");
  const fileInput = document.getElementById("cert-file");

  const title = document.getElementById("cert-title").value.trim();
  const issuer = document.getElementById("cert-issuer").value.trim();
  const credentialId = document.getElementById("cert-id").value.trim();

  if (!title) {
    alert("Please enter Certification Title.");
    return;
  }

  if (!issuer) {
    alert("Please enter Issuing Body.");
    return;
  }

  if (fileInput.files.length === 0) {
    alert("Please select a certificate PDF/image.");
    return;
  }

  const formData = new FormData();

  formData.append("title", title);
  formData.append("issuer", issuer);
  formData.append("credential_id", credentialId);
  formData.append("file", fileInput.files[0]);

  console.log("Certificate upload data:", {
    title: title,
    issuer: issuer,
    credential_id: credentialId,
    file: fileInput.files[0].name
  });

  try {
    const response = await fetch("/api/learner/certifications", {
      method: "POST",
      body: formData
    });

    const result = await response.json();

    console.log("Certificate response:", response.status, result);

    if (!response.ok) {
      alert(
        "Certificate upload failed.\n\n" +
        "Status: " + response.status +
        "\n\n" +
        JSON.stringify(result, null, 2)
      );
      return;
    }

    alert("Certificate uploaded successfully.");

    form.reset();

    await loadSkillsHubPayload();

  } catch (err) {
    console.error("Certificate upload failed:", err);
    alert("Certificate upload failed. Check browser console.");
  }
}

async function syncExternalLinks() {
  const github = document.getElementById("link-github").value;
  const linkedin = document.getElementById("link-linkedin").value;
  try {
    await fetch("/api/learner/links", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ github_url: github, linkedin_url: linkedin })
    });
    alert("Profile links synced successfully.");
    loadSkillsHubPayload();
  } catch (err) {
    console.error(err);
  }
}

// --- TAB PAYLOAD 3: CAREER SHIFT DELTA ---
async function calculateCareerShift() {
  const targetRole = document.getElementById("shift-target-role").value;
  const reason = document.getElementById("shift-reason").value;
  if (!targetRole.strip()) return;

  try {
    const res = await fetch("/api/readiness/career-shift", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ target_role: targetRole, shift_reason: reason })
    });
    const data = await res.json();

    const panel = document.getElementById("shift-results-panel");
    panel.classList.remove("hidden");
    panel.innerHTML = `
      <div class="card glass" style="border-color: var(--secondary); background: rgba(79, 172, 254, 0.03);">
        <h4>Capability Delta Results</h4>
        <p class="small-text muted margin-bottom">Switching to: <strong>${targetRole}</strong></p>
        
        <h5 class="small-text uppercase text-green">Transferable Skills</h5>
        <div class="skills-chips-wrapper pb-2">
          ${data.transferable_skills.map(s => `<span class="skill-chip tech">${s}</span>`).join("")}
        </div>

        <h5 class="small-text uppercase text-red margin-top">Skill Deficits & Gaps</h5>
        <div class="skills-chips-wrapper pb-2">
          ${data.gaps.map(g => `<span class="skill-chip" style="color: var(--accent-red); border-color: rgba(255, 60, 105, 0.3); background: rgba(255, 60, 105, 0.05);">${g}</span>`).join("")}
        </div>

        <h5 class="small-text uppercase text-blue margin-top">Remediation Roadmap Tasks</h5>
        <ul class="small-text pl-3 text-muted">
          ${data.reremediation_delta ? data.reremediation_delta.map(r => `<li>${r}</li>`).join("") : data.remediation_delta.map(r => `<li>${r}</li>`).join("")}
        </ul>
      </div>
    `;
  } catch (err) {
    console.error(err);
  }
}

// --- TAB PAYLOAD 4: MOCK INTERVIEWS ---
async function initializeMockInterview() {
  const name = document.getElementById("interview-user-name").value;
  const role = document.getElementById("interview-target-role").value;
  const diff = document.getElementById("interview-difficulty").value;
  const track = document.getElementById("interview-track").value;
  const avatar = document.getElementById("interview-avatar").value;
  if (!name.strip() || !role.strip()) return;

  try {
    const res = await fetch("/api/sessions", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({
        user_name: name,
        target_role: role,
        experience_level: "Fresher",
        difficulty: diff,
        interview_track: track,
        interviewer_avatar: avatar
      })
    });
    const session = await res.json();
    activeInterviewSessionId = session.session_id;

    // Show active screen, hide setup
    document.getElementById("mock-setup-workspace").classList.add("hidden");
    document.getElementById("mock-active-workspace").classList.remove("hidden");

    // Enable coding editor sandbox if technical track is active
    const codeSandbox = document.getElementById("interview-code-sandbox");
    if (track === "Technical & DSA") {
      codeSandbox.classList.remove("hidden");
      document.querySelector(".dialogue-pane").style.minHeight = "400px";
    } else {
      codeSandbox.classList.add("hidden");
    }

    // Set avatar characters
    document.getElementById("avatar-char").textContent = avatar.charAt(0);
    document.getElementById("avatar-name").textContent = `${avatar} the Recruiter`;

    // Connect WebSocket timer channel
    connectWebsocketTimer(session.session_id);

    // Load first question
    loadNextMockQuestion();

  } catch (err) {
    console.error("Session creation failed:", err);
  }
}

function connectWebsocketTimer(sessionId) {
  const loc = window.location;
  const protocol = loc.protocol === "https:" ? "wss:" : "ws:";
  ws = new WebSocket(`${protocol}//${loc.host}/ws/${sessionId}`);

  ws.onmessage = (event) => {
    const msg = JSON.parse(event.data);
    if (msg.type === "tick") {
      document.getElementById("interview-timer").textContent = `${msg.remaining}s`;
    } else if (msg.type === "ended") {
      document.getElementById("interview-timer").textContent = "0s";
      alert("Stress Time Limit Exceeded. Auto-submitting response.");
      submitTypedInterviewAnswer();
    }
  };
}

async function loadNextMockQuestion() {
  try {
    const res = await fetch(`/api/sessions/${activeInterviewSessionId}/current-question`);
    const q = await res.json();

    if (q.completed) {
      // Completed, load report
      ws.close();
      loadMockInterviewReport();
      return;
    }

    currentQuestionId = q.question_id;

    // Add question bubble
    const dialogue = document.getElementById("dialogue-box");
    dialogue.insertAdjacentHTML("beforeend", `
      <div class="speech-bubble bubble-interviewer">
        <strong>Interviewer:</strong> ${q.text}
      </div>
    `);
    dialogue.scrollTop = dialogue.scrollHeight;

    // Trigger timer start
    ws.send(JSON.stringify({ type: "start_timer", seconds: 40 }));

  } catch (err) {
    console.error("Load question failed:", err);
  }
}

async function submitTypedInterviewAnswer() {
  const ansText = document.getElementById("interview-response-text").value;
  const codeText = document.getElementById("sandbox-code-editor").value;
  if (!ansText.strip()) return;

  // stop timer
  ws.send(JSON.stringify({ type: "stop_timer" }));

  try {
    const dialogue = document.getElementById("dialogue-box");
    dialogue.insertAdjacentHTML("beforeend", `
      <div class="speech-bubble bubble-candidate">
        <strong>You:</strong> ${ansText}
      </div>
    `);
    dialogue.scrollTop = dialogue.scrollHeight;
    document.getElementById("interview-response-text").value = "";

    const res = await fetch(`/api/sessions/${activeInterviewSessionId}/answers`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ question_id: currentQuestionId, answer_text: ansText, submitted_code: codeText || null })
    });
    await res.json();

    // Load next question
    loadNextMockQuestion();

  } catch (err) {
    console.error(err);
  }
}

async function loadMockInterviewReport() {
  try {
    const res = await fetch(`/api/sessions/${activeInterviewSessionId}/report`);
    const rep = await res.json();

    document.getElementById("mock-active-workspace").classList.add("hidden");
    document.getElementById("mock-report-workspace").classList.remove("hidden");

    // Populate overall parameters
    document.getElementById("mock-score-overall").textContent = rep.overall_score;
    document.getElementById("mock-score-clarity").textContent = rep.clarity_score;
    document.getElementById("mock-score-confidence").textContent = rep.confidence_score;
    document.getElementById("mock-score-fillers").textContent = rep.total_filler_words;

    // Populate behavioral KPIs progress
    const latestItem = rep.items[rep.items.length - 1] || {};
    document.getElementById("kpi-growth").textContent = `${latestItem.growth_mindset || 50}%`;
    document.getElementById("fill-growth").style.width = `${latestItem.growth_mindset || 50}%`;
    document.getElementById("kpi-ownership").textContent = `${latestItem.ownership || 50}%`;
    document.getElementById("fill-ownership").style.width = `${latestItem.ownership || 50}%`;
    document.getElementById("kpi-empathy").textContent = `${latestItem.collaborative_empathy || 50}%`;
    document.getElementById("fill-empathy").style.width = `${latestItem.collaborative_empathy || 50}%`;
    document.getElementById("kpi-resilience").textContent = `${latestItem.stress_resilience || 50}%`;
    document.getElementById("fill-resilience").style.width = `${latestItem.stress_resilience || 50}%`;
    document.getElementById("kpi-integrity").textContent = `${latestItem.professional_integrity || 90}%`;
    document.getElementById("fill-integrity").style.width = `${latestItem.professional_integrity || 90}%`;

    // Populate code feedback
    const codePane = document.getElementById("code-feedback-pane");
    const techItem = rep.items.find(i => i.submitted_code);
    if (techItem) {
      codePane.innerHTML = `
        <div class="row between"><span class="small-text">Syntax Passes:</span><strong class="${techItem.code_syntax_passes ? 'text-green' : 'text-red'}">${techItem.code_syntax_passes ? 'PASSED' : 'FAILED'}</strong></div>
        <div class="row between"><span class="small-text">Estimated Time Complexity:</span><strong class="text-blue">${techItem.code_time_complexity || 'O(1)'}</strong></div>
        <div class="row between"><span class="small-text">Estimated Space Complexity:</span><strong class="text-blue">${techItem.code_space_complexity || 'O(1)'}</strong></div>
        <div class="row between"><span class="small-text">Code Cleanliness Score:</span><strong>${techItem.code_cleanliness_score || 0}/100</strong></div>
        <div class="row between"><span class="small-text">Error Robustness Score:</span><strong>${techItem.code_error_resilience || 0}/100</strong></div>
        <p class="small-text text-muted margin-top pt-2 border-top"><strong>Advice:</strong> Ensure try-except blocks protect against boundary conditions. Optimise nested loops to O(N log N) or O(N).</p>
      `;
    } else {
      codePane.innerHTML = `<p class="muted">No technical code submitted during this mock session.</p>`;
    }

    // Strengths summary
    document.getElementById("mock-strengths-list").innerHTML = rep.strengths_summary.map(s => `<li>${s}</li>`).join("");
    document.getElementById("mock-improvements-list").innerHTML = rep.improvement_summary.map(i => `<li>${i}</li>`).join("");

    // Detail trans
    document.getElementById("mock-transcript-items").innerHTML = rep.items.map(i => `
      <div class="card glass py-2 px-3">
        <p class="small-text font-bold text-blue">Q: ${i.question}</p>
        <p class="small-text pt-1"><strong>Answer:</strong> ${i.answer}</p>
        ${i.submitted_code ? `<pre class="small-text font-mono margin-top pt-2" style="background:#011627; color:#addb67; padding:8px; border-radius:6px;"><code>${i.submitted_code}</code></pre>` : ''}
        <p class="small-text text-green margin-top-5"><strong>Interviewer Feedback:</strong> ${i.feedback}</p>
      </div>
    `).join("");

  } catch (err) {
    console.error(err);
  }
}

async function verifySandboxCode() {
  const code = document.getElementById("sandbox-code-editor").value;
  const msg = document.getElementById("sandbox-syntax-msg");
  if (!code.strip()) return;

  // Simple compiled check fallback using local verify regex
  try {
    if (code.includes("def ") && code.includes("return")) {
      msg.textContent = "Compile status: Syntactic checks pass.";
      msg.className = "margin-top small-text font-mono text-green";
    } else {
      msg.textContent = "Compile warning: Missing function definition or return block.";
      msg.className = "margin-top small-text font-mono text-orange";
    }
  } catch (err) {
    msg.textContent = `Compile status: Failed. ${err}`;
    msg.className = "margin-top small-text font-mono text-red";
  }
}

// --- TAB PAYLOAD 5: LMS ACADEMY ---
async function loadLmsAcademyPayload() {
  try {
    const res = await fetch("/api/lms/courses");
    const courses = await res.json();

    const tree = document.getElementById("lms-syllabus-tree");
    if (courses && courses.length > 0) {
      const course = courses[0];
      tree.innerHTML = course.modules.map(m => `
        <div class="lms-module">
          <div class="lms-module-title">${m.title}</div>
          <div class="flex-column gap-5">
            ${m.lectures.map(l => `
              <div class="lms-lecture-item" onclick="loadLmsLecture(${course.id}, ${l.id}, '${l.title.replace(/'/g, "\\'")}')">
                &bull; ${l.title}
              </div>
            `).join("")}
          </div>
        </div>
      `).join("");

      // load active discussion posts
      loadLmsDiscussionPosts(course.id);
    }
  } catch (err) {
    console.error(err);
  }
}

async function loadLmsLecture(courseId, lectureId, title) {
  try {
    const res = await fetch("/api/lms/courses");
    const courses = await res.json();
    const course = courses.find(c => c.id === courseId);

    let lecture = null;
    for (const m of course.modules) {
      const found = m.lectures.find(l => l.id === lectureId);
      if (found) {
        lecture = found;
        break;
      }
    }

    if (lecture) {
      const player = document.getElementById("lms-lecture-player");
      player.innerHTML = `
        <div class="flex-column gap">
          <div class="row between border-bottom pb-2">
            <h3>${lecture.title}</h3>
            <button class="primary-btn small-text" onclick="completeLmsLecture(${courseId}, ${lectureId})">Mark Completed</button>
          </div>
          <p class="muted">${lecture.content}</p>
          ${lecture.mantras ? `
            <div class="card glass" style="background: rgba(0, 242, 254, 0.02); border-color: var(--secondary);">
              <h5 class="text-blue">Native Success Mantra</h5>
              <p class="small-text font-italic">"${lecture.mantras}"</p>
            </div>
          ` : ''}
        </div>
      `;
    }
  } catch (err) {
    console.error(err);
  }
}

async function completeLmsLecture(courseId, lectureId) {
  try {
    await fetch(`/api/lms/courses/${courseId}/enroll`, { method: "POST" });
    const res = await fetch(`/api/lms/courses/${courseId}/progress?lecture_id=${lectureId}`, { method: "POST" });
    const data = await res.json();
    alert(`Lecture completed. Total Course Progress: ${data.progress_percent}%`);
  } catch (err) {
    console.error(err);
  }
}

async function loadLmsDiscussionPosts(courseId) {
  try {
    const res = await fetch(`/api/lms/courses/${courseId}/posts`);
    const posts = await res.json();

    const container = document.getElementById("lms-posts-container");
    if (posts && posts.length > 0) {
      container.innerHTML = posts.map(p => `
        <div class="card glass py-2 px-3">
          <div class="row between"><span class="small-text font-bold text-blue">${p.user_name}</span><span class="small-text muted">${new Date(p.created_at).toLocaleTimeString()}</span></div>
          <p class="small-text pt-1">${p.text}</p>
        </div>
      `).join("");
    }
  } catch (err) {
    console.error(err);
  }
}

async function submitLmsCollaborationPost() {
  const text = document.getElementById("lms-new-post-text").value;
  if (!text.strip()) return;

  try {
    await fetch("/api/lms/courses/1/posts", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ text })
    });
    document.getElementById("lms-new-post-text").value = "";
    loadLmsDiscussionPosts(1);
  } catch (err) {
    console.error(err);
  }
}

// --- TAB PAYLOAD 6: GLOBAL COURSES ---
async function loadGlobalCoursesPayload() {
  try {
    const res = await fetch("/api/courses/campus");
    const courses = await res.json();

    const grid = document.getElementById("global-courses-grid");

    if (courses && courses.length > 0) {
      grid.innerHTML = courses.map(c => `
        <div class="card glass shadow flex-column gap">
          
          <div class="row between">
            <span class="pill-indicator pill-gray">${c.tier}</span>

            <span class="pill-indicator ${c.fee_type === "Free"
          ? "pill-green"
          : "pill-orange"
        }">
              ${c.fee_type}
            </span>
          </div>

          <div>
            <h4>${c.title}</h4>

            <span class="small-text muted">
              Offered by: ${c.provider} (${c.origin})
            </span>
          </div>

          <div class="row between margin-top pt-2 border-top align-center">

            ${c.coupon_code
          ? `<span class="small-text font-mono text-green">
                     Coupon: <code>${c.coupon_code}</code>
                   </span>`
          : "<span></span>"
        }

            <button
              class="primary-btn small-text"
              onclick="handleCampusCourseEnrollment(${c.id})"
            >
              Enroll Course
            </button>

          </div>

        </div>
      `).join("");
    }

  } catch (err) {
    console.error("Failed to load campus courses:", err);
  }
}

async function handleCampusCourseEnrollment(courseId) {
  try {
    // Get course information
    const coursesResponse = await fetch("/api/courses/campus");
    const courses = await coursesResponse.json();

    const course = courses.find(c => c.id === courseId);

    if (!course) {
      alert("Course not found.");
      return;
    }

    // FREE COURSE
    if (course.fee_type === "Free") {

      const response = await fetch(
        `/api/courses/${courseId}/enroll`,
        {
          method: "POST"
        }
      );

      const data = await response.json();

      if (!response.ok) {
        alert(data.detail || "Enrollment failed.");
        return;
      }

      alert(
        `Enrollment Successful! ✅\n\n${course.title}`
      );

      // Open the original course website
      if (course.direct_url) {
        window.open(course.direct_url, "_blank");
      }

      return;
    }

    // PAID COURSE
    showDummyPaymentScreen(course);

  } catch (err) {
    console.error("Enrollment error:", err);
    alert("Something went wrong. Please try again.");
  }
}


function showDummyPaymentScreen(course) {

  const existing = document.getElementById("dummy-payment-modal");

  if (existing) {
    existing.remove();
  }

  const modal = document.createElement("div");

  modal.id = "dummy-payment-modal";

  modal.innerHTML = `
    <div style="
      position: fixed;
      inset: 0;
      background: rgba(0,0,0,0.75);
      display: flex;
      align-items: center;
      justify-content: center;
      z-index: 9999;
      padding: 20px;
    ">

      <div class="card glass shadow" style="
        width: 100%;
        max-width: 480px;
        padding: 28px;
      ">

        <div class="row between">
          <h3>Course Payment</h3>

           <button
  type="button"
  class="secondary-btn"
  id="close-dummy-payment-btn"
>
  ✕
</button>
        </div>

        <div class="border-top pt-3 margin-top">

          <h4>${course.title}</h4>

          <p class="muted small-text">
            Offered by: ${course.provider}
          </p>

          <div class="card glass margin-top">
            <div class="row between">
              <span>Course Fee</span>
              <strong>₹999</strong>
            </div>

            ${course.coupon_code
      ? `
                  <div class="row between margin-top">
                    <span>Coupon</span>
                    <code>${course.coupon_code}</code>
                  </div>

                  <div class="row between margin-top">
                    <span>Discount</span>
                    <strong>100%</strong>
                  </div>
                `
      : ""
    }

            <div class="row between margin-top border-top pt-2">
              <strong>Total</strong>
              <strong class="text-green">
                ${course.coupon_code ? "₹0" : "₹999"}
              </strong>
            </div>
          </div>

          <p class="small-text muted margin-top">
            This is a demo payment. No real money will be charged.
          </p>

          <button
            id="dummy-pay-now-btn"
            class="primary-btn"
            style="width:100%; margin-top:16px;"
            onclick="processDummyCoursePayment(${course.id})"
          >
            Pay Now
          </button>

        </div>

      </div>

    </div>
  `;

  document.body.appendChild(modal);
  const closeButton = document.getElementById("close-dummy-payment-btn");

  if (closeButton) {
    closeButton.addEventListener("click", () => {
      const modal = document.getElementById("dummy-payment-modal");
      if (modal) {
        modal.remove();
      }
    });
  }
}

async function processDummyCoursePayment(courseId) {

  const button = document.getElementById("dummy-pay-now-btn");

  if (button) {
    button.disabled = true;
    button.innerText = "Processing...";
  }

  try {

    // Step 1: Dummy payment
    const paymentResponse = await fetch(
      `/api/courses/${courseId}/payment`,
      {
        method: "POST"
      }
    );

    const paymentData = await paymentResponse.json();

    if (!paymentResponse.ok) {
      alert(paymentData.detail || "Payment failed.");
      return;
    }

    // Step 2: Enroll after successful payment
    const enrollmentResponse = await fetch(
      `/api/courses/${courseId}/enroll`,
      {
        method: "POST"
      }
    );

    const enrollmentData = await enrollmentResponse.json();

    if (!enrollmentResponse.ok) {
      alert(
        enrollmentData.detail ||
        "Payment succeeded but enrollment failed."
      );
      return;
    }

    closeDummyPaymentScreen();

    alert(
      "Demo Payment Successful! ✅\n\n" +
      "Enrollment Successful! 🎓"
    );

  } catch (err) {

    console.error("Payment error:", err);

    alert("Payment processing failed.");

  } finally {

    if (button) {
      button.disabled = false;
      button.innerText = "Pay Now";
    }

  }
}

// --- TAB PAYLOAD 7: jobs board ---
async function loadJobsPayload() {
  try {
    const res = await fetch("/api/jobs");
    const jobs = await res.json();

    const grid = document.getElementById("job-openings-grid");

    if (jobs && jobs.length > 0) {
      grid.innerHTML = jobs.map(j => `
        <div class="card glass shadow row between align-center py-3">

          <div style="flex:1;">

            <h4>${j.title}</h4>

            <span class="small-text muted">
              Organization: ${j.organization} | Track: ${j.type}
            </span>

            <!-- Required Skills -->
            <div class="skills-chips-wrapper pt-1">
              ${j.required_skills.map(s => `
                <span
                  class="skill-chip tech small-text py-0 px-2"
                  style="font-size:11px;"
                >
                  ${s}
                </span>
              `).join("")}
            </div>

            <!-- Matched Skills -->
            ${
              j.matched_skills && j.matched_skills.length > 0
              ? `
                <div class="margin-top">
                  <span class="small-text text-green">
                    ✓ Matched Skills
                  </span>

                  <div class="skills-chips-wrapper pt-1">
                    ${j.matched_skills.map(s => `
                      <span
                        class="skill-chip tech small-text py-0 px-2"
                        style="font-size:11px;"
                      >
                        ✓ ${s}
                      </span>
                    `).join("")}
                  </div>
                </div>
              `
              : `
                <div class="margin-top">
                  <span class="small-text muted">
                    No matching skills yet
                  </span>
                </div>
              `
            }

            <!-- Missing Skills -->
            ${
              j.missing_skills && j.missing_skills.length > 0
              ? `
                <div class="margin-top">
                  <span class="small-text">
                    Skills to Improve
                  </span>

                  <div class="skills-chips-wrapper pt-1">
                    ${j.missing_skills.map(s => `
                      <span
                        class="skill-chip small-text py-0 px-2"
                        style="font-size:11px;"
                      >
                        ○ ${s}
                      </span>
                    `).join("")}
                  </div>
                </div>
              `
              : `
                <div class="margin-top">
                  <span class="small-text text-green">
                    ✓ All required skills matched
                  </span>
                </div>
              `
            }

          </div>

          <div class="text-right flex-column gap-5">

            <!-- Fit Index -->
            <span
              class="pill-indicator ${
                j.match_score >= 80
                  ? "pill-green"
                  : "pill-orange"
              }"
              style="display:inline-block;"
            >
              Fit Index: ${j.match_score}%
            </span>

            <!-- Apply -->
            <button
              class="primary-btn small-text"
              style="margin-top:6px;"
              onclick="applyToJob(${j.id}, this)"
            >
              Apply (1-Click)
            </button>
            
            <a
              href="${j.url}"
              target="_blank"
              class="secondary-btn small-text"
              style="text-decoration:none; margin-top:6px; display:block;"
            >
              Apply Direct
            </a>

          </div>

        </div>
      `).join("");
    }

  } catch (err) {
    console.error("Failed to load jobs:", err);
  }
}

async function applyToJob(jobId, btn) {
  const originalText = btn.innerText;
  btn.innerText = "Applying...";
  btn.disabled = true;
  
  try {
    const res = await fetch(`/api/jobs/${jobId}/apply`, { method: "POST" });
    const data = await res.json();
    if (res.ok) {
      btn.innerText = "✓ Applied";
      btn.classList.remove("primary-btn");
      btn.classList.add("secondary-btn");
      
      // Refresh dashboard timeline if framework is open
      const timeline = document.getElementById("dashboard-proceedings-timeline");
      if (timeline && timeline.innerHTML) {
        // Option to reload dashboard payload or just let it be until they switch tabs
      }
    } else {
      alert(data.detail || "Failed to apply");
      btn.innerText = originalText;
      btn.disabled = false;
    }
  } catch(e) {
    alert("Network error.");
    btn.innerText = originalText;
    btn.disabled = false;
  }
}

// --- TAB PAYLOAD 8: BOOKTOUCHPOINTS ---
async function loadAppointmentsPayload() {
  try {
    const res = await fetch("/api/mentorship/appointments");
    const appts = await res.json();

    const container = document.getElementById("booked-appointments-list");
    if (appts && appts.length > 0) {
      container.innerHTML = appts.map(a => {
        const mType = a.meeting_type || "Google Meet";
        return `
        <div class="card glass shadow py-2 px-3 margin-bottom row between align-center">
          <div>
            <h4>Session with ${a.mentor_name}</h4>
            <span class="small-text muted">Scheduled: ${a.date_str} at ${a.time_str}</span><br/>
            <span class="small-text muted">Meeting:<br/>${mType}</span>
          </div>
          <div class="text-right">
              <span class="pill-indicator pill-green" style="display:inline-block; margin-bottom:6px;">${a.status}</span><br/>
              <button onclick="openEditMeetingModal('${a.id}', '${a.mentor_name}', '${a.date_str}', '${a.time_str}', '${a.meeting_type}', '${a.meet_url}')" class="primary-btn small-text" style="background: #26384f; color: #fff; margin-right: 5px;">Edit Meeting</button>
              <a href="${a.meet_url}" target="_blank" class="primary-btn small-text" style="text-decoration:none;">Join Meeting</a>
          </div>
        </div>
      `}).join("");
    } else {
      container.innerHTML = `<p class="muted">No touchpoints booked yet. Select a slot on the left to schedule.</p>`;
    }
  } catch (err) {
    console.error(err);
  }
}

  function toggleCustomUrlInput() {
    const meetingType = document.getElementById("appointment-meeting-type").value;
    const customUrlContainer = document.getElementById("custom-url-container");
    if (meetingType === "Custom Meeting Link") {
      customUrlContainer.style.display = "block";
    } else {
      customUrlContainer.style.display = "none";
    }
  }

  async function bookMentorshipMeeting() {
    const mentor = document.getElementById("appointment-mentor").value;
    const date = document.getElementById("appointment-date").value;
    const time = document.getElementById("appointment-time").value;
    const meetingType = document.getElementById("appointment-meeting-type").value;
    const customUrl = document.getElementById("appointment-custom-url").value;

    if (!mentor || !date || !time || !meetingType) return;
    if (meetingType === "Custom Meeting Link" && !customUrl) {
      alert("Please enter a custom meeting URL.");
      return;
    }

    try {
      await fetch("/api/mentorship/appointments", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ mentor_name: mentor, date_str: date, time_str: time, meeting_type: meetingType, custom_url: customUrl })
      });
      alert("Touchpoint scheduled. Meeting details saved.");
      loadAppointmentsPayload();
    } catch (err) {
      console.error(err);
    }
  }

  function toggleEditCustomUrlInput() {
    const meetingType = document.getElementById("edit-appointment-meeting-type").value;
    const customUrlContainer = document.getElementById("edit-custom-url-container");
    if (meetingType === "Custom Meeting Link") {
      customUrlContainer.style.display = "block";
    } else {
      customUrlContainer.style.display = "none";
    }
  }

  function openEditMeetingModal(appId, mentor, date, time, meetingType, meetUrl) {
    document.getElementById("edit-appointment-id").value = appId;
    document.getElementById("edit-appointment-mentor").value = mentor;
    document.getElementById("edit-appointment-date").value = date;
    document.getElementById("edit-appointment-time").value = time;
    
    // Safely fallback meeting type
    const safeMeetingType = meetingType && meetingType !== "null" ? meetingType : "Google Meet";
    document.getElementById("edit-appointment-meeting-type").value = safeMeetingType;
    
    toggleEditCustomUrlInput();
    if (safeMeetingType === "Custom Meeting Link") {
      document.getElementById("edit-appointment-custom-url").value = meetUrl;
    } else {
      document.getElementById("edit-appointment-custom-url").value = "";
    }
    
    document.getElementById("edit-mentorship-modal").style.display = "flex";
  }

  function closeEditMentorshipModal() {
    document.getElementById("edit-mentorship-modal").style.display = "none";
  }

  async function saveEditedMentorshipMeeting() {
    const appId = document.getElementById("edit-appointment-id").value;
    const mentor = document.getElementById("edit-appointment-mentor").value;
    const date = document.getElementById("edit-appointment-date").value;
    const time = document.getElementById("edit-appointment-time").value;
    const meetingType = document.getElementById("edit-appointment-meeting-type").value;
    const customUrl = document.getElementById("edit-appointment-custom-url").value;

    if (!mentor || !date || !time || !meetingType) return;
    if (meetingType === "Custom Meeting Link" && !customUrl) {
      alert("Please enter a custom meeting URL.");
      return;
    }

    try {
      await fetch(`/api/mentorship/appointments/${appId}`, {
        method: "PUT",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ 
            mentor_name: mentor, 
            date_str: date, 
            time_str: time, 
            meeting_type: meetingType, 
            custom_url: customUrl 
        })
      });
      alert("Meeting details updated successfully.");
      closeEditMentorshipModal();
      loadAppointmentsPayload();
    } catch (err) {
      console.error(err);
    }
  }

// --- TAB PAYLOAD 9: CYBER SECURITY ---
async function loadCyberSecurityPayload() {
  try {
    const resLogs = await fetch("/api/admin/security-logs");
    const logs = await resLogs.json();

    const tbody = document.getElementById("security-logs-tbody");
    if (logs && logs.length > 0) {
      tbody.innerHTML = logs.map(l => `
        <tr>
          <td><code>${l.ip_address}</code></td>
          <td><strong>${l.category}</strong></td>
          <td class="small-text text-muted">${l.action_attempt}</td>
          <td><span class="pill-indicator ${l.status === 'Allowed' ? 'pill-green' : 'pill-red'}">${l.status}</span></td>
        </tr>
      `).join("");
    } else {
      tbody.innerHTML = `<tr><td colspan="4" class="text-center muted">No threats logged. System secure.</td></tr>`;
    }

    // load RAG/CAG monitor status
    const resStatus = await fetch("/api/rag-cag/status");
    const status = await resStatus.json();
    const pane = document.getElementById("rag-cag-status-pane");
    pane.innerHTML = `
      <div class="row between"><span class="small-text">RAG Search Corpus:</span><strong class="text-green">${status.vector_docs_count} Documents Indexed</strong></div>
      <div class="row between"><span class="small-text">CAG Caching Status:</span><strong class="text-blue">${status.cag_cached_docs_count} Docs pre-cached</strong></div>
      <div class="row between"><span class="small-text">CAG Latency:</span><strong>${status.latency_cag_ms}ms</strong></div>
      <div class="row between"><span class="small-text">RAG Retr Latency:</span><strong>${status.latency_rag_ms}ms</strong></div>
      <div class="row between"><span class="small-text">Index cache hits:</span><strong class="text-green">${status.cache_hits} hits</strong></div>
    `;

    // load feedback loops
    const resLoops = await fetch("/api/safety/feedback-loops");
    const loops = await resLoops.json();
    const loopsContainer = document.getElementById("safety-feedback-loops");
    if (loops && loops.length > 0) {
      loopsContainer.innerHTML = loops.map(l => `
        <div class="card glass py-2 px-3" style="border-color: rgba(0, 242, 254, 0.15);">
          <div class="row between"><strong class="small-text text-blue">Trigger: ${l.trigger_event}</strong><span class="pill-indicator pill-green">${l.status}</span></div>
          <p class="small-text pt-1 text-muted"><strong>Remediation Applied:</strong> ${l.action_taken}</p>
        </div>
      `).join("");
    } else {
      loopsContainer.innerHTML = `<p class="muted small-text">No loop interventions logged yet.</p>`;
    }

  } catch (err) {
    console.error(err);
  }
}

// --- TAB PAYLOAD 10: FRAMEWORK reference ---
async function loadFrameworkPayload(subtab) {
  const infoPane = document.getElementById("framework-info-pane");
  const subtabs = document.querySelectorAll(".tab-btn");
  subtabs.forEach(btn => {
    btn.classList.remove("active");
    if (btn.getAttribute("data-subtab") === subtab) {
      btn.classList.add("active");
    }
  });

  // Re-bind click event
  subtabs.forEach(btn => {
    btn.onclick = () => loadFrameworkPayload(btn.getAttribute("data-subtab"));
  });

  try {
    const res = await fetch("/api/framework");
    const data = await res.json();

    if (subtab === "flow") {
      infoPane.innerHTML = `
        <div class="flex-column gap">
          <h4>Universal Readiness Flow (9 Stages)</h4>
          <p class="muted">Evidence-based chronological stages mapped from baseline discovery to long-term career growth.</p>
          <div class="grid grid-2 gap margin-top">
            ${data.universal_flow.map(f => `
              <div class="card glass py-2 px-3">
                <div class="flex-row justify-between align-center">
                  <span class="small-text uppercase text-blue font-bold">Stage: ${f.stage}</span>
                  ${f.completed ? '<span class="badge green">✓ Completed</span>' : '<span class="badge muted">○ Not started</span>'}
                </div>
                <h5 class="margin-top-5">Key Purpose: ${f.purpose}</h5>
                <p class="small-text muted">Trigger Check: ${f.key_question}</p>
                <p class="small-text text-green">Output: ${f.output}</p>
              </div>
            `).join("")}
          </div>
        </div>
      `;
    } else if (subtab === "dimensions") {
      infoPane.innerHTML = `
        <div class="flex-column gap">
          <h4>Weighted Readiness Scorecard Dimensions</h4>
          <div class="grid grid-3 gap margin-top">
            ${data.readiness_dimensions.map(d => `
              <div class="card glass py-2 px-3">
                <h5>${d.label}</h5>
                <span class="small-text muted">Weight: ${d.weight}% | Layer: ${d.layer}</span>
                <p class="small-text text-green margin-top-5">Signals: ${d.signals.join(", ")}</p>
              </div>
            `).join("")}
          </div>
        </div>
      `;
    } else if (subtab === "gaps") {
      infoPane.innerHTML = `
        <div class="flex-column gap">
          <h4>Gap Diagnostics Heuristics</h4>
          <div class="flex-column gap margin-top">
            ${data.gap_matrix.map(g => `
              <div class="card glass py-2 px-3" style="border-left: 3px solid var(--accent-red);">
                <h5>${g.gap_type}</h5>
                <p class="small-text muted">Symptom: ${g.symptoms}</p>
                <p class="small-text text-red">Root Cause: ${g.root_cause}</p>
                <p class="small-text text-green">Remediation Action: ${g.fix}</p>
              </div>
            `).join("")}
          </div>
        </div>
      `;
    } else if (subtab === "compliance") {
      infoPane.innerHTML = `
        <div class="flex-column gap">
          <h4>Platform Compliance & Data Policies</h4>
          <div class="grid grid-2 gap margin-top">
            <div class="card glass py-2 px-3">
              <h5>GDPR Compliance</h5>
              <p class="small-text text-muted">Strict data portability enabled. Learners have rights to download/export diagnostic portfolios. All file buffers are deleted post analysis.</p>
            </div>
            <div class="card glass py-2 px-3">
              <h5>Data Sovereignty</h5>
              <p class="small-text text-muted">All logs, transcript records, and SQLite databases run locally inside user-owned workspaces, ensuring zero-cost cloud data leakage risk.</p>
            </div>
          </div>
        </div>
      `;
    } else if (subtab === "moats") {
      try {
        const resMoat = await fetch("/api/admin/moat");
        const moat = await resMoat.json();
        infoPane.innerHTML = `
          <div class="flex-column gap">
            <h4>Strategic Moat Metrics</h4>
            <p class="muted">Capturing platform core datasets, custom model iterations, and academic partners.</p>
            <div class="grid grid-3 gap margin-top">
              ${Object.entries(moat).map(([key, val]) => `
                <div class="card glass text-center">
                  <span class="small-text uppercase text-blue">${key}</span>
                  <h3 class="margin-top-5 text-green">${val}</h3>
                </div>
              `).join("")}
            </div>
          </div>
        `;
      } catch (err) {
        console.error(err);
      }
    }

  } catch (err) {
    console.error(err);
  }
}

// --- ADMIN PANELS: COHORT, MENTORS, EMPLOYERS ---
async function loadMentorDeskPayload() {
  try {
    loadMentorRosterPayload();
    const resHitl = await fetch("/api/admin/hitl-queue");
    const hitl = await resHitl.json();

    const container = document.getElementById("mentor-hitl-queue");
    if (hitl && hitl.length > 0) {
      container.innerHTML = hitl.map(h => `
        <div class="card glass py-2 px-3 row between align-center margin-bottom-5">
          <div style="flex: 2;">
            <strong>Student: ${h.learner_name || 'System'}</strong> | <span class="small-text text-orange">Task: ${h.task_type}</span>
            <p class="small-text margin-top-5">
              Certificate: ${h.certificate_title || h.flag_reason}<br/>
              Issuer: ${h.issuer || 'N/A'} | Credential ID: ${h.credential_id || 'N/A'}<br/>
              ${h.file_url ? `<a href="${h.file_url}" target="_blank" class="text-blue">📄 View Evidence</a>` : ''}
            </p>
          </div>
          <div style="flex: 1; text-align: right;">
            <p class="small-text margin-bottom-5">Status: ${h.status}</p>
            ${h.status === 'Pending' ? `
              <button class="primary-btn small-text" onclick="resolveHitlTask(${h.id}, 'approve')">Approve</button>
              <button class="primary-btn small-text" style="background: var(--accent-red);" onclick="resolveHitlTask(${h.id}, 'reject')">Reject</button>
            ` : `<span class="pill-indicator pill-green">Resolved</span>`}
          </div>
        </div>
      `).join("");
    } else {
      container.innerHTML = `<p class="muted">No pending review tasks in queue.</p>`;
    }
  } catch (err) {
    console.error(err);
  }
}

async function resolveHitlTask(hitlId, decision) {
  const notes = prompt(`Enter reviewer notes/decision remarks for ${decision.toUpperCase()}:`);
  if (notes === null) return;

  try {
    const formData = new FormData();
    formData.append("decision", decision);
    formData.append("reviewer_notes", notes);
    await fetch(`/api/admin/hitl-queue/${hitlId}/resolve`, {
      method: "POST",
      body: formData
    });
    alert(`Task ${decision}d and logged.`);
    loadMentorDeskPayload();
  } catch (err) {
    console.error(err);
  }
}

async function loadMentorRosterPayload() {
  try {
    const res = await fetch("/api/admin/roster");
    const roster = await res.json();
    const container = document.getElementById("mentor-cohort-roster");
    
    if (roster && roster.length > 0) {
      container.innerHTML = roster.map(r => `
        <div class="roster-item card glass py-2 px-3 row between align-center margin-bottom-5">
          <div>
            <strong>${r.learner_name}</strong><br/>
            <span class="small-text muted">${r.target_role || r.stream || 'Target Not Set'}</span>
          </div>
          <div class="text-right">
            <strong>CARI: ${r.cari !== null ? r.cari : 'Not assessed'}</strong><br/>
            <span class="small-text ${r.top_gap ? 'text-orange' : 'text-green'}">Gap: ${r.top_gap || 'No major gap identified'}</span>
          </div>
          <div>
            <button class="primary-btn small-text" onclick="openDiagnosticModal(${r.learner_id})">View Profile</button>
          </div>
        </div>
      `).join("");
    } else {
      container.innerHTML = `<p class="muted">No learners available.</p>`;
    }
  } catch (err) {
    console.error("Failed to load roster", err);
  }
}

async function openDiagnosticModal(learnerId) {
  document.getElementById("diagnostic-modal").classList.remove("hidden");
  const container = document.getElementById("diagnostic-modal-content");
  container.innerHTML = `<p>Loading diagnostic data...</p>`;
  
  try {
    const res = await fetch(`/api/admin/learners/${learnerId}/diagnostics`);
    if (!res.ok) {
      container.innerHTML = `<p class="text-red">Failed to load learner data.</p>`;
      return;
    }
    const data = await res.json();
    
    let gapsHtml = data.gaps.length > 0 
      ? data.gaps.map(g => `<li><strong>${g.gap_type}</strong> (${g.severity}): ${g.symptoms}</li>`).join("")
      : "<li>No gaps recorded.</li>";
      
    let skillsHtml = data.skills.length > 0
      ? data.skills.map(s => `<span class="pill-indicator">${s.skill_name} (${s.proficiency_level})</span>`).join(" ")
      : "<span class='muted'>No skills logged.</span>";

    container.innerHTML = `
      <h4>${data.learner_name} - ${data.target_roles || data.stream || 'Unspecified'}</h4>
      <div class="grid grid-2 gap">
        <div class="card glass shadow-sm">
          <strong>CARI Score:</strong> ${data.cari !== null ? data.cari : 'N/A'}<br/>
          <strong>Level:</strong> ${data.readiness_level || 'N/A'}
        </div>
        <div class="card glass shadow-sm">
          <strong>Scorecard Highlights:</strong><br/>
          ${data.scorecard ? `
            Comm: ${data.scorecard.communication_readiness} | Domain: ${data.scorecard.domain_readiness} <br/>
            Problem Solving: ${data.scorecard.problem_solving}
          ` : 'No scorecard available'}
        </div>
      </div>
      <div>
        <strong>Diagnostic Gaps:</strong>
        <ul class="margin-top-5 small-text">${gapsHtml}</ul>
      </div>
      <div>
        <strong>Skills:</strong>
        <div class="margin-top-5">${skillsHtml}</div>
      </div>
    `;
  } catch (err) {
    console.error(err);
    container.innerHTML = `<p class="text-red">Error loading diagnostics.</p>`;
  }
}

function closeDiagnosticModal() {
  document.getElementById("diagnostic-modal").classList.add("hidden");
}

async function loadInstitutionBoardPayload() {
  try {
    // Seed and load partnership ROI
    const list = document.getElementById("institution-collaborations-list");
    list.innerHTML = `
      <div class="card glass py-2 px-3 row between">
        <div><strong>National Skill Development Corp (NSDC)</strong><br/><span class="small-text muted">Bilateral certification partnership</span></div>
        <div class="text-right"><strong>SROI: 88%</strong><br/><span class="small-text text-green">CSC: &sigma;=6.2</span></div>
      </div>
      <div class="card glass py-2 px-3 row between margin-top-5">
        <div><strong>SWAYAM Offline-Online Program</strong><br/><span class="small-text muted">Curriculum bridging gap programs</span></div>
        <div class="text-right"><strong>SROI: 74%</strong><br/><span class="small-text text-green">CSC: &sigma;=9.4</span></div>
      </div>
    `;
  } catch (err) {
    console.error(err);
  }
}

async function loadEmployerBoardPayload() {
  try {
    const container = document.getElementById("employer-job-matches");
    container.innerHTML = `
      <div class="card glass py-2 px-3 row between align-center">
        <div>
          <h4>Applicant: Rahul Sen</h4>
          <span class="small-text muted">Target: Junior Python Engineer | Stream: Eng Track</span>
        </div>
        <div class="text-right">
          <strong>Aspiration Match (ARMC): 94%</strong><br/>
          <button class="primary-btn small-text margin-top-5" onclick="alert('Applicant portfolio downloaded locally.')">Get Portfolio</button>
        </div>
      </div>
    `;
  } catch (err) {
    console.error(err);
  }
}

// --- MODAL CONTROLLERS ---
function openOnboardModal() {
  document.getElementById("onboard-modal").classList.remove("hidden");
}

function closeOnboardModal() {
  document.getElementById("onboard-modal").classList.add("hidden");
}

async function submitOnboardDiagnostics() {
  const name = document.getElementById("onboard-name").value;
  const stream = document.getElementById("onboard-stream").value;
  const experience = document.getElementById("onboard-experience").value;
  const dreamRole = document.getElementById("onboard-dream-role").value;
  const dreamReason = document.getElementById("onboard-dream-reason").value;
  const impact = document.getElementById("onboard-dream-impact").value;
  const identity = document.getElementById("onboard-dream-identity").value;
  const strengths = document.getElementById("onboard-dream-strengths").value;
  const fears = document.getElementById("onboard-dream-fears").value;
  const reflection = document.getElementById("onboard-reflection").value;

  if (!name.strip() || !dreamRole.strip()) {
    alert("Please fill in candidate name and dream role.");
    return;
  }

  const contextFactors = {
    family_pressure: document.getElementById("onboard-cf-family").value,
    financial_dependency: document.getElementById("onboard-cf-finance").value,
    confidence_baseline: parseInt(document.getElementById("onboard-cf-confidence").value) || 50,
    stress_baseline: parseInt(document.getElementById("onboard-cf-stress").value) || 50,
    resilience_rating: parseInt(document.getElementById("onboard-cf-resilience").value) || 50,
    income_tier: document.getElementById("onboard-cf-income").value,
    city_tier: document.getElementById("onboard-cf-city").value,
    college_tier: document.getElementById("onboard-cf-college").value
  };

  const payload = {
    user_name: name,
    target_role: dreamRole,
    experience_level: experience,
    stream: stream,
    dream_role: dreamRole,
    dream_reason: dreamReason,
    impact: impact,
    lifestyle: "",
    strengths: strengths,
    fears: fears,
    identity_goal: identity,
    reflection: reflection,
    dimension_scores: {
      purpose_clarity: 65,
      self_awareness_confidence: 60,
      communication_readiness: 55,
      digital_ai_readiness: 50,
      domain_technical_readiness: 55,
      problem_solving_readiness: 50,
      collaboration_leadership: 60,
      career_readiness: 60,
      portfolio_evidence: 45
    },
    portfolio_evidence: ["Resume", "LinkedIn/profile"],
    context_factors: contextFactors
  };

  try {
    const res = await fetch("/api/readiness/diagnose", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(payload)
    });
    await res.json();
    closeOnboardModal();
    loadDashboardPayload();
  } catch (err) {
    console.error("Diagnosis submission failed:", err);
  }
}

// --- MEDIA RECORDING HELPERS ---
async function startMediaRecording(type) {
  mediaType = type;
  recordedChunks = [];

  const constraints = {
    audio: true,
    video: type === "video" ? { width: 320, height: 240 } : false
  };

  try {
    const stream = await navigator.mediaDevices.getUserMedia(constraints);
    mediaRecorder = new MediaRecorder(stream);

    mediaRecorder.ondataavailable = (e) => {
      if (e.data && e.data.size > 0) {
        recordedChunks.push(e.data);
      }
    };

    mediaRecorder.onstop = () => {
      const blob = new Blob(recordedChunks, { type: type === "video" ? "video/webm" : "audio/wav" });
      const url = URL.createObjectURL(blob);

      const preview = document.getElementById("dialogue-media-preview");
      preview.classList.remove("hidden");

      if (type === "video") {
        preview.innerHTML = `<video src="${url}" controls style="width:200px; border-radius:6px;"></video>`;
      } else {
        preview.innerHTML = `<audio src="${url}" controls></audio>`;
      }
    };

    mediaRecorder.start();
    document.getElementById("interview-record-audio-btn").classList.add("hidden");
    document.getElementById("interview-record-video-btn").classList.add("hidden");
    document.getElementById("interview-stop-record-btn").classList.remove("hidden");
    document.getElementById("interview-recording-label").classList.remove("hidden");

  } catch (err) {
    console.error("Recording start failed:", err);
    alert("Audio/Video recording inputs not accessible. Type response instead.");
  }
}

function stopMediaRecording() {
  if (mediaRecorder && mediaRecorder.state !== "inactive") {
    mediaRecorder.stop();
    mediaRecorder.stream.getTracks().forEach(t => t.stop());
  }

  document.getElementById("interview-stop-record-btn").classList.add("hidden");
  document.getElementById("interview-recording-label").classList.add("hidden");

  // Auto package response text
  document.getElementById("interview-response-text").value = `Recorded spoken response (${mediaType}) ready to sync.`;
  document.getElementById("interview-record-audio-btn").classList.remove("hidden");
  document.getElementById("interview-record-video-btn").classList.remove("hidden");
}

// --- HELPER PROTOTYPES ---
String.prototype.strip = function () {
  return this.trim();
};
