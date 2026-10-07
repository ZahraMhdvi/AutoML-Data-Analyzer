

function showClusteringPreferences(){

    wizard.problemType = "clustering";

    setProblemSteps("clustering");
    updateStepper("clustering");
    setStep("preferences");

    const previous =
        wizard.preferences || {};

    const goal =
        previous.cluster_shape === "irregular"
        ? "pattern_discovery"
        : (previous.hierarchical_analysis ? "customer_segmentation" : null);

    const known =
        previous.cluster_count_known === true
        ? "known"
        : (previous.cluster_count_known === false ? "unknown" : null);

    const rows =
        (wizard.analysis.profile && wizard.analysis.profile.shape && wizard.analysis.profile.shape.rows) || 0;

    wizardContainer().innerHTML = `

    <h2>
        تنظیمات پیدا کردن گروه‌های مشابه
    </h2>

    ${
        wizard.targetMode === "clustering"
        ?
        `<div class="notice notice--soft">به‌جای پیش‌بینی، سیستم داده‌های شبیه به هم را گروه‌بندی می‌کند.</div>`
        :
        ""
    }

    <div class="card">

        <h3>
            هدف شما از گروه‌بندی چیست؟
        </h3>

        <label>
            <input type="radio" name="cluster_goal" value="customer_segmentation" ${goal === "customer_segmentation" ? "checked" : ""}>
            شناخت گروه‌های مختلف کاربران و ارتباط بین گروه‌ها
        </label>

        <label>
            <input type="radio" name="cluster_goal" value="pattern_discovery" ${goal === "pattern_discovery" ? "checked" : ""}>
            پیدا کردن الگوهای پنهان (گروه‌ها ممکن است شکل نامنظم داشته باشند)
        </label>

    </div>

    <div class="card">

        <h3>
            آیا تعداد گروه‌ها را می‌دانید؟
        </h3>

        <label>
            <input type="radio" name="cluster_number" value="unknown" ${known === "unknown" ? "checked" : ""}>
            خیر، سیستم خودش تعداد مناسب را پیدا کند
        </label>

        <label>
            <input type="radio" name="cluster_number" value="known" ${known === "known" ? "checked" : ""}>
            بله، خودم مشخص می‌کنم
        </label>

        <div id="clusterCountInput" ${known === "known" ? "" : "hidden"}>

            <label class="field__label" for="clusterCount">
                تعداد گروه‌ها
            </label>

            <input
                type="number"
                id="clusterCount"
                min="2"
                max="${Math.max(2, rows - 1)}"
                step="1"
                placeholder="مثلاً ۳"
                value="${previous.cluster_count || ""}">

        </div>

    </div>

    ${renderCharacteristicsCard(null, "clustering")}

    <button type="button" id="submitClusteringBtn" class="btn--block">

        مشاهده الگوریتم‌های پیشنهادی

    </button>

    `;

    document
        .querySelectorAll('input[name="cluster_number"]')
        .forEach(radio => {

            radio.addEventListener("change", () => {

                const box =
                    document.getElementById("clusterCountInput");

                box.hidden = !(radio.value === "known" && radio.checked);

                if(!box.hidden){
                    document.getElementById("clusterCount").focus();
                }

            });

        });

    document.getElementById("submitClusteringBtn")
        .addEventListener("click", submitClusteringPreferences);

    loadCharacteristicsInto("clustering");

}


function submitClusteringPreferences(){

    const clusterNumber =
        document.querySelector('input[name="cluster_number"]:checked')?.value;

    const clusterGoal =
        document.querySelector('input[name="cluster_goal"]:checked')?.value;

    if(!clusterGoal || !clusterNumber){

        showToast("لطفاً به هر دو سؤال پاسخ دهید", "error");

        return;

    }

    let clusterCount = null;

    if(clusterNumber === "known"){

        clusterCount =
            Number(document.getElementById("clusterCount").value);

        const rows =
            (wizard.analysis.profile && wizard.analysis.profile.shape && wizard.analysis.profile.shape.rows) || 0;

        if(!Number.isInteger(clusterCount) || clusterCount < 2 || (rows && clusterCount >= rows)){

            showToast("تعداد گروه‌ها باید یک عدد صحیح، حداقل ۲ باشد", "error");

            document.getElementById("clusterCount").focus();

            return;

        }

    }

    wizard.preferences = {

        cluster_count_known:
            clusterNumber === "known",

        cluster_count:
            clusterCount,

        cluster_shape:
            clusterGoal === "pattern_discovery"
            ?
            "irregular"
            :
            "unknown",

        hierarchical_analysis:
            clusterGoal === "customer_segmentation"

    };

    window.selectedPreferences = wizard.preferences;

    wizard.problemType = "clustering";
    wizard.target = null;

    wizardGo(runModelSelection);

}
