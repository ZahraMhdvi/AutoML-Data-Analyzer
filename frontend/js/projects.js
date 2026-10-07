// ---------------------------------------------------------------------------
// Profile (projects list), new project upload, project dashboard & versions
// ---------------------------------------------------------------------------

const projectCache = new Map();

let versionChartInstance = null;

const projectPage = {

    project: null,

    selectedVersion: null

};


const PROBLEM_LABELS = {
    classification: "پیش‌بینی نتیجه (Classification)",
    clustering: "گروه‌بندی (Clustering)"
};


const GOAL_LABELS = {
    accuracy: "بیشترین دقت",
    speed: "سرعت بالا",
    interpretability: "قابل توضیح بودن"
};


// ---------------------------------------------------------------------------
// Profile: list of projects
// ---------------------------------------------------------------------------

async function showProjects(){

    showView("projectsView");
    setNav("projects");

    const view =
        document.getElementById("projectsView");

    view.innerHTML = `<p class="hint">در حال بارگذاری پروژه‌ها...</p>`;

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

    const projects =
        data.projects;

    const user =
        session.user || {};

    const readyCount =
        projects.filter(p => p.status === "ready").length;

    const versionCount =
        projects.reduce((sum, p) => sum + p.version_count, 0);

    view.innerHTML = `

        <div class="profile">

            <div class="profile__avatar">${escapeHtml((user.name || "?").charAt(0))}</div>

            <div class="profile__info">
                <h2>سلام ${escapeHtml(user.name || "")}</h2>
                <p dir="ltr" class="profile__email">${escapeHtml(user.email || "")}</p>
                <p class="hint">عضو از ${formatDate(user.created_at, false)}</p>
            </div>

            <ul class="profile__stats">
                <li><b>${formatNumber(projects.length)}</b><span>پروژه</span></li>
                <li><b>${formatNumber(readyCount)}</b><span>داشبورد آماده</span></li>
                <li><b>${formatNumber(versionCount)}</b><span>نسخه داده</span></li>
            </ul>

        </div>

        <div class="section-head">
            <h2>پروژه‌های من</h2>
            <a class="button" href="#/new">+ پروژه جدید (دیتاست جدید)</a>
        </div>

        ${
            projects.length === 0
            ?
            `
            <div class="empty">
                <div class="empty__icon">▤</div>
                <h3>هنوز پروژه‌ای ندارید</h3>
                <p>اولین دیتاست خود را بارگذاری کنید. سیستم آن را تحلیل می‌کند، روش و الگوریتم مناسب را پیشنهاد می‌دهد و نتیجه را در یک داشبورد نگه می‌دارد.</p>
                <a class="button" href="#/new">بارگذاری اولین دیتاست</a>
            </div>
            `
            :
            `<div class="project-grid">${projects.map(projectCard).join("")}</div>`
        }

    `;

    view.querySelectorAll("[data-update-project]").forEach(button => {

        button.addEventListener("click", () => {
            sessionStorageSet("openUpdate", button.dataset.updateProject);
            location.hash = `#/project/${button.dataset.updateProject}`;
        });

    });

    view.querySelectorAll("[data-delete-project]").forEach(button => {

        button.addEventListener("click", () =>
            deleteProject(Number(button.dataset.deleteProject), button.dataset.name)
        );

    });

}


function summaryText(summary){

    if(!summary){
        return "";
    }

    if(summary.accuracy !== undefined && summary.accuracy !== null){
        return `دقت مدل: <b>${formatPercent(summary.accuracy)}</b>`;
    }

    if(summary.cluster_count !== undefined){

        const quality =
            summary.silhouette_score !== null && summary.silhouette_score !== undefined
            ? ` · کیفیت تفکیک: <b>${formatNumber(Math.round(summary.silhouette_score * 100) / 100)}</b>`
            : "";

        return `${formatNumber(summary.cluster_count)} گروه${quality}`;

    }

    return "";

}


function projectCard(project){

    const ready =
        project.status === "ready";

    const config =
        project.config || {};

    return `

    <article class="project-card">

        <div class="project-card__head">
            <h3 dir="auto">${escapeHtml(project.name)}</h3>
            <span class="badge ${ready ? "badge--ok" : "badge--warn"}">
                ${ready ? "داشبورد آماده" : "در انتظار تکمیل تنظیمات"}
            </span>
        </div>

        <ul class="project-card__meta">
            <li>${ready ? escapeHtml(PROBLEM_LABELS[config.problem_type] || "") : "تحلیل اولیه انجام شده است"}</li>
            ${ready ? `<li dir="ltr">${escapeHtml(config.algorithm || "")}</li>` : ""}
            <li>${formatNumber(project.version_count)} نسخه · ${formatNumber(project.total_rows)} ردیف</li>
            <li>آخرین تغییر: ${formatDate(project.updated_at)}</li>
        </ul>

        ${ready && project.latest_summary ? `<p class="project-card__metric">${summaryText(project.latest_summary)}</p>` : ""}

        <div class="project-card__actions">

            ${
                ready
                ?
                `
                <a class="button" href="#/project/${project.id}">مشاهده داشبورد</a>
                <button type="button" class="btn--secondary" data-update-project="${project.id}">افزودن داده جدید</button>
                `
                :
                `<a class="button" href="#/project/${project.id}/setup">ادامه تنظیم تحلیل</a>`
            }

            <button type="button" class="btn--icon" title="حذف پروژه" aria-label="حذف پروژه"
                data-delete-project="${project.id}" data-name="${escapeHtml(project.name)}">🗑</button>

        </div>

    </article>

    `;

}


async function deleteProject(projectId, name){

    const ok = await confirmDialog(
        "حذف پروژه",
        `پروژه «${name}» با همه نسخه‌ها و نتایجش برای همیشه حذف می‌شود. ادامه می‌دهید؟`,
        "حذف پروژه"
    );

    if(!ok){
        return;
    }

    const result = await withLoading(
        "در حال حذف پروژه...",
        () => api(`/api/projects/${projectId}`, { method: "DELETE" })
    );

    if(result){

        projectCache.delete(projectId);

        showToast("پروژه حذف شد", "success");

        if(location.hash === "#/projects"){
            showProjects();
        }
        else {
            location.hash = "#/projects";
        }

    }

}


// ---------------------------------------------------------------------------
// New project (a completely new dataset)
// ---------------------------------------------------------------------------

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
    document.getElementById("projectName").placeholder = "مثلاً: تحلیل مشتریان فروشگاه";

    if(newProjectDropzone){
        newProjectDropzone.reset();
    }

}


document.getElementById("analyzeBtn").addEventListener("click", async () => {

    const file =
        document.getElementById("datasetFile").files[0];

    if(!file){

        showToast("ابتدا فایل دیتاست را انتخاب کنید", "error");

        return;

    }

    const formData =
        new FormData();

    formData.append("file", file);
    formData.append("name", document.getElementById("projectName").value.trim());

    const data = await withLoading(
        "در حال بارگذاری و تحلیل دیتاست...",
        () => api("/api/projects", { form: formData })
    );

    if(!data){
        return;
    }

    projectCache.set(data.project.id, data.project);

    showToast("پروژه ساخته شد؛ حالا نوع تحلیل را انتخاب کنید", "success");

    location.hash = `#/project/${data.project.id}/setup`;

});


// ---------------------------------------------------------------------------
// Loading a project
// ---------------------------------------------------------------------------

async function fetchProject(projectId, useCache = false){

    if(useCache && projectCache.has(projectId)){
        return projectCache.get(projectId);
    }

    const data =
        await api(`/api/projects/${projectId}`);

    projectCache.set(projectId, data.project);

    return data.project;

}


async function showProjectSetup(projectId){

    showView("wizardView");
    setNav(null);

    wizardContainer().innerHTML = `<p class="hint">در حال بارگذاری پروژه...</p>`;

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


// ---------------------------------------------------------------------------
// Project dashboard: versions ("branches") of the dataset
// ---------------------------------------------------------------------------

async function showProjectDashboard(projectId){

    showView("projectView");
    setNav(null);

    const view =
        document.getElementById("projectView");

    view.innerHTML = `<p class="hint">در حال بارگذاری داشبورد...</p>`;

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

    projectPage.project = project;

    const completed =
        project.versions.filter(v => v.status === "completed");

    projectPage.selectedVersion =
        completed.length ? completed[completed.length - 1].version_no : null;

    renderProjectDashboard();

    if(sessionStorageGet("openUpdate") === String(project.id)){
        sessionStorageSet("openUpdate", null);
        openUpdateModal();
    }

}


function renderProjectDashboard(){

    const project =
        projectPage.project;

    const config =
        project.config || {};

    const view =
        document.getElementById("projectView");

    const targetLabel =
        config.problem_type !== "classification"
        ? null
        : (config.target_mode === "ai"
            ? ((config.ai_target && config.ai_target.method === "statistical")
                ? "Target ساخته‌شده (روش آماری)"
                : "Target هوشمند (ساخته‌شده با AI)")
            : config.target);

    const prefs =
        config.preferences || {};

    view.innerHTML = `

    <a class="back-link" href="#/projects">→ همه پروژه‌ها</a>

    <section class="panel project-head">

        <div class="project-head__title">
            <h2 id="projectTitle" dir="auto">${escapeHtml(project.name)}</h2>
            <button type="button" class="btn--ghost btn--small" id="renameBtn">تغییر نام</button>
        </div>

        <div class="chips">
            <span class="chip">${escapeHtml(PROBLEM_LABELS[config.problem_type] || "")}</span>
            ${targetLabel ? `<span class="chip">نتیجه: <b dir="auto">${escapeHtml(targetLabel)}</b></span>` : ""}
            <span class="chip">الگوریتم: <b dir="ltr">${escapeHtml(config.algorithm || "")}</b></span>
            ${prefs.main_goal ? `<span class="chip">هدف: ${GOAL_LABELS[prefs.main_goal] || ""}</span>` : ""}
            ${prefs.cluster_count ? `<span class="chip">تعداد گروه: ${formatNumber(prefs.cluster_count)}</span>` : ""}
            <span class="chip">${formatNumber(project.version_count)} نسخه · ${formatNumber(project.total_rows)} ردیف</span>
        </div>

        ${
            config.ai_target
            ?
            `<p class="hint">${config.ai_target.method === "statistical" ? "Target" : "Target هوشمند"} از ترکیب ستون‌های ${(config.ai_target.important_features || []).map(escapeHtml).join("، ")} ساخته شده است. ${escapeHtml(config.ai_target.reason || "")}</p>`
            :
            ""
        }

        <div class="button-row">
            <button type="button" id="openUpdateBtn">+ افزودن داده جدید به همین دیتاست</button>
            <a class="button btn--secondary" href="#/project/${project.id}/setup">تغییر تنظیمات تحلیل</a>
            <button type="button" class="btn--ghost btn--danger-text" id="deleteProjectBtn">حذف پروژه</button>
        </div>

    </section>

    <section class="panel">

        <div class="section-head section-head--tight">
            <h2>نسخه‌های داده (شاخه‌ها)</h2>
            <p class="hint">هر نسخه = داده‌های قبلی + رکوردهای جدید. روی هر نسخه کلیک کنید تا نتیجه کامل آن را ببینید.</p>
        </div>

        <div class="branches" id="branches" role="tablist">
            ${project.versions.map((version, index) => branchNode(version, project.versions[index - 1])).join("")}
        </div>

        ${project.versions.length > 1 ? `<div id="versionComparison"></div>` : ""}

    </section>

    <section id="versionDetail"></section>

    <section class="panel next-step">

        <h2>داده جدید دارید؟</h2>

        <div class="cards cards--2">

            <button type="button" class="choice" id="choiceContinue">
                <span class="choice__icon">⤓</span>
                <span class="choice__title">ادامه همین دیتاست</span>
                <span class="choice__text">رکوردهای جدیدِ همین داده (با همین ستون‌ها) را اضافه کنید تا یک نسخه جدید ساخته شود و پیشرفت آن را با نسخه‌های قبلی مقایسه کنید.</span>
            </button>

            <a class="choice" href="#/new">
                <span class="choice__icon">✚</span>
                <span class="choice__title">دیتاست کاملاً جدید</span>
                <span class="choice__text">یک پروژه مستقل جدید با داشبورد جداگانه بسازید؛ هیچ ارتباطی با این پروژه نخواهد داشت.</span>
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
    document.getElementById("deleteProjectBtn").addEventListener("click", () =>
        deleteProject(project.id, project.name)
    );

    renderVersionSelection();

}


function versionMainValue(summary){

    if(!summary){
        return null;
    }

    if(summary.accuracy !== undefined && summary.accuracy !== null){
        return { value: summary.accuracy, text: formatPercent(summary.accuracy), label: "دقت" };
    }

    if(summary.silhouette_score !== undefined && summary.silhouette_score !== null){
        return {
            value: summary.silhouette_score,
            text: formatNumber(Math.round(summary.silhouette_score * 100) / 100),
            label: `${formatNumber(summary.cluster_count)} گروه · کیفیت`
        };
    }

    if(summary.cluster_count !== undefined){
        return { value: null, text: formatNumber(summary.cluster_count), label: "تعداد گروه" };
    }

    return null;

}


function branchNode(version, previous){

    const main =
        versionMainValue(version.summary);

    const prev =
        previous ? versionMainValue(previous.summary) : null;

    let delta = "";

    if(main && prev && main.value !== null && prev.value !== null){

        const diff =
            main.value - prev.value;

        const isPercent =
            version.summary.accuracy !== undefined && version.summary.accuracy !== null;

        const shown =
            isPercent
            ? formatNumber(Math.round(Math.abs(diff) * 1000) / 10) + "٪"
            : formatNumber(Math.round(Math.abs(diff) * 100) / 100);

        const roundedZero =
            isPercent ? Math.round(Math.abs(diff) * 1000) === 0 : Math.round(Math.abs(diff) * 100) === 0;

        if(roundedZero){
            delta = `<span class="delta delta--flat">بدون تغییر</span>`;
        }
        else {
            delta = `<span class="delta ${diff > 0 ? "delta--up" : "delta--down"}">${diff > 0 ? "▲" : "▼"} ${shown}</span>`;
        }

    }

    return `

    <button type="button" class="branch" role="tab" data-version="${version.version_no}">

        <span class="branch__dot">${toFaDigits(version.version_no)}</span>

        <span class="branch__body">

            <span class="branch__title">
                نسخه ${toFaDigits(version.version_no)}
                ${version.version_no === 1 ? `<small>(داده اولیه)</small>` : ""}
            </span>

            <span class="branch__meta">${formatDate(version.created_at)}</span>

            <span class="branch__meta">
                ${version.version_no === 1 ? "" : `+${formatNumber(version.rows_added)} ردیف · `}کل ${formatNumber(version.total_rows)} ردیف
            </span>

            ${
                main
                ?
                `<span class="branch__metric">${main.label}: <b>${main.text}</b> ${delta}</span>`
                :
                `<span class="branch__metric">${version.status === "completed" ? "" : "تحلیل نشده"}</span>`
            }

        </span>

    </button>

    `;

}


function renderVersionSelection(){

    const project =
        projectPage.project;

    document.querySelectorAll("[data-version]").forEach(node => {

        const active =
            Number(node.dataset.version) === projectPage.selectedVersion;

        node.classList.toggle("branch--active", active);
        node.setAttribute("aria-selected", active ? "true" : "false");

    });

    const version =
        project.versions.find(v => v.version_no === projectPage.selectedVersion);

    const detail =
        document.getElementById("versionDetail");

    if(!version){
        detail.innerHTML = "";
        renderVersionComparison(project);
        return;
    }

    const isLatest =
        version.version_no === project.versions[project.versions.length - 1].version_no;

    detail.innerHTML = `

        <div class="version-head">

            <div>
                <h2>داشبورد نسخه ${toFaDigits(version.version_no)}${isLatest ? ` <span class="badge badge--primary">آخرین نسخه</span>` : ""}</h2>
                <p class="hint">
                    فایل: <span dir="auto">${escapeHtml(version.filename)}</span> ·
                    ${formatDate(version.created_at)} ·
                    تحلیل روی ${formatNumber(version.total_rows)} ردیف (نسخه‌های ۱ تا ${toFaDigits(version.version_no)})
                </p>
            </div>

            ${
                isLatest && version.version_no > 1
                ?
                `<button type="button" class="btn--ghost btn--small btn--danger-text" id="deleteVersionBtn">حذف این نسخه</button>`
                :
                ""
            }

        </div>

        <div class="result" id="versionDashboard"></div>

    `;

    const deleteBtn =
        document.getElementById("deleteVersionBtn");

    if(deleteBtn){
        deleteBtn.addEventListener("click", () => deleteVersion(version.version_no));
    }

    const dashboard =
        document.getElementById("versionDashboard");

    if(version.status !== "completed" || !version.result){

        dashboard.innerHTML = `<div class="error">${escapeHtml(version.error || "این نسخه هنوز تحلیل نشده است")}</div>`;

    }
    else {

        renderDashboard(version.result, dashboard);

    }

    // The comparison chart lives outside the version dashboard; redraw it
    // because renderDashboard() clears every chart on the page.
    renderVersionComparison(project);

}


function renderVersionComparison(project){

    const box =
        document.getElementById("versionComparison");

    if(!box){
        return;
    }

    const versions =
        project.versions.filter(v => v.status === "completed" && v.summary);

    const isClassification =
        (project.config || {}).problem_type === "classification";

    const labels =
        versions.map(v => "نسخه " + toFaDigits(v.version_no));

    const rows =
        versions.map(v => {

            const s = v.summary;

            if(isClassification){
                return `
                <tr>
                    <th>نسخه ${toFaDigits(v.version_no)}</th>
                    <td>${formatNumber(v.total_rows)}</td>
                    <td>${formatPercent(s.accuracy)}</td>
                    <td>${formatPercent(s.precision)}</td>
                    <td>${formatPercent(s.recall)}</td>
                    <td>${formatPercent(s.f1)}</td>
                </tr>`;
            }

            return `
                <tr>
                    <th>نسخه ${toFaDigits(v.version_no)}</th>
                    <td>${formatNumber(v.total_rows)}</td>
                    <td>${formatNumber(s.cluster_count)}</td>
                    <td>${s.silhouette_score === null || s.silhouette_score === undefined ? "-" : formatNumber(Math.round(s.silhouette_score * 100) / 100)}</td>
                    <td>${formatNumber(s.noise_points)}</td>
                </tr>`;

        }).join("");

    box.innerHTML = `

        <div class="comparison">

            <div class="comparison__chart">
                <h3>روند تغییر نتایج در نسخه‌ها</h3>
                <div class="chart-box"><canvas id="versionChart"></canvas></div>
            </div>

            <div class="comparison__table">
                <table class="data-table">
                    <thead>
                        ${
                            isClassification
                            ?
                            `<tr><th>نسخه</th><th>ردیف‌ها</th><th>دقت کلی</th><th>دقت پیش‌بینی</th><th>شناسایی موارد</th><th>تعادل (F1)</th></tr>`
                            :
                            `<tr><th>نسخه</th><th>ردیف‌ها</th><th>تعداد گروه</th><th>کیفیت تفکیک</th><th>داده غیرعادی</th></tr>`
                        }
                    </thead>
                    <tbody>${rows}</tbody>
                </table>
            </div>

        </div>

    `;

    if(!window.Chart){
        return;
    }

    const canvas =
        document.getElementById("versionChart");

    const line = (label, data, color, extra = {}) => ({
        label,
        data,
        borderColor: color,
        backgroundColor: color,
        tension: 0.3,
        pointRadius: 5,
        pointHoverRadius: 7,
        ...extra
    });

    let datasets;
    let scales;

    if(isClassification){

        datasets = [
            line("دقت کلی", versions.map(v => v.summary.accuracy * 100), "#ec4899"),
            line("دقت پیش‌بینی", versions.map(v => v.summary.precision * 100), "#8b5cf6"),
            line("شناسایی موارد درست", versions.map(v => v.summary.recall * 100), "#06b6d4"),
            line("تعادل عملکرد (F1)", versions.map(v => v.summary.f1 * 100), "#f97316")
        ];

        scales = {
            y: { grace: "10%", title: { display: true, text: "درصد" } }
        };

    }
    else {

        datasets = [
            line("کیفیت تفکیک گروه‌ها", versions.map(v => v.summary.silhouette_score), "#ec4899", { yAxisID: "y" }),
            line("تعداد گروه‌ها", versions.map(v => v.summary.cluster_count), "#8b5cf6", { yAxisID: "y1", borderDash: [6, 4] })
        ];

        scales = {
            y: { suggestedMin: 0, suggestedMax: 1, title: { display: true, text: "کیفیت تفکیک" }, position: "left" },
            y1: { beginAtZero: true, ticks: { precision: 0 }, title: { display: true, text: "تعداد گروه" }, position: "right", grid: { drawOnChartArea: false } }
        };

    }

    if(versionChartInstance){
        try { versionChartInstance.destroy(); } catch(err){ /* already destroyed */ }
    }

    versionChartInstance = new Chart(canvas, {
        type: "line",
        data: { labels, datasets },
        options: {
            responsive: true,
            maintainAspectRatio: false,
            interaction: { mode: "index", intersect: false },
            plugins: { legend: { position: "bottom" } },
            scales
        }
    });

}


async function deleteVersion(versionNo){

    const ok = await confirmDialog(
        "حذف نسخه",
        `نسخه ${toFaDigits(versionNo)} و رکوردهایی که در آن اضافه شده بود حذف می‌شود. نسخه‌های قبلی دست نمی‌خورند.`,
        "حذف نسخه"
    );

    if(!ok){
        return;
    }

    const data = await withLoading(
        "در حال حذف نسخه...",
        () => api(`/api/projects/${projectPage.project.id}/versions/${versionNo}`, { method: "DELETE" })
    );

    if(!data){
        return;
    }

    projectCache.set(data.project.id, data.project);
    projectPage.project = data.project;
    projectPage.selectedVersion = data.project.versions[data.project.versions.length - 1].version_no;

    showToast("نسخه حذف شد", "success");

    renderProjectDashboard();

}


function startRename(){

    const title =
        document.getElementById("projectTitle");

    const current =
        projectPage.project.name;

    title.outerHTML = `
        <form class="rename" id="renameForm">
            <input class="input" id="renameInput" maxlength="120" value="${escapeHtml(current)}" aria-label="نام پروژه">
            <button type="submit" class="btn--small">ذخیره</button>
            <button type="button" class="btn--ghost btn--small" id="renameCancel">انصراف</button>
        </form>
    `;

    document.getElementById("renameBtn").hidden = true;

    const input =
        document.getElementById("renameInput");

    input.focus();
    input.select();

    document.getElementById("renameCancel").addEventListener("click", renderProjectDashboard);

    document.getElementById("renameForm").addEventListener("submit", async event => {

        event.preventDefault();

        const name =
            input.value.trim();

        if(!name){
            showToast("نام پروژه نمی‌تواند خالی باشد", "error");
            return;
        }

        const data = await withLoading(
            "در حال ذخیره...",
            () => api(`/api/projects/${projectPage.project.id}`, { method: "PATCH", json: { name } })
        );

        if(data){
            projectCache.set(data.project.id, data.project);
            projectPage.project = data.project;
            renderProjectDashboard();
        }

    });

}


// ---------------------------------------------------------------------------
// Upload new records for the current project
// ---------------------------------------------------------------------------

const updateDropzone = setupDropzone(
    document.getElementById("updateDropzone"),
    document.getElementById("updateFile"),
    document.getElementById("updateFileName"),
    () => { document.getElementById("updateError").textContent = ""; }
);


function openUpdateModal(){

    const project =
        projectPage.project;

    if(!project){
        return;
    }

    if(updateDropzone){
        updateDropzone.reset();
    }

    document.getElementById("updateError").textContent = "";

    document.getElementById("updateColumns").innerHTML = `
        فایل جدید باید دقیقاً همین ستون‌ها را داشته باشد (ترتیب مهم نیست):
        <div class="chips chips--small">${project.columns.map(c => `<span class="chip" dir="auto">${escapeHtml(c)}</span>`).join("")}</div>
    `;

    openModal("updateModal");

}


document.getElementById("updateSubmitBtn").addEventListener("click", async () => {

    const file =
        document.getElementById("updateFile").files[0];

    const errorBox =
        document.getElementById("updateError");

    if(!file){
        errorBox.textContent = "ابتدا فایل داده‌های جدید را انتخاب کنید";
        return;
    }

    const formData =
        new FormData();

    formData.append("file", file);

    const projectId =
        projectPage.project.id;

    showLoading("در حال افزودن داده‌های جدید و تحلیل نسخه جدید...");

    try {

        const data = await api(
            `/api/projects/${projectId}/versions`,
            { form: formData }
        );

        closeModal("updateModal");

        projectCache.set(projectId, data.project);
        projectPage.project = data.project;
        projectPage.selectedVersion = data.version_no;

        renderProjectDashboard();

        showToast(`نسخه ${toFaDigits(data.version_no)} ساخته و تحلیل شد`, "success");

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
