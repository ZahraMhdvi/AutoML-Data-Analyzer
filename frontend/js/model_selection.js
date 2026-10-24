let lastModelSelection = null;


async function runModelSelection(){

    setStep("model");

    const container = wizardContainer();

    if(lastModelSelection && lastModelSelection.key === JSON.stringify(wizardSettings())){
        showModelResult(lastModelSelection.data);
        return;
    }

    container.innerHTML = `<p class="hint">${t("loading.models")}</p>`;

    const data = await withLoading(
        t("loading.models"),
        () => api(`/api/projects/${wizard.project.id}/model-selection`, { json: wizardSettings() })
    );

    if(!data){
        container.innerHTML = `<div class="error">${t("models.failed")}</div>`;
        return;
    }

    lastModelSelection = { key: JSON.stringify(wizardSettings()), data };

    showModelResult(data);

}


function showModelResult(data){

    const container = wizardContainer();
    const recommendations = data.recommendations || [];
    const excluded = data.excluded || [];

    if(recommendations.length === 0){
        container.innerHTML = `<div class="error">${t("models.none")}</div>`;
        return;
    }

    container.innerHTML = `

    <h2>${t("models.title")}</h2>

    <p>${t("models.intro")}</p>

    <div class="notice notice--soft">${t("models.semantics")}</div>

    <div class="cards">
        ${recommendations.map((model, index) => createModelCard(model, index === 0)).join("")}
    </div>

    ${excluded.length ? `
    <div class="card card--muted">
        <h3>${t("models.excludedTitle")}</h3>
        <ul>${excluded.map(item => `<li><b dir="ltr">${escapeHtml(item.algorithm)}</b> — ${escapeHtml(t(`eligibility.${item.reason}`))}</li>`).join("")}</ul>
    </div>` : ""}

    <details class="disclosure">
        <summary>${t("models.formulaTitle")}</summary>
        <p>${t("models.formulaText")}</p>
        <p dir="ltr" class="mono small">CS(a) = clip(50 + 50 · raw(a) / R, 0, 100) ; raw(a) = Σ w⁺·[e∈S_a] − w⁻·[e∈W_a] ; R = Σ w⁺</p>
    </details>

    ${renderCharacteristicsCard(data.data_characteristics, wizard.problemType)}
    `;

    container.querySelectorAll("[data-algorithm]").forEach(button => {
        button.addEventListener("click", () => selectAlgorithm(button.dataset.algorithm));
    });

}


function evidenceLine(item){

    const sign = item.points > 0 ? "+" : "−";

    return `
        <li class="evidence evidence--${item.effect}">
            <span>${escapeHtml(capabilityLabel(item.code))}</span>
            <span class="evidence__meta">${t(`models.source.${item.source}`)} · <b dir="ltr">${sign}${formatNumber(Math.abs(item.points), 0)}</b></span>
        </li>
    `;

}


function createModelCard(model, isBest){

    const reasons = (model.reasons || []).map(evidenceLine).join("");
    const limitations = (model.limitations || []).map(evidenceLine).join("");

    return `

    <div class="card ${isBest ? "card--highlight" : ""}">

        <div class="card__top">
            ${isBest ? `<span class="badge badge--primary">${t("models.topPick")}</span>` : `<span class="badge badge--soft">#${localizeDigits(model.rank)}</span>`}
            <span class="badge badge--soft">${t(`models.band.${model.compatibility}`)}</span>
        </div>

        <h3 dir="ltr" class="algo-name">${escapeHtml(model.algorithm)}</h3>

        <div class="meter" role="meter" aria-valuemin="0" aria-valuemax="100" aria-valuenow="${model.score}" aria-label="${t("models.score")}">
            <div class="meter__bar" style="width:${Math.min(model.score, 100)}%"></div>
        </div>

        <p class="score-line">${t("models.score")}: <b>${formatNumber(model.score, 1)}</b> <span class="hint">/ ${formatNumber(100)}</span></p>

        <h4>${t("models.why")}</h4>
        ${reasons ? `<ul class="evidence-list">${reasons}</ul>` : `<p class="hint">${t("models.noStrengths")}</p>`}

        <h4>${t("models.limitations")}</h4>
        ${limitations ? `<ul class="evidence-list">${limitations}</ul>` : `<p class="hint">${t("models.noLimitations")}</p>`}

        <button type="button" data-algorithm="${escapeHtml(model.algorithm)}" class="${isBest ? "" : "btn--secondary"}">
            ${t("models.choose")}
        </button>

    </div>
    `;

}


async function selectAlgorithm(algorithm){

    const versions = wizard.project.version_count || 1;

    const data = await withLoading(
        versions > 1 ? t("loading.trainingVersions", { count: versions }) : t("loading.training"),
        () => api(`/api/projects/${wizard.project.id}/run`, { json: { ...wizardSettings(), algorithm } })
    );

    if(!data){
        return;
    }

    setStep("results");
    showToast(t("models.done"), "success");
    projectCache.set(data.project.id, data.project);
    lastModelSelection = null;
    location.hash = `#/project/${data.project.id}`;

}
