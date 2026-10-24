function targetDisplayName(){

    if(wizard.targetMode === "ai"){
        return wizard.aiTarget && wizard.aiTarget.source === "statistical"
            ? t("pseudo.labelStatistical")
            : t("pseudo.labelLLM");
    }

    return wizard.target;

}


function showPreferences(){

    wizard.problemType = "classification";

    setProblemSteps("classification");
    updateStepper("classification");
    setStep("preferences");

    const previous = wizard.preferences || {};
    const checked = (name, value) => previous[name] === value ? "checked" : "";
    const typeKey = wizard.targetMode === "ai" ? "pseudo" : (wizard.targetMode === "manual" ? "user_selected" : "observed");

    wizardContainer().innerHTML = `

    <h2>${t("prefs.title")}</h2>

    <p>
        ${t("prefs.targetLine")} <b dir="auto">${escapeHtml(targetDisplayName())}</b>
        <span class="badge badge--soft">${targetTypeLabel(typeKey, wizard.aiTarget && wizard.aiTarget.source)}</span>
        — ${t("prefs.intro")}
    </p>

    <div class="card">
        <h3>${t("prefs.goalQuestion")}</h3>
        <label class="radio"><input type="radio" name="goal" value="accuracy" ${checked("main_goal", "accuracy")}> ${t("prefs.goalAccuracy")}</label>
        <label class="radio"><input type="radio" name="goal" value="speed" ${checked("main_goal", "speed")}> ${t("prefs.goalSpeed")}</label>
        <label class="radio"><input type="radio" name="goal" value="interpretability" ${checked("main_goal", "interpretability")}> ${t("prefs.goalInterpretability")}</label>
    </div>

    <div class="card">
        <h3>${t("prefs.growthQuestion")}</h3>
        <label class="radio"><input type="radio" name="growth" value="continuous_data" ${checked("data_growth", "continuous_data")}> ${t("prefs.growthYes")}</label>
        <label class="radio"><input type="radio" name="growth" value="static_data" ${checked("data_growth", "static_data")}> ${t("prefs.growthNo")}</label>
    </div>

    ${renderCharacteristicsCard(null, "classification")}

    <button type="button" id="submitPreferencesBtn" class="btn--block">${t("prefs.submit")}</button>
    `;

    document.getElementById("submitPreferencesBtn").addEventListener("click", submitPreferences);

    loadCharacteristicsInto("classification");

}


function submitPreferences(){

    const mainGoal = document.querySelector('input[name="goal"]:checked')?.value;
    const dataGrowth = document.querySelector('input[name="growth"]:checked')?.value;

    if(!mainGoal || !dataGrowth){
        showToast(t("prefs.answerBoth"), "error");
        return;
    }

    wizard.preferences = { main_goal: mainGoal, data_growth: dataGrowth };

    wizardGo(runModelSelection);

}
