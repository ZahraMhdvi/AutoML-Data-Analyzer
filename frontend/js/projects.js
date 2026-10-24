const projectCache = new Map();

const projectPage = {
    project: null,
    selectedVersion: null
};


function problemLabel(type){
    return type ? t(`problemType.${type}`) : "";
}


function goalLabel(goal){
    return goal ? t(`goal.${goal}`) : "";
}


async function showProjects(){

    showView("projectsView");
    setNav("projects");

    const view = document.getElementById("projectsView");
    view.innerHTML = `<p class="hint">${t("loading.projects")}</p>`;

    let data;
    try {
        data = await api("/api/projects");
    }
    catch(err){
        if(err.status !== 401){
            view.innerHTML = `<div class="error">${escapeHtml(err.message)}</div>`;
        }
        return;
    }

    const projects = data.projects;
    const user = session.user || {};
    const readyCount = projects.filter(p => p.status === "ready").length;
    const versionCount = projects.reduce((sum, p) => sum + p.version_count, 0);

    view.innerHTML = `
        <div class="profile">
            <div class="profile__avatar">${escapeHtml((user.name || "?").charAt(0).toUpperCase())}</div>
            <div class="profile__info">
                <h2>${t("projects.hello", { name: escapeHtml(user.name || "") })}</h2>
                <p dir="ltr" class="profile__email">${escapeHtml(user.email || "")}</p>
                <p class="hint">${t("projects.memberSince", { date: formatDate(user.created_at, false) })}</p>
            </div>
            <ul class="profile__stats">
                <li><b>${formatNumber(projects.length)}</b><span>${t("projects.statProjects")}</span></li>
                <li><b>${formatNumber(readyCount)}</b><span>${t("projects.statReady")}</span></li>
                <li><b>${formatNumber(versionCount)}</b><span>${t("projects.statVersions")}</span></li>
            </ul>
        </div>

        <div class="section-head">
            <h2>${t("projects.title")}</h2>
            <a class="button" href="#/new">${t("projects.newButton")}</a>
        </div>

        ${projects.length === 0 ? `
            <div class="empty">
                <div class="empty__icon">▤</div>
                <h3>${t("projects.emptyTitle")}</h3>
                <p>${t("projects.emptyText")}</p>
                <a class="button" href="#/new">${t("projects.emptyButton")}</a>
            </div>`
        : `<div class="project-grid">${projects.map(projectCard).join("")}</div>`}
    `;

    view.querySelectorAll("[data-update-project]").forEach(button => {
        button.addEventListener("click", () => {
            sessionStorageSet("openUpdate", button.dataset.updateProject);
            location.hash = `#/project/${button.dataset.updateProject}`;
        });
    });

    view.querySelectorAll("[data-delete-project]").forEach(button => {
        button.addEventListener("click", () => deleteProject(Number(button.dataset.deleteProject), button.dataset.name));
    });

}


function summaryText(summary){

    if(!summary){
        return "";
    }

    if(summary.accuracy !== undefined && summary.accuracy !== null){
        return t("projects.summaryClassification", { f1: formatPercent(summary.macro_f1), acc: formatPercent(summary.accuracy) });
    }

    if(summary.cluster_count !== undefined){
        return t("projects.summaryClustering", {
            k: summary.cluster_count,
            silhouette: summary.silhouette_score === null || summary.silhouette_score === undefined ? "-" : formatNumber(summary.silhouette_score, 2)
        });
    }

    return "";

}


function projectCard(project){

    const ready = project.status === "ready";
    const config = project.config || {};

    return `
    <article class="project-card">
        <div class="project-card__head">
            <h3 dir="auto">${escapeHtml(project.name)}</h3>
            <span class="badge ${ready ? "badge--ok" : "badge--warn"}">${ready ? t("projects.ready") : t("projects.pending")}</span>
        </div>
        <ul class="project-card__meta">
            <li>${ready ? escapeHtml(problemLabel(config.problem_type)) : t("projects.analysedOnly")}</li>
            ${ready ? `<li dir="ltr" class="mono">${escapeHtml(config.algorithm || "")}</li>` : ""}
            ${ready && config.target_type ? `<li><span class="badge badge--soft">${targetTypeLabel(config.target_type, config.ai_target && config.ai_target.source)}</span></li>` : ""}
            <li>${t("projects.versionsRows", { versions: project.version_count, rows: project.total_rows })}</li>
            <li>${t("projects.lastChange", { date: formatDate(project.updated_at) })}</li>
        </ul>
        ${ready && project.latest_summary ? `<p class="project-card__metric">${summaryText(project.latest_summary)}</p>` : ""}
        <div class="project-card__actions">
            ${ready ? `
                <a class="button" href="#/project/${project.id}">${t("projects.openDashboard")}</a>
                <button type="button" class="btn--secondary" data-update-project="${project.id}">${t("projects.addData")}</button>`
            : `<a class="button" href="#/project/${project.id}/setup">${t("projects.continueSetup")}</a>`}
            <button type="button" class="btn--icon" title="${t("projects.delete")}" aria-label="${t("projects.delete")}"
                data-delete-project="${project.id}" data-name="${escapeHtml(project.name)}">🗑</button>
        </div>
    </article>
    `;

}


async function deleteProject(projectId, name){

    const ok = await confirmDialog(t("projects.deleteTitle"), t("projects.deleteText", { name }), t("projects.delete"));

    if(!ok){
        return;
    }

    const result = await withLoading(t("loading.deleting"), () => api(`/api/projects/${projectId}`, { method: "DELETE" }));

    if(result){
        projectCache.delete(projectId);
        showToast(t("projects.deleted"), "success");
        if(location.hash === "#/projects"){
            showProjects();
        }
        else {
            location.hash = "#/projects";
        }
    }

}



const newProjectDropzone = setupDropzone(
    document.getElementById("dropzone"),
    document.getElementById("datasetFile"),
    document.getElementById("fileNameLabel"),
    file => {
        const nameInput = document.getElementById("projectName");
        if(file && !nameInput.value.trim()){
            nameInput.placeholder = file.name.replace(/\.[^.]+$/, "");
        }
    }
);


function showNewProject(){

    showView("newProjectView");
    setNav("new");

    document.getElementById("projectName").value = "";
    document.getElementById("projectName").placeholder = t("upload.projectNamePlaceholder");

    if(newProjectDropzone){
        newProjectDropzone.reset();
    }

}


document.getElementById("analyzeBtn").addEventListener("click", async () => {

    const file = document.getElementById("datasetFile").files[0];

    if(!file){
        showToast(t("upload.chooseFirst"), "error");
        return;
    }

    const formData = new FormData();
    formData.append("file", file);
    formData.append("name", document.getElementById("projectName").value.trim());

    const data = await withLoading(t("loading.uploading"), () => api("/api/projects", { form: formData }));

    if(!data){
        return;
    }

    projectCache.set(data.project.id, data.project);
    showToast(t("upload.created"), "success");
    location.hash = `#/project/${data.project.id}/setup`;

});


async function fetchProject(projectId, useCache = false){

    if(useCache && projectCache.has(projectId)){
        return projectCache.get(projectId);
    }

    const data = await api(`/api/projects/${projectId}`);
    projectCache.set(projectId, data.project);
    return data.project;

}


async function showProjectSetup(projectId){

    showView("wizardView");
    setNav(null);

    wizardContainer().innerHTML = `<p class="hint">${t("loading.project")}</p>`;

    let project;
    try {
        project = await fetchProject(projectId, true);
    }
    catch(err){
        if(err.status !== 401){
            showToast(err.message, "error");
            location.hash = "#/projects";
        }
        return;
    }

    startWizard(project);

}


async function showProjectDashboard(projectId){

    showView("projectView");
    setNav(null);

    const view = document.getElementById("projectView");
    view.innerHTML = `<p class="hint">${t("loading.dashboard")}</p>`;

    let project;
    try {
        project = await fetchProject(projectId, false);
    }
    catch(err){
        if(err.status !== 401){
            showToast(err.message, "error");
            location.hash = "#/projects";
        }
        return;
    }

    if(project.status !== "ready"){
        location.hash = `#/project/${project.id}/setup`;
        return;
    }

    const keepSelection = projectPage.project && projectPage.project.id === project.id ? projectPage.selectedVersion : null;
    projectPage.project = project;

    const completed = project.versions.filter(v => v.status === "completed");
    projectPage.selectedVersion = keepSelection || (completed.length ? completed[completed.length - 1].version_no : null);

    renderProjectDashboard();

    if(sessionStorageGet("openUpdate") === String(project.id)){
        sessionStorageSet("openUpdate", null);
        openUpdateModal();
    }

}


function targetLabel(config){

    if(config.problem_type !== "classification"){
        return null;
    }

    if(config.target_type === "pseudo" || config.target_mode === "ai"){
        return config.ai_target && config.ai_target.source === "statistical" ? t("pseudo.labelStatistical") : t("pseudo.labelLLM");
    }

    return config.target;

}


function renderProjectDashboard(){

    const project = projectPage.project;
    const config = project.config || {};
    const view = document.getElementById("projectView");
    const target = targetLabel(config);
    const prefs = config.preferences || {};
    const pseudo = config.ai_target;

    view.innerHTML = `

    <a class="back-link" href="#/projects">${t("nav.allProjects")}</a>

    <section class="panel project-head">

        <div class="project-head__title">
            <h2 id="projectTitle" dir="auto">${escapeHtml(project.name)}</h2>
            <button type="button" class="btn--ghost btn--small" id="renameBtn">${t("dashboard.rename")}</button>
        </div>

        <div class="chips">
            <span class="chip">${escapeHtml(problemLabel(config.problem_type))}</span>
            ${target ? `<span class="chip">${t("dashboard.target")}: <b dir="auto">${escapeHtml(target)}</b></span>` : ""}
            ${config.target_type ? `<span class="chip chip--accent">${targetTypeLabel(config.target_type, pseudo && pseudo.source)}</span>` : ""}
            <span class="chip">${t("dashboard.algorithm")}: <b dir="ltr">${escapeHtml(config.algorithm || "")}</b></span>
            ${prefs.main_goal ? `<span class="chip">${t("dashboard.goal")}: ${goalLabel(prefs.main_goal)}</span>` : ""}
            ${prefs.cluster_count ? `<span class="chip">${t("dashboard.clusterCount")}: ${formatNumber(prefs.cluster_count)}</span>` : ""}
            <span class="chip">${t("projects.versionsRows", { versions: project.version_count, rows: project.total_rows })}</span>
        </div>

        ${pseudo ? `<p class="hint">${t("dashboard.pseudoSummary", {
            source: t(`pseudo.source.${pseudo.source}`),
            features: (pseudo.usable_features || pseudo.features || []).map(escapeHtml)
        })} ${escapeHtml(aiReason(pseudo))}</p>` : ""}

        <div class="button-row">
            <button type="button" id="openUpdateBtn">${t("dashboard.addData")}</button>
            <a class="button btn--secondary" href="#/project/${project.id}/setup">${t("dashboard.changeSettings")}</a>
            <button type="button" class="btn--ghost btn--danger-text" id="deleteProjectBtn">${t("projects.delete")}</button>
        </div>

    </section>

    <section class="panel">
        <div class="section-head section-head--tight">
            <h2>${t("versions.title")}</h2>
            <p class="hint">${t("versions.hint")}</p>
        </div>
        <div class="branches" id="branches" role="tablist">
            ${project.versions.map((version, index) => branchNode(version, project.versions[index - 1])).join("")}
        </div>
        ${project.versions.length > 1 ? `<div id="versionComparison"></div>` : ""}
    </section>

    <section id="versionDetail"></section>

    <section class="panel next-step">
        <h2>${t("dashboard.nextTitle")}</h2>
        <div class="cards cards--2">
            <button type="button" class="choice" id="choiceContinue">
                <span class="choice__icon">⤓</span>
                <span class="choice__title">${t("dashboard.nextContinue")}</span>
                <span class="choice__text">${t("dashboard.nextContinueText")}</span>
            </button>
            <a class="choice" href="#/new">
                <span class="choice__icon">✚</span>
                <span class="choice__title">${t("dashboard.nextNew")}</span>
                <span class="choice__text">${t("dashboard.nextNewText")}</span>
            </a>
        </div>
    </section>
    `;

    view.querySelectorAll("[data-version]").forEach(node => {
        node.addEventListener("click", () => {
            projectPage.selectedVersion = Number(node.dataset.version);
            renderVersionSelection();
        });
    });

    document.getElementById("openUpdateBtn").addEventListener("click", openUpdateModal);
    document.getElementById("choiceContinue").addEventListener("click", openUpdateModal);
    document.getElementById("renameBtn").addEventListener("click", startRename);
    document.getElementById("deleteProjectBtn").addEventListener("click", () => deleteProject(project.id, project.name));

    renderVersionSelection();

}


function versionMainValue(summary){

    if(!summary){
        return null;
    }

    if(summary.macro_f1 !== undefined && summary.macro_f1 !== null){
        return { value: summary.macro_f1, text: formatPercent(summary.macro_f1), label: t("metrics.macro_f1"), percent: true };
    }

    if(summary.silhouette_score !== undefined && summary.silhouette_score !== null){
        return { value: summary.silhouette_score, text: formatNumber(summary.silhouette_score, 2),
                 label: t("versions.clustersQuality", { k: summary.cluster_count }), percent: false };
    }

    if(summary.cluster_count !== undefined){
        return { value: null, text: formatNumber(summary.cluster_count), label: t("metrics.cluster_count"), percent: false };
    }

    return null;

}


function branchNode(version, previous){

    const main = versionMainValue(version.summary);
    const prev = previous ? versionMainValue(previous.summary) : null;

    let delta = "";

    if(main && prev && main.value !== null && prev.value !== null){
        const diff = main.value - prev.value;
        const zero = main.percent ? Math.round(Math.abs(diff) * 1000) === 0 : Math.round(Math.abs(diff) * 100) === 0;
        const shown = main.percent ? formatPercent(Math.abs(diff)) : formatNumber(Math.abs(diff), 2);
        delta = zero
            ? `<span class="delta delta--flat">${t("versions.noChange")}</span>`
            : `<span class="delta ${diff > 0 ? "delta--up" : "delta--down"}">${diff > 0 ? "▲" : "▼"} ${shown}</span>`;
    }

    return `
    <button type="button" class="branch" role="tab" data-version="${version.version_no}">
        <span class="branch__dot">${localizeDigits(version.version_no)}</span>
        <span class="branch__body">
            <span class="branch__title">${t("versions.version", { n: version.version_no })} ${version.version_no === 1 ? `<small>${t("versions.initial")}</small>` : ""}</span>
            <span class="branch__meta">${formatDate(version.created_at)}</span>
            <span class="branch__meta">${version.version_no === 1 ? "" : t("versions.added", { rows: version.rows_added }) + " · "}${t("versions.total", { rows: version.total_rows })}</span>
            ${main ? `<span class="branch__metric">${main.label}: <b>${main.text}</b> ${delta}</span>`
                   : `<span class="branch__metric">${version.status === "completed" ? "" : t("versions.notAnalysed")}</span>`}
        </span>
    </button>
    `;

}


function renderVersionSelection(){

    const project = projectPage.project;

    document.querySelectorAll("[data-version]").forEach(node => {
        const active = Number(node.dataset.version) === projectPage.selectedVersion;
        node.classList.toggle("branch--active", active);
        node.setAttribute("aria-selected", active ? "true" : "false");
    });

    const version = project.versions.find(v => v.version_no === projectPage.selectedVersion);
    const detail = document.getElementById("versionDetail");

    destroyCharts();

    if(!version){
        detail.innerHTML = "";
        renderVersionComparison(project);
        return;
    }

    const isLatest = version.version_no === project.versions[project.versions.length - 1].version_no;

    detail.innerHTML = `
        <div class="version-head">
            <div>
                <h2>${t("versions.dashboardTitle", { n: version.version_no })}${isLatest ? ` <span class="badge badge--primary">${t("versions.latest")}</span>` : ""}</h2>
                <p class="hint">
                    ${t("versions.file")} <span dir="auto">${escapeHtml(version.filename)}</span> ·
                    ${formatDate(version.created_at)} ·
                    ${t("versions.scope", { rows: version.total_rows, n: version.version_no })}
                </p>
            </div>
            <div class="button-row button-row--tight">
                ${version.status === "completed" ? `
                    <button type="button" class="btn--secondary btn--small" data-export="json">${t("versions.exportJson")}</button>
                    <button type="button" class="btn--secondary btn--small" data-export="csv">${t("versions.exportCsv")}</button>` : ""}
                ${isLatest && version.version_no > 1 ? `<button type="button" class="btn--ghost btn--small btn--danger-text" id="deleteVersionBtn">${t("versions.delete")}</button>` : ""}
            </div>
        </div>
        ${(version.issues || []).length ? renderIssues(version.issues, t("issues.versionTitle")) : ""}
        <div class="result" id="versionDashboard"></div>
    `;

    const deleteBtn = document.getElementById("deleteVersionBtn");
    if(deleteBtn){
        deleteBtn.addEventListener("click", () => deleteVersion(version.version_no));
    }

    detail.querySelectorAll("[data-export]").forEach(button => {
        button.addEventListener("click", () => exportAudit(version.version_no, button.dataset.export));
    });

    const dashboard = document.getElementById("versionDashboard");

    if(version.status !== "completed" || !version.result){
        const error = version.error && typeof version.error === "object" ? tCode("errors", version.error) : (version.error || t("versions.notAnalysedYet"));
        dashboard.innerHTML = `<div class="error">${escapeHtml(error)}</div>`;
    }
    else {
        renderDashboard(version.result, dashboard);
    }

    renderVersionComparison(project);

}


async function exportAudit(versionNo, format){

    const project = projectPage.project;
    const name = `guidml_project${project.id}_v${versionNo}_audit.${format}`;

    try {
        await download(`/api/projects/${project.id}/versions/${versionNo}/audit?format=${format}`, name);
        showToast(t("versions.exported"), "success");
    }
    catch(err){
        showToast(err.message, "error");
    }

}


function renderVersionComparison(project){

    const box = document.getElementById("versionComparison");

    if(!box){
        return;
    }

    const versions = project.versions.filter(v => v.status === "completed" && v.summary);
    const isClassification = (project.config || {}).problem_type === "classification";
    const labels = versions.map(v => t("versions.version", { n: v.version_no }));

    const rows = versions.map(v => {
        const s = v.summary;
        if(isClassification){
            return `<tr><th>${t("versions.version", { n: v.version_no })}</th><td>${formatNumber(v.total_rows)}</td>
                <td>${formatPercent(s.accuracy)}</td><td>${formatPercent(s.balanced_accuracy)}</td><td>${formatPercent(s.macro_f1)}</td>
                <td>${formatPercent(s.weighted_f1)}</td><td>${s.fixed_holdout_macro_f1 === null || s.fixed_holdout_macro_f1 === undefined ? "-" : formatPercent(s.fixed_holdout_macro_f1)}</td></tr>`;
        }
        return `<tr><th>${t("versions.version", { n: v.version_no })}</th><td>${formatNumber(v.total_rows)}</td>
            <td>${formatNumber(s.cluster_count)}</td><td>${s.silhouette_score === null || s.silhouette_score === undefined ? "-" : formatNumber(s.silhouette_score, 3)}</td>
            <td>${s.davies_bouldin_index === null || s.davies_bouldin_index === undefined ? "-" : formatNumber(s.davies_bouldin_index, 3)}</td><td>${formatPercent(s.noise_ratio)}</td></tr>`;
    }).join("");

    box.innerHTML = `
        <div class="comparison">
            <div class="comparison__chart">
                <h3>${t("versions.trend")}</h3>
                <div class="chart-box"><canvas id="versionChart"></canvas></div>
            </div>
            <div class="comparison__table">
                <table class="data-table">
                    <thead>${isClassification
                        ? `<tr><th>${t("versions.versionCol")}</th><th>${t("versions.rowsCol")}</th><th>${t("metrics.accuracy")}</th><th>${t("metrics.balanced_accuracy")}</th><th>${t("metrics.macro_f1")}</th><th>${t("metrics.weighted_f1")}</th><th>${t("versions.fixedCol")}</th></tr>`
                        : `<tr><th>${t("versions.versionCol")}</th><th>${t("versions.rowsCol")}</th><th>${t("metrics.cluster_count")}</th><th>${t("metrics.silhouette")}</th><th>${t("metrics.davies_bouldin")}</th><th>${t("metrics.noise_ratio")}</th></tr>`}
                    </thead>
                    <tbody>${rows}</tbody>
                </table>
                <p class="hint">${t(isClassification ? "versions.comparisonNote" : "versions.comparisonNoteClustering")}</p>
            </div>
        </div>
    `;

    if(!window.Chart){
        return;
    }

    const line = (label, data, color, extra = {}) => ({
        label, data, borderColor: color, backgroundColor: color, tension: 0.3, pointRadius: 4, pointHoverRadius: 6, ...extra
    });

    let datasets;
    let scales;

    if(isClassification){
        datasets = [
            line(t("metrics.accuracy"), versions.map(v => v.summary.accuracy * 100), PALETTE[0]),
            line(t("metrics.macro_f1"), versions.map(v => v.summary.macro_f1 * 100), PALETTE[1]),
            line(t("metrics.balanced_accuracy"), versions.map(v => v.summary.balanced_accuracy * 100), PALETTE[2]),
            line(t("versions.fixedCol"), versions.map(v => v.summary.fixed_holdout_macro_f1 === null ? null : v.summary.fixed_holdout_macro_f1 * 100), PALETTE[3], { borderDash: [6, 4] })
        ];
        scales = {
            x: { reverse: isRTL() },
            y: { grace: "10%", title: { display: true, text: t("dashboard.classification.percent") }, ticks: numberTicks() }
        };
    }
    else {
        datasets = [
            line(t("metrics.silhouette"), versions.map(v => v.summary.silhouette_score), PALETTE[0], { yAxisID: "y" }),
            line(t("metrics.cluster_count"), versions.map(v => v.summary.cluster_count), PALETTE[3], { yAxisID: "y1", borderDash: [6, 4] })
        ];
        scales = {
            x: { reverse: isRTL() },
            y: { suggestedMin: 0, suggestedMax: 1, title: { display: true, text: t("metrics.silhouette") }, position: isRTL() ? "right" : "left", ticks: numberTicks() },
            y1: { beginAtZero: true, ticks: { precision: 0, callback: v => formatNumber(v) }, title: { display: true, text: t("metrics.cluster_count") }, position: isRTL() ? "left" : "right", grid: { drawOnChartArea: false } }
        };
    }

    trackChart(new Chart(document.getElementById("versionChart"), {
        type: "line",
        data: { labels, datasets },
        options: { responsive: true, maintainAspectRatio: false, interaction: { mode: "index", intersect: false },
                   plugins: { legend: legendOptions(), tooltip: tooltipOptions() }, scales }
    }));

}


async function deleteVersion(versionNo){

    const ok = await confirmDialog(t("versions.deleteTitle"), t("versions.deleteText", { n: versionNo }), t("versions.delete"));

    if(!ok){
        return;
    }

    const data = await withLoading(t("loading.deleting"),
        () => api(`/api/projects/${projectPage.project.id}/versions/${versionNo}`, { method: "DELETE" }));

    if(!data){
        return;
    }

    projectCache.set(data.project.id, data.project);
    projectPage.project = data.project;
    projectPage.selectedVersion = data.project.versions[data.project.versions.length - 1].version_no;

    showToast(t("versions.deleted"), "success");
    renderProjectDashboard();

}


function startRename(){

    const title = document.getElementById("projectTitle");
    const current = projectPage.project.name;

    title.outerHTML = `
        <form class="rename" id="renameForm">
            <input class="input" id="renameInput" maxlength="120" value="${escapeHtml(current)}" aria-label="${t("upload.projectName")}" dir="auto">
            <button type="submit" class="btn--small">${t("common.save")}</button>
            <button type="button" class="btn--ghost btn--small" id="renameCancel">${t("common.cancel")}</button>
        </form>
    `;

    document.getElementById("renameBtn").hidden = true;

    const input = document.getElementById("renameInput");
    input.focus();
    input.select();

    document.getElementById("renameCancel").addEventListener("click", renderProjectDashboard);

    document.getElementById("renameForm").addEventListener("submit", async event => {

        event.preventDefault();

        const name = input.value.trim();

        if(!name){
            showToast(t("errors.PROJECT_NAME_EMPTY"), "error");
            return;
        }

        const data = await withLoading(t("loading.saving"),
            () => api(`/api/projects/${projectPage.project.id}`, { method: "PATCH", json: { name } }));

        if(data){
            projectCache.set(data.project.id, data.project);
            projectPage.project = data.project;
            renderProjectDashboard();
        }

    });

}


const updateDropzone = setupDropzone(
    document.getElementById("updateDropzone"),
    document.getElementById("updateFile"),
    document.getElementById("updateFileName"),
    () => { document.getElementById("updateError").textContent = ""; }
);


function openUpdateModal(){

    const project = projectPage.project;

    if(!project){
        return;
    }

    if(updateDropzone){
        updateDropzone.reset();
    }

    document.getElementById("updateError").textContent = "";
    document.getElementById("updateColumns").innerHTML = `
        ${t("update.columns")}
        <div class="chips chips--small">${project.columns.map(c => `<span class="chip" dir="auto">${escapeHtml(c)}</span>`).join("")}</div>
    `;

    openModal("updateModal");

}


document.getElementById("updateSubmitBtn").addEventListener("click", async () => {

    const file = document.getElementById("updateFile").files[0];
    const errorBox = document.getElementById("updateError");

    if(!file){
        errorBox.textContent = t("update.chooseFirst");
        return;
    }

    const formData = new FormData();
    formData.append("file", file);

    const projectId = projectPage.project.id;

    showLoading(t("loading.addingVersion"));

    try {
        const data = await api(`/api/projects/${projectId}/versions`, { form: formData });

        closeModal("updateModal");

        projectCache.set(projectId, data.project);
        projectPage.project = data.project;
        projectPage.selectedVersion = data.version_no;

        renderProjectDashboard();

        showToast(t("update.done", { n: data.version_no }), "success");

        document.getElementById("versionDetail").scrollIntoView({ behavior: "smooth" });
    }
    catch(err){
        if(err.status !== 401){
            errorBox.textContent = err.message;
        }
    }
    finally {
        hideLoading();
    }

});
