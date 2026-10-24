const wizard = {
    project: null,
    analysis: null,
    problemType: null,
    target: null,
    targetMode: null,
    preferences: null,
    aiTarget: null,
    fallbackPolicy: "notify",
    history: []
};

window.analysisData = null;


function wizardContainer(){
    return document.getElementById("result");
}


function refreshWizardHeader(project){

    document.getElementById("wizardTitle").textContent = t("wizard.projectTitle", { name: project.name });

    const backLink = document.getElementById("wizardProjectLink");
    const notice = document.getElementById("wizardNotice");

    if(project.status === "ready"){
        backLink.href = `#/project/${project.id}`;
        backLink.textContent = t("wizard.backToDashboard");
        notice.hidden = false;
        notice.innerHTML = t("wizard.reconfigureNotice", { count: project.version_count });
    }
    else {
        backLink.href = "#/projects";
        backLink.textContent = t("wizard.backSaved");
        notice.hidden = true;
    }

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

    refreshWizardHeader(project);

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
    wizard.history[wizard.history.length - 1]();
    refreshWizardBack();
}


function refreshWizardBack(){
    document.getElementById("wizardBackBtn").hidden = wizard.history.length < 2;
}


document.getElementById("wizardBackBtn").addEventListener("click", wizardBack);



function renderIssues(issues, title){

    const visible = (issues || []).filter(issue => issue.severity !== "info" || issue.code === "DUPLICATE_ROWS");

    if(!visible.length){
        return "";
    }

    return `
        <div class="card card--muted issues">
            <h3>${escapeHtml(title || t("issues.title"))}</h3>
            <ul class="issue-list">
                ${visible.map(issue => `
                    <li class="issue issue--${issue.severity}">
                        <span class="badge ${issue.severity === "error" ? "badge--danger" : issue.severity === "warning" ? "badge--warn" : "badge--soft"}">${t(`issues.severity.${issue.severity}`)}</span>
                        <span>${escapeHtml(tCode("issues.codes", issue))}</span>
                    </li>`).join("")}
            </ul>
        </div>
    `;

}



function renderAnalysis(){

    setProblemSteps("classification");
    updateStepper("classification");
    setStep("problem");

    const data = wizard.analysis;
    const problems = data.problem_recommendations;
    const shape = (data.profile || {}).shape || {};

    wizardContainer().innerHTML = `
        <h2>${t("wizard.problem.title")}</h2>
        <p>${t("wizard.problem.intro", { rows: shape.rows, columns: shape.columns })}</p>
        <div class="cards cards--2">
            ${createProblemCard(problems.classification)}
            ${createProblemCard(problems.clustering)}
        </div>
        <p class="hint">${t("wizard.problem.rulesNote")}</p>
        ${renderIssues(data.issues, t("issues.datasetTitle"))}
    `;

    wizardContainer().querySelectorAll("[data-problem]").forEach(button => {
        button.addEventListener("click", () => selectProblem(button.dataset.problem));
    });

}


function createProblemCard(problem){

    const explanation = getProblemExplanation(problem.problem_type);
    const best = problem.priority === 1 && problem.status !== "not_suitable";

    const evidence = (problem.evidence || [])
        .map(item => `<li>${escapeHtml(tCode("evidence", item))}</li>`)
        .join("");

    return `
    <div class="card ${best ? "card--highlight" : ""}">
        <div class="card__top">
            <span class="badge ${statusBadgeClass(problem.status)}">${statusLabel(problem.status)}</span>
            ${best ? `<span class="badge badge--primary">${t("wizard.problem.systemSuggestion")}</span>` : ""}
        </div>
        <h3>${explanation.title}</h3>
        <p>${explanation.description}</p>
        <h4>${t("wizard.problem.evidence")}</h4>
        <ul>${evidence}</ul>
        <h4>${t("wizard.problem.examples")}</h4>
        <ul>${explanation.examples.map(e => `<li>${e}</li>`).join("")}</ul>
        <button type="button" data-problem="${problem.problem_type}" ${problem.available ? "" : "disabled"}>
            ${problem.available ? t("wizard.problem.choose") : t("wizard.problem.unavailable")}
        </button>
    </div>
    `;

}


function selectProblem(type){

    wizard.problemType = type;
    wizard.target = null;
    wizard.targetMode = null;
    wizard.aiTarget = null;

    setProblemSteps(type);
    updateStepper(type);

    wizardGo(type === "classification" ? showTargetSelection : showClusteringPreferences);

}



function showTargetSelection(){

    wizard.problemType = "classification";

    setProblemSteps("classification");
    updateStepper("classification");
    setStep("target");

    const recommended = wizard.analysis.recommended_targets || [];
    const possible = wizard.analysis.possible_targets || [];

    let html = `<h2>${t("wizard.target.title")}</h2>`;

    if(recommended.length > 0){
        html += `
        <p>${t("wizard.target.detectedIntro")}</p>
        <div class="cards">
            ${recommended.map((target, index) => createTargetCard(target, index === 0)).join("")}
            ${possible.map(target => createTargetCard(target, false)).join("")}
        </div>
        <details class="disclosure">
            <summary>${t("wizard.target.otherColumn")}</summary>
            ${manualTargetPicker()}
        </details>
        <details class="disclosure">
            <summary>${t("wizard.target.pseudoInstead")}</summary>
            ${pseudoTargetOption()}
        </details>
        `;
    }
    else {
        html += `
        <div class="notice">${t("wizard.target.noneFound")}</div>
        <div class="cards cards--3">
            <div class="card option-card">
                <span class="option-card__icon">☰</span>
                <h3>${t("wizard.target.manualTitle")}</h3>
                <p>${t("wizard.target.manualText")}</p>
                ${manualTargetPicker()}
            </div>
            <div class="card option-card">
                <span class="option-card__icon">◎</span>
                <h3>${t("wizard.target.clusteringTitle")}</h3>
                <p>${t("wizard.target.clusteringText")}</p>
                <button type="button" id="continueClusteringBtn">${t("wizard.target.clusteringButton")}</button>
            </div>
            <div class="card option-card">
                <span class="option-card__icon">✦</span>
                <h3>${t("wizard.target.aiTitle")}</h3>
                ${pseudoTargetOption()}
            </div>
        </div>
        `;
    }

    const container = wizardContainer();
    container.innerHTML = html;

    container.querySelectorAll("[data-target]").forEach(button => {
        button.addEventListener("click", () => selectTarget(button.dataset.target, "detected"));
    });

    const manualBtn = container.querySelector("#manualTargetBtn");
    if(manualBtn){ manualBtn.addEventListener("click", submitManualTarget); }

    const clusteringBtn = container.querySelector("#continueClusteringBtn");
    if(clusteringBtn){ clusteringBtn.addEventListener("click", continueWithClustering); }

    const aiBtn = container.querySelector("#aiTargetBtn");
    if(aiBtn){ aiBtn.addEventListener("click", generateAITarget); }

    const policy = container.querySelector("#fallbackPolicy");
    if(policy){
        policy.checked = wizard.fallbackPolicy === "abort";
        policy.addEventListener("change", () => { wizard.fallbackPolicy = policy.checked ? "abort" : "notify"; });
    }

}


function pseudoTargetOption(){
    return `
        <p>${t("wizard.target.aiText")}</p>
        <div class="notice notice--soft privacy-note">
            <b>${t("wizard.target.privacyTitle")}</b> ${t("wizard.target.privacyText")}
        </div>
        <label class="checkbox">
            <input type="checkbox" id="fallbackPolicy"> ${t("wizard.target.abortOnFailure")}
        </label>
        <button type="button" id="aiTargetBtn">${t("wizard.target.aiButton")}</button>
    `;
}


function manualTargetPicker(){

    const targets = wizard.analysis.manual_targets || [];

    if(targets.length === 0){
        return `<p class="hint">${t("wizard.target.noManual")}</p>`;
    }

    return `
        <label class="field__label" for="manualTarget">${t("wizard.target.manualLabel")}</label>
        <select id="manualTarget" dir="auto">
            ${targets.map(target => `<option value="${escapeHtml(target.column)}">${escapeHtml(target.column)}</option>`).join("")}
        </select>
        <button type="button" id="manualTargetBtn">${t("wizard.target.manualButton")}</button>
    `;

}


function createTargetCard(target, isBest){

    return `
    <div class="card ${isBest ? "card--highlight" : ""}">
        ${isBest ? `<span class="badge badge--primary">${t("wizard.problem.systemSuggestion")}</span>` : ""}
        <h3 dir="auto">${escapeHtml(target.column)}</h3>
        <p><span class="badge badge--soft">${t("targetType.observed")}</span> ${isBest ? t("wizard.target.best") : t("wizard.target.alternative")}</p>
        <ul>${target.reason.map(r => `<li>${escapeHtml(tCode("evidence", r))}</li>`).join("")}</ul>
        <button type="button" data-target="${escapeHtml(target.column)}" class="${isBest ? "" : "btn--secondary"}">
            ${t("wizard.target.choose")}
        </button>
    </div>
    `;

}


async function selectTarget(target, mode){

    const result = await withLoading(
        t("loading.validatingTarget"),
        () => api(`/api/projects/${wizard.project.id}/validate-target`, { json: { target } })
    );

    if(!result){
        return;
    }

    wizard.target = target;
    wizard.targetMode = mode;

    wizardGo(showPreferences);

}


function submitManualTarget(){

    const select = document.getElementById("manualTarget");

    if(!select || !select.value){
        showToast(t("wizard.target.pickColumn"), "error");
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


async function requestAITarget(){
    return withLoading(
        t("loading.aiTarget"),
        () => api(`/api/projects/${wizard.project.id}/ai-target`, { json: { fallback_policy: wizard.fallbackPolicy } })
    );
}


async function generateAITarget(){

    const data = await requestAITarget();

    if(!data){
        return;
    }

    wizard.aiTarget = data;

    wizardGo(showAITargetResult);

}


function aiReason(definition){

    const reason = (definition && definition.reason) || {};

    if(reason.code){
        return t(`pseudo.reason.${reason.code}`, reason.params || {});
    }

    if(i18n.locale === "fa-IR" && reason.fa){
        return reason.fa;
    }

    return reason.en || reason.fa || "";

}


function renderLLMRecord(llm){

    if(!llm){
        return "";
    }

    const statusClass = llm.status === "SUCCESS" ? "badge--ok" : llm.status === "FALLBACK" ? "badge--warn" : "badge--danger";

    return `
        <details class="disclosure">
            <summary>${t("pseudo.llmRecord")}</summary>
            <ul class="facts facts--compact">
                <li><span>${t("pseudo.fields.status")}</span><b><span class="badge ${statusClass}">${t(`llmStatus.${llm.status}`)}</span></b></li>
                <li><span>${t("pseudo.fields.requestedMethod")}</span><b>${t(`method.${llm.requested_method}`)}</b></li>
                <li><span>${t("pseudo.fields.actualMethod")}</span><b>${llm.actual_method ? t(`method.${llm.actual_method}`) : "-"}</b></li>
                <li><span>${t("pseudo.fields.requestedModel")}</span><b dir="ltr">${escapeHtml(llm.requested_model || "-")}</b></li>
                <li><span>${t("pseudo.fields.successfulModel")}</span><b dir="ltr">${escapeHtml(llm.successful_model || "-")}</b></li>
                <li><span>${t("pseudo.fields.fallback")}</span><b>${llm.fallback_used ? t("common.yes") : t("common.no")}${llm.fallback_reason ? " · " + escapeHtml(t(`llmError.${llm.fallback_reason}`)) : ""}</b></li>
                <li><span>${t("pseudo.fields.latency")}</span><b>${formatNumber(llm.latency_ms, 0)} ms</b></li>
                <li><span>${t("pseudo.fields.requestId")}</span><b dir="ltr" class="mono">${escapeHtml(llm.request_id || "")}</b></li>
            </ul>
        </details>
    `;

}


function renderRuleDefinition(definition){

    if(!definition){
        return "";
    }

    const directions = definition.directions || {};
    const cutoffs = definition.cutoffs || [];

    return `
        <h4>${t("pseudo.generatorFeatures")}</h4>
        <div class="chips">
            ${(definition.usable_features || definition.features || []).map(f => `
                <span class="chip" dir="auto">${escapeHtml(f)} <b>${directions[f] < 0 ? "↓" : "↑"}</b></span>`).join("")}
        </div>
        <details class="disclosure">
            <summary>${t("pseudo.ruleDetails")}</summary>
            <ul class="facts facts--compact">
                <li><span>${t("pseudo.fields.rule")}</span><b dir="ltr" class="mono">${escapeHtml((definition.rule || {}).name || "")} v${escapeHtml((definition.rule || {}).version || "")}</b></li>
                <li><span>${t("pseudo.fields.formula")}</span><b dir="ltr" class="mono small">${escapeHtml((definition.rule || {}).formula || "")}</b></li>
                <li><span>${t("pseudo.fields.cutoffs")}</span><b dir="ltr">${cutoffs.map(c => Number(c).toFixed(3)).join(" · ")}</b></li>
                <li><span>${t("pseudo.fields.fitScope")}</span><b>${t("pseudo.fitScope")}</b></li>
                <li><span>${t("pseudo.fields.labelPolicy")}</span><b>${t("pseudo.labelPolicy")}</b></li>
                <li><span>${t("pseudo.fields.missingPolicy")}</span><b>${t("pseudo.missingPolicy")}</b></li>
                <li><span>${t("pseudo.fields.weights")}</span><b>${t("pseudo.equalWeights")}</b></li>
            </ul>
        </details>
    `;

}


function showAITargetResult(){

    setStep("target");

    const data = wizard.aiTarget;
    const definition = data.definition || {};
    const total = data.classes.reduce((sum, item) => sum + item.count, 0) || 1;
    const isStatistical = data.source === "statistical";

    wizardContainer().innerHTML = `
    <h2>${isStatistical ? t("pseudo.titleStatistical") : t("pseudo.titleLLM")}</h2>

    ${data.notice ? `<div class="notice notice--warn">${escapeHtml(tCode("notices", { code: data.notice.code, params: { reason: t(`llmError.${data.notice.params.reason}`) } }))}</div>` : ""}

    <div class="notice notice--soft">${t("pseudo.circularityWarning")}</div>

    <div class="card card--highlight">
        <div class="card__top">
            <span class="badge badge--primary">${targetTypeLabel("pseudo", data.source)}</span>
            <span class="badge ${isStatistical ? "badge--warn" : "badge--ok"}">${t(`pseudo.source.${data.source}`)}</span>
        </div>
        <h3>${t("pseudo.generated")} <span dir="ltr" class="mono">${escapeHtml(data.target_column)}</span></h3>

        <h4>${t("pseudo.reasonTitle")}</h4>
        <p dir="auto">${escapeHtml(aiReason(definition))}</p>

        ${renderRuleDefinition(definition)}

        <h4>${t("pseudo.classes")}</h4>
        <ul class="facts">
            ${data.classes.map(item => `
                <li><span>${escapeHtml(classLabel(item.label))}</span><b>${t("pseudo.classCount", { count: item.count, percent: formatPercent(item.count / total, 0) })}</b></li>
            `).join("")}
        </ul>

        ${renderLLMRecord(data.llm)}

        <div class="button-row">
            <button type="button" id="acceptAiBtn">${t("pseudo.accept")}</button>
            <button type="button" class="btn--ghost" id="retryAiBtn">${isStatistical ? t("pseudo.retryLLM") : t("pseudo.regenerate")}</button>
        </div>
    </div>
    `;

    document.getElementById("acceptAiBtn").addEventListener("click", acceptAITarget);

    document.getElementById("retryAiBtn").addEventListener("click", async () => {
        const fresh = await requestAITarget();
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

    wizardGo(showPreferences);

}


function wizardSettings(){
    return {
        problem_type: wizard.problemType,
        target: wizard.problemType === "classification" ? wizard.target : null,
        target_mode: wizard.targetMode,
        preferences: wizard.preferences || {}
    };
}


function renderCharacteristicsCard(characteristics, problemType){

    if(!characteristics){
        return `
            <div class="card card--muted auto-detect" id="autoDetectCard">
                <h3>${t("autoDetect.title")}</h3>
                <p class="hint">${t("autoDetect.loading")}</p>
            </div>
        `;
    }

    const noise = characteristics.noise;
    const dimension = characteristics.dimension;

    const items = [`
        <li>
            <span class="auto-detect__label">${t("autoDetect.noise")}</span>
            <span class="badge ${noise.has_noise ? "badge--warn" : "badge--ok"}">${noise.has_noise ? t("autoDetect.present") : t("autoDetect.negligible")}</span>
            <small>
                ${t("autoDetect.noiseText", { outliers: formatPercent(noise.outlier_ratio || 0), missing: formatPercent(noise.missing_ratio || 0) })}
                ${noise.has_noise ? t("autoDetect.noiseEffect") : ""}
            </small>
        </li>
    `];

    if(problemType === "classification"){
        items.push(`
        <li>
            <span class="auto-detect__label">${t("autoDetect.dimension")}</span>
            <span class="badge ${dimension.high_dimension ? "badge--warn" : "badge--ok"}">${dimension.high_dimension ? t("autoDetect.high") : t("autoDetect.normal")}</span>
            <small>
                ${t("autoDetect.dimensionText", { features: dimension.feature_count, encoded: dimension.encoded_feature_count, rows: characteristics.rows })}
                ${dimension.high_dimension ? t("autoDetect.dimensionEffect") : ""}
            </small>
        </li>
        `);
    }

    return `
        <div class="card card--muted auto-detect" id="autoDetectCard">
            <h3>${t("autoDetect.title")}</h3>
            <p class="hint">${t("autoDetect.intro")}</p>
            <ul class="auto-detect__list">${items.join("")}</ul>
        </div>
    `;

}


async function loadCharacteristicsInto(problemType){

    try {
        const characteristics = await api(
            `/api/projects/${wizard.project.id}/characteristics`,
            { json: wizardSettings() }
        );
        const card = document.getElementById("autoDetectCard");
        if(card){
            card.outerHTML = renderCharacteristicsCard(characteristics, problemType);
        }
    }
    catch(err){
        const card = document.getElementById("autoDetectCard");
        if(card){
            card.remove();
        }
    }

}
