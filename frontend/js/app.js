// ---------------------------------------------------------------------------
// Analysis wizard: problem type -> target -> preferences -> model -> results
// ---------------------------------------------------------------------------
//
// The dataset is stored on the server as part of a project, so every step
// sends the project id instead of re-uploading the file.

const wizard = {

    project: null,

    analysis: null,

    problemType: null,

    target: null,

    // "detected" | "manual" | "ai" (classification) or "clustering"
    targetMode: null,

    preferences: null,

    aiTarget: null,

    history: []

};

// Kept for compatibility with older code paths.
window.analysisData = null;


function wizardContainer(){

    return document.getElementById("result");

}


function startWizard(project){

    wizard.project = project;
    wizard.analysis = project.analysis;
    wizard.problemType = null;
    wizard.target = null;
    wizard.targetMode = null;
    wizard.preferences = null;
    wizard.aiTarget = null;
    wizard.history = [];

    window.analysisData = project.analysis;

    document.getElementById("wizardTitle").textContent =
        "پروژه: " + project.name;

    const backLink =
        document.getElementById("wizardProjectLink");

    const notice =
        document.getElementById("wizardNotice");

    if(project.status === "ready"){

        backLink.href = `#/project/${project.id}`;
        backLink.textContent = "→ بازگشت به داشبورد پروژه";

        notice.hidden = false;
        notice.innerHTML =
            `شما در حال <b>تغییر تنظیمات تحلیل</b> این پروژه هستید. پس از انتخاب مدل، همه ${formatNumber(project.version_count)} نسخه داده با تنظیمات جدید دوباره تحلیل می‌شوند تا قابل مقایسه بمانند.`;

    }
    else {

        backLink.href = "#/projects";
        backLink.textContent = "→ بازگشت به پروژه‌ها (پیشرفت شما ذخیره می‌شود)";

        notice.hidden = true;

    }

    setProblemSteps("classification");
    updateStepper("classification");

    wizardGo(renderAnalysis);

}


function wizardGo(stepFn){

    wizard.history.push(stepFn);

    stepFn();

    refreshWizardBack();

    window.scrollTo({ top: 0, behavior: "smooth" });

}


function wizardBack(){

    if(wizard.history.length < 2){
        return;
    }

    wizard.history.pop();

    const previous =
        wizard.history[wizard.history.length - 1];

    previous();

    refreshWizardBack();

}


function refreshWizardBack(){

    document.getElementById("wizardBackBtn").hidden =
        wizard.history.length < 2;

}


document.getElementById("wizardBackBtn")
    .addEventListener("click", wizardBack);


// ---------------------------------------------------------------------------
// Step 2: problem type
// ---------------------------------------------------------------------------

function renderAnalysis() {

    setProblemSteps("classification");
    updateStepper("classification");
    setStep("problem");

    const data =
        wizard.analysis;

    const container =
        wizardContainer();

    const problems =
        data.problem_recommendations;

    const profile =
        data.profile || {};

    const shape =
        profile.shape || {};

    const best =
        problems.classification.score >= problems.clustering.score
        ? "classification"
        : "clustering";

    container.innerHTML = `

        <h2>
            تحلیل اولیه دیتاست
        </h2>

        <p>
            دیتاست شما ${formatNumber(shape.rows)} ردیف و ${formatNumber(shape.columns)} ستون دارد.
            بر اساس این داده‌ها، میزان مناسب بودن هر روش تحلیل را می‌بینید. انتخاب نهایی با شماست.
        </p>

        <div class="cards">

            ${createProblemCard(problems.classification, best === "classification")}

            ${createProblemCard(problems.clustering, best === "clustering")}

        </div>

    `;

    container.querySelectorAll("[data-problem]").forEach(button => {

        button.addEventListener("click", () => selectProblem(button.dataset.problem));

    });

}


function createProblemCard(problem, isBest) {

    const explanation =
        getProblemExplanation(
            problem.problem_type
        );

    const reasons =
        problem.reasons
        .map(
            r => `<li>${escapeHtml(translateReason(r))}</li>`
        )
        .join("");

    const examples =
        explanation.examples
        .map(
            e => `<li>${e}</li>`
        )
        .join("");

    return `

    <div class="card ${isBest ? "card--highlight" : ""}">

        ${isBest ? `<span class="badge badge--primary">پیشنهاد سیستم</span>` : ""}

        <h3>
            ${explanation.title}
        </h3>

        <p>
            ${explanation.description}
        </p>

        <h4>
            چرا پیشنهاد شده؟
        </h4>

        <ul>
            ${reasons}
        </ul>

        <h4>
            مثال کاربرد
        </h4>

        <ul>
            ${examples}
        </ul>

        <div class="meter" aria-label="میزان تناسب">
            <div class="meter__bar" style="width:${Math.min(problem.score, 100)}%"></div>
        </div>

        <p>
            میزان تناسب:
            <b>
            ${getScoreText(problem.score)}
            </b>
        </p>

        <button type="button" data-problem="${problem.problem_type}" ${problem.available ? "" : "disabled"}>

            ${problem.available ? "انتخاب این روش" : "برای این دیتاست در دسترس نیست"}

        </button>

    </div>

    `;

}


function selectProblem(type) {

    wizard.problemType = type;
    wizard.target = null;
    wizard.targetMode = null;
    wizard.aiTarget = null;

    window.selectedProblemType = type;

    setProblemSteps(type);
    updateStepper(type);

    if(type === "classification") {

        wizardGo(showTargetSelection);

    }

    if(type === "clustering") {

        wizardGo(showClusteringPreferences);

    }

}


// ---------------------------------------------------------------------------
// Step 3: target (label) selection
// ---------------------------------------------------------------------------

function showTargetSelection(){

    wizard.problemType = "classification";

    setProblemSteps("classification");
    updateStepper("classification");
    setStep("target");

    const container =
        wizardContainer();

    const recommended =
        wizard.analysis.recommended_targets || [];

    const possible =
        wizard.analysis.possible_targets || [];

    let html = `

        <h2>
            انتخاب نتیجه مورد نظر (Target)
        </h2>

    `;

    if(recommended.length > 0){

        html += `

        <p>
            سیستم این ستون‌ها را برای پیش‌بینی مناسب تشخیص داده است. گزینه برجسته پیشنهاد سیستم است، اما انتخاب با شماست.
        </p>

        <div class="cards">

            ${recommended.map((target, index) => createTargetCard(target, index === 0)).join("")}

            ${possible.map(target => createTargetCard(target, false)).join("")}

        </div>

        <details class="disclosure">

            <summary>ستون دیگری مد نظر دارید؟</summary>

            ${manualTargetPicker()}

        </details>

        `;

    }

    else {

        html += `

        <div class="notice">
            در این دیتاست ستون نتیجه مشخصی پیدا نشد (داده‌ها بیشتر برای گروه‌بندی مناسب‌اند).
            برای انجام Classification یکی از روش‌های زیر را انتخاب کنید.
        </div>

        <div class="cards cards--3">

            <div class="card option-card">
                <span class="option-card__icon">☰</span>
                <h3>انتخاب دستی نتیجه</h3>
                <p>از بین ستون‌هایی که سیستم برای Target مناسب می‌داند، خودتان یکی را انتخاب کنید.</p>
                ${manualTargetPicker()}
            </div>

            <div class="card option-card">
                <span class="option-card__icon">◎</span>
                <h3>ادامه با گروه‌بندی</h3>
                <p>سیستم داده‌های مشابه را در گروه‌های مختلف قرار می‌دهد (Clustering).</p>
                <button type="button" id="continueClusteringBtn">ادامه با گروه‌بندی</button>
            </div>

            <div class="card option-card">
                <span class="option-card__icon">✦</span>
                <h3>ساخت نتیجه با هوش مصنوعی</h3>
                <p>هوش مصنوعی چند ستون را ترکیب می‌کند و مناسب‌ترین Target را برای Classification می‌سازد.</p>
                <button type="button" id="aiTargetBtn">ساخت Target هوشمند</button>
            </div>

        </div>

        `;

    }

    container.innerHTML = html;

    container.querySelectorAll("[data-target]").forEach(button => {

        button.addEventListener("click", () => selectTarget(button.dataset.target, "detected"));

    });

    const manualBtn =
        container.querySelector("#manualTargetBtn");

    if(manualBtn){
        manualBtn.addEventListener("click", submitManualTarget);
    }

    const clusteringBtn =
        container.querySelector("#continueClusteringBtn");

    if(clusteringBtn){
        clusteringBtn.addEventListener("click", continueWithClustering);
    }

    const aiBtn =
        container.querySelector("#aiTargetBtn");

    if(aiBtn){
        aiBtn.addEventListener("click", generateAITarget);
    }

}


function manualTargetPicker(){

    const targets =
        wizard.analysis.manual_targets || [];

    if(targets.length === 0){

        return `
            <p class="hint">
                در این دیتاست ستونی که برای Target دستی مناسب باشد پیدا نشد (ستون‌ها یا شناسه هستند یا مقادیر عددی بسیار متنوع دارند). یکی از گزینه‌های دیگر را انتخاب کنید.
            </p>
        `;

    }

    return `

        <label class="field__label" for="manualTarget">ستون نتیجه</label>

        <select id="manualTarget">

            ${
                targets
                .map(
                    target =>
                    `<option value="${escapeHtml(target.column)}">${escapeHtml(target.column)}</option>`
                )
                .join("")
            }

        </select>

        <button type="button" id="manualTargetBtn">ادامه با این ستون</button>

    `;

}


function translateReason(reason) {

    const dictionary = {

        "Classification is possible":
        "اطلاعات لازم برای پیش‌بینی یک نتیجه مشخص وجود دارد",

        "Strong target candidate detected":
        "یک ستون نتیجه مناسب در داده‌ها پیدا شد",

        "Enough features available for clustering":
        "اطلاعات کافی برای پیدا کردن گروه‌های مشابه وجود دارد",

        "Multiple numerical features available":
        "چندین ویژگی عددی برای مقایسه داده‌ها وجود دارد",

        "Dataset size is suitable for clustering":
        "تعداد داده‌ها برای پیدا کردن الگو مناسب است",

        "Target column exists, classification may be more suitable":
        "یک نتیجه مشخص در داده‌ها وجود دارد و شاید پیش‌بینی آن مناسب‌تر باشد",

        "No target column detected":
        "ستون نتیجه مشخصی در داده‌ها نیست؛ گروه‌بندی انتخاب طبیعی‌تری است",

        "Target keyword detected":
        "نام ستون نشان می‌دهد که یک نتیجه یا وضعیت است",

        "Reasonable number of classes":
        "تعداد مقادیر مختلف آن برای پیش‌بینی مناسب است",

        "Categorical target candidate":
        "مقادیر آن دسته‌ای (گروهی) هستند"

    };

    return dictionary[reason] || reason;

}


function createTargetCard(target, isBest){

    return `

    <div class="card ${isBest ? "card--highlight" : ""}">

        ${isBest ? `<span class="badge badge--primary">پیشنهاد سیستم</span>` : ""}

        <h3 dir="auto">
            ${escapeHtml(target.column)}
        </h3>

        <p>
            ${isBest ? "مناسب‌ترین ستون برای پیش‌بینی" : "گزینه جایگزین"}
        </p>

        <ul>

            ${
                target.reason
                .map(
                    r => `<li>${escapeHtml(translateReason(r))}</li>`
                )
                .join("")
            }

        </ul>

        <button type="button" data-target="${escapeHtml(target.column)}" class="${isBest ? "" : "btn--secondary"}">

            انتخاب این نتیجه

        </button>

    </div>

    `;

}


async function selectTarget(target, mode){

    const result = await withLoading(
        "در حال بررسی ستون نتیجه...",
        () => api(
            `/api/projects/${wizard.project.id}/validate-target`,
            { json: { target } }
        )
    );

    if(!result){
        return;
    }

    wizard.target = target;
    wizard.targetMode = mode;

    window.selectedTarget = target;

    wizardGo(showPreferences);

}


function submitManualTarget(){

    const select =
        document.getElementById("manualTarget");

    if(!select || !select.value){

        showToast("یک ستون انتخاب کنید", "error");

        return;

    }

    selectTarget(select.value, "manual");

}


function continueWithClustering(){

    wizard.problemType = "clustering";
    wizard.targetMode = "clustering";
    wizard.target = null;

    setProblemSteps("clustering");
    updateStepper("clustering");

    wizardGo(showClusteringPreferences);

}


async function generateAITarget(){

    const data = await withLoading(
        "هوش مصنوعی در حال ساخت Target است... (ممکن است کمی طول بکشد)",
        () => api(`/api/projects/${wizard.project.id}/ai-target`, { method: "POST" })
    );

    if(!data){
        return;
    }

    wizard.aiTarget = data;

    wizardGo(showAITargetResult);

}


function showAITargetResult(){

    setStep("target");

    const data =
        wizard.aiTarget;

    const total =
        data.classes.reduce((sum, item) => sum + item.count, 0) || 1;

    const isStatistical =
        data.method === "statistical";

    wizardContainer().innerHTML = `

    <h2>
        ${isStatistical ? "Target پیشنهادی (روش آماری)" : "پیشنهاد هوشمند AI"}
    </h2>

    ${
        data.notice
        ?
        `<div class="notice">${escapeHtml(data.notice)}</div>`
        :
        ""
    }

    <div class="card card--highlight">

        <h3>
            Target ساخته‌شده: <span dir="ltr">${escapeHtml(data.target_column)}</span>
        </h3>

        <h4>
            دلیل پیشنهاد
        </h4>

        <p>
            ${escapeHtml(data.reason)}
        </p>

        <h4>
            ستون‌های ترکیب‌شده
        </h4>

        <div class="chips">
            ${(data.important_features || []).map(f => `<span class="chip">${escapeHtml(f)}</span>`).join("")}
        </div>

        <h4>
            دسته‌های ساخته‌شده
        </h4>

        <ul class="facts">
            ${data.classes.map(item => `
                <li><span>${escapeHtml(item.label)}</span><b>${formatNumber(item.count)} ردیف (${formatNumber(Math.round(item.count / total * 100))}٪)</b></li>
            `).join("")}
        </ul>

        <div class="button-row">
            <button type="button" id="acceptAiBtn">تایید و ادامه</button>
            <button type="button" class="btn--ghost" id="retryAiBtn">${isStatistical ? "تلاش دوباره با هوش مصنوعی" : "ساخت دوباره"}</button>
        </div>

    </div>

    `;

    document.getElementById("acceptAiBtn").addEventListener("click", acceptAITarget);

    document.getElementById("retryAiBtn").addEventListener("click", async () => {

        const fresh = await withLoading(
            "هوش مصنوعی در حال ساخت Target است...",
            () => api(`/api/projects/${wizard.project.id}/ai-target`, { method: "POST" })
        );

        if(fresh){
            wizard.aiTarget = fresh;
            showAITargetResult();
        }

    });

}


function acceptAITarget(){

    wizard.target = "generated_target";
    wizard.targetMode = "ai";
    wizard.problemType = "classification";

    window.selectedTarget = "generated_target";

    wizardGo(showPreferences);

}


// ---------------------------------------------------------------------------
// Helpers shared by preferences / model selection
// ---------------------------------------------------------------------------

function wizardSettings(){

    return {
        problem_type: wizard.problemType,
        target: wizard.problemType === "classification" ? wizard.target : null,
        target_mode: wizard.targetMode,
        preferences: wizard.preferences || {}
    };

}


/**
 * Card explaining what the system measured on the data by itself
 * (noise and number of features), instead of asking the user.
 */
function renderCharacteristicsCard(characteristics, problemType){

    if(!characteristics){

        return `
            <div class="card card--muted auto-detect" id="autoDetectCard">
                <h3>تشخیص خودکار از روی داده‌ها</h3>
                <p class="hint">در حال بررسی داده‌ها...</p>
            </div>
        `;

    }

    const noise =
        characteristics.noise;

    const dimension =
        characteristics.dimension;

    const noisePercent =
        Math.round((noise.outlier_ratio || 0) * 1000) / 10;

    const missingPercent =
        Math.round((noise.missing_ratio || 0) * 1000) / 10;

    const items = [

        `
        <li>
            <span class="auto-detect__label">داده‌های غیرعادی (نویز)</span>
            <span class="badge ${noise.has_noise ? "badge--warn" : "badge--ok"}">
                ${noise.has_noise ? "وجود دارد" : "ناچیز"}
            </span>
            <small>
                ${formatNumber(noisePercent)}٪ ردیف‌ها مقدار غیرعادی دارند و ${formatNumber(missingPercent)}٪ خانه‌ها خالی است.
                ${noise.has_noise ? "الگوریتم‌هایی که در برابر نویز مقاوم‌اند امتیاز بیشتری می‌گیرند." : ""}
            </small>
        </li>
        `

    ];

    if(problemType === "classification"){

        items.push(`
        <li>
            <span class="auto-detect__label">تعداد ویژگی‌ها نسبت به داده‌ها</span>
            <span class="badge ${dimension.high_dimension ? "badge--warn" : "badge--ok"}">
                ${dimension.high_dimension ? "زیاد" : "معمولی"}
            </span>
            <small>
                ${formatNumber(dimension.feature_count)} ستون ورودی (${formatNumber(dimension.encoded_feature_count)} ویژگی پس از آماده‌سازی) برای ${formatNumber(characteristics.rows)} ردیف.
                ${dimension.high_dimension ? "الگوریتم‌های مناسب داده‌های پربُعد امتیاز بیشتری می‌گیرند." : ""}
            </small>
        </li>
        `);

    }

    return `

        <div class="card card--muted auto-detect" id="autoDetectCard">

            <h3>تشخیص خودکار از روی داده‌ها</h3>

            <p class="hint">این موارد را لازم نیست شما جواب بدهید؛ سیستم آن‌ها را مستقیماً از دیتاست اندازه گرفت و در انتخاب الگوریتم استفاده می‌کند.</p>

            <ul class="auto-detect__list">
                ${items.join("")}
            </ul>

        </div>

    `;

}


async function loadCharacteristicsInto(problemType){

    try {

        const characteristics = await api(
            `/api/projects/${wizard.project.id}/characteristics`,
            { json: wizardSettings() }
        );

        const card =
            document.getElementById("autoDetectCard");

        if(card){
            card.outerHTML = renderCharacteristicsCard(characteristics, problemType);
        }

    }
    catch(err){

        const card =
            document.getElementById("autoDetectCard");

        if(card){
            card.remove();
        }

    }

}
