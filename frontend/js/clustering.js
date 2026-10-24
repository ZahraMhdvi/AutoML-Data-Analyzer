function showClusteringPreferences(){

    wizard.problemType = "clustering";

    setProblemSteps("clustering");
    updateStepper("clustering");
    setStep("preferences");

    const previous = wizard.preferences || {};

    const goal = previous.cluster_shape === "irregular"
        ? "pattern_discovery"
        : (previous.hierarchical_analysis ? "customer_segmentation" : null);

    const known = previous.cluster_count_known === true
        ? "known"
        : (previous.cluster_count_known === false ? "unknown" : null);

    const rows = (wizard.analysis.profile && wizard.analysis.profile.shape && wizard.analysis.profile.shape.rows) || 0;

    wizardContainer().innerHTML = `

    <h2>${t("clusterPrefs.title")}</h2>

    ${wizard.targetMode === "clustering" ? `<div class="notice notice--soft">${t("clusterPrefs.fallbackNotice")}</div>` : ""}

    <div class="card">
        <h3>${t("clusterPrefs.goalQuestion")}</h3>
        <label class="radio"><input type="radio" name="cluster_goal" value="customer_segmentation" ${goal === "customer_segmentation" ? "checked" : ""}> ${t("clusterPrefs.goalSegmentation")}</label>
        <label class="radio"><input type="radio" name="cluster_goal" value="pattern_discovery" ${goal === "pattern_discovery" ? "checked" : ""}> ${t("clusterPrefs.goalPatterns")}</label>
    </div>

    <div class="card">
        <h3>${t("clusterPrefs.countQuestion")}</h3>
        <label class="radio"><input type="radio" name="cluster_number" value="unknown" ${known === "unknown" ? "checked" : ""}> ${t("clusterPrefs.countUnknown")}</label>
        <label class="radio"><input type="radio" name="cluster_number" value="known" ${known === "known" ? "checked" : ""}> ${t("clusterPrefs.countKnown")}</label>
        <div id="clusterCountInput" ${known === "known" ? "" : "hidden"}>
            <label class="field__label" for="clusterCount">${t("clusterPrefs.countLabel")}</label>
            <input class="input input--short" type="number" id="clusterCount" min="2" max="${Math.max(2, rows - 1)}" step="1"
                   placeholder="${t("clusterPrefs.countPlaceholder")}" value="${previous.cluster_count || ""}">
        </div>
    </div>

    ${renderCharacteristicsCard(null, "clustering")}

    <button type="button" id="submitClusteringBtn" class="btn--block">${t("prefs.submit")}</button>
    `;

    document.querySelectorAll('input[name="cluster_number"]').forEach(radio => {
        radio.addEventListener("change", () => {
            const box = document.getElementById("clusterCountInput");
            box.hidden = !(radio.value === "known" && radio.checked);
            if(!box.hidden){
                document.getElementById("clusterCount").focus();
            }
        });
    });

    document.getElementById("submitClusteringBtn").addEventListener("click", submitClusteringPreferences);

    loadCharacteristicsInto("clustering");

}


function submitClusteringPreferences(){

    const clusterNumber = document.querySelector('input[name="cluster_number"]:checked')?.value;
    const clusterGoal = document.querySelector('input[name="cluster_goal"]:checked')?.value;

    if(!clusterGoal || !clusterNumber){
        showToast(t("prefs.answerBoth"), "error");
        return;
    }

    let clusterCount = null;

    if(clusterNumber === "known"){

        clusterCount = Number(document.getElementById("clusterCount").value);

        const rows = (wizard.analysis.profile && wizard.analysis.profile.shape && wizard.analysis.profile.shape.rows) || 0;

        if(!Number.isInteger(clusterCount) || clusterCount < 2 || (rows && clusterCount >= rows)){
            showToast(t("clusterPrefs.countInvalid"), "error");
            document.getElementById("clusterCount").focus();
            return;
        }

    }

    wizard.preferences = {
        cluster_count_known: clusterNumber === "known",
        cluster_count: clusterCount,
        cluster_shape: clusterGoal === "pattern_discovery" ? "irregular" : "unknown",
        hierarchical_analysis: clusterGoal === "customer_segmentation"
    };

    wizard.problemType = "clustering";
    wizard.target = null;

    wizardGo(runModelSelection);

}
