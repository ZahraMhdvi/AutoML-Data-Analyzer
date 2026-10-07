

function showPreferences(){

    wizard.problemType = "classification";

    setProblemSteps("classification");
    updateStepper("classification");
    setStep("preferences");

    const previous =
        wizard.preferences || {};

    const checked = (name, value) =>
        previous[name] === value ? "checked" : "";

    const targetLabel =
        wizard.targetMode === "ai"
        ? "Target ساخته‌شده با هوش مصنوعی"
        : wizard.target;

    wizardContainer().innerHTML = `

    <h2>
        تنظیمات تحلیل
    </h2>

    <p>
        ستون نتیجه: <b dir="auto">${escapeHtml(targetLabel)}</b> — به دو سؤال زیر پاسخ دهید تا مناسب‌ترین الگوریتم‌ها پیشنهاد شوند.
    </p>

    <div class="card">

        <h3>
            مهم‌ترین چیزی که از مدل انتظار دارید چیست؟
        </h3>

        <label>
            <input type="radio" name="goal" value="accuracy" ${checked("main_goal", "accuracy")}>
            بیشترین دقت ممکن را می‌خواهم
        </label>

        <label>
            <input type="radio" name="goal" value="speed" ${checked("main_goal", "speed")}>
            سرعت بالاتر برای من مهم‌تر است
        </label>

        <label>
            <input type="radio" name="goal" value="interpretability" ${checked("main_goal", "interpretability")}>
            می‌خواهم دلیل تصمیم مدل را بتوانم بفهمم
        </label>

    </div>

    <div class="card">

        <h3>
            آیا در آینده داده‌های جدید به سیستم اضافه می‌شود؟
        </h3>

        <label>
            <input type="radio" name="growth" value="continuous_data" ${checked("data_growth", "continuous_data")}>
            بله، مرتب داده جدید اضافه می‌شود
        </label>

        <label>
            <input type="radio" name="growth" value="static_data" ${checked("data_growth", "static_data")}>
            خیر، داده تقریباً ثابت است
        </label>

    </div>

    ${renderCharacteristicsCard(null, "classification")}

    <button type="button" id="submitPreferencesBtn" class="btn--block">

        مشاهده الگوریتم‌های پیشنهادی

    </button>

    `;

    document.getElementById("submitPreferencesBtn")
        .addEventListener("click", submitPreferences);

    loadCharacteristicsInto("classification");

}


function submitPreferences(){

    const mainGoal =
        document.querySelector('input[name="goal"]:checked')?.value;

    const dataGrowth =
        document.querySelector('input[name="growth"]:checked')?.value;

    if(!mainGoal || !dataGrowth){

        showToast("لطفاً به هر دو سؤال پاسخ دهید", "error");

        return;

    }


    wizard.preferences = {
        main_goal: mainGoal,
        data_growth: dataGrowth
    };

    window.selectedPreferences = wizard.preferences;

    wizardGo(runModelSelection);

}
