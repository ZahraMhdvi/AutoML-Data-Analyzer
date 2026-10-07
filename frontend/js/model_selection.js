

async function runModelSelection(){

    setStep("model");

    const container =
        wizardContainer();

    container.innerHTML = `<p class="hint">در حال یافتن بهترین مدل‌ها...</p>`;

    const data = await withLoading(
        "در حال یافتن بهترین مدل‌ها...",
        () => api(
            `/api/projects/${wizard.project.id}/model-selection`,
            { json: wizardSettings() }
        )
    );

    if(!data){

        container.innerHTML = `
            <div class="error">پیشنهاد مدل انجام نشد. با دکمه «مرحله قبل» تنظیمات را بررسی کنید و دوباره تلاش کنید.</div>
        `;

        return;

    }

    showModelResult(data);

}


function showModelResult(data){

    const container =
        wizardContainer();

    const recommendations =
        data.recommendations || [];

    if(recommendations.length === 0){

        container.innerHTML = `
            <div class="error">برای این تنظیمات الگوریتم مناسبی پیدا نشد. با «مرحله قبل» پاسخ‌ها را تغییر دهید.</div>
        `;

        return;

    }

    container.innerHTML = `

    <h2>
        پیشنهاد مدل مناسب
    </h2>

    <p>
        الگوریتم‌ها بر اساس پاسخ‌های شما و ویژگی‌های دیتاست امتیازدهی شده‌اند. گزینه برجسته پیشنهاد سیستم است؛ هر کدام را بخواهید انتخاب کنید.
    </p>

    <div class="cards">

        ${
            recommendations
            .map(
                (model, index) =>
                createModelCard(model, index === 0)
            )
            .join("")
        }

    </div>

    ${renderCharacteristicsCard(data.data_characteristics, wizard.problemType)}

    `;

    container.querySelectorAll("[data-algorithm]").forEach(button => {

        button.addEventListener("click", () => selectAlgorithm(button.dataset.algorithm));

    });

}


function createModelCard(model, isBest){

    const reasons =
        model.reasons
        .map(
            r => `<li>${escapeHtml(r)}</li>`
        )
        .join("");

    const limitations =
        model.limitations
        .map(
            l => `<li>${escapeHtml(l)}</li>`
        )
        .join("");

    const compatibilityText = {
        high: "تناسب زیاد",
        medium: "تناسب متوسط",
        low: "تناسب کم"
    }[model.compatibility] || "";

    return `

    <div class="card ${isBest ? "card--highlight" : ""}">

        ${isBest ? `<span class="badge badge--primary">پیشنهاد اول سیستم</span>` : ""}

        <h3 dir="ltr" class="algo-name">
            ${escapeHtml(model.algorithm)}
        </h3>

        <div class="meter" aria-label="امتیاز سازگاری">
            <div class="meter__bar" style="width:${Math.min(model.score, 100)}%"></div>
        </div>

        <p>
            امتیاز سازگاری: <b>${formatNumber(model.score)}</b>
            ${compatibilityText ? `<span class="badge badge--soft">${compatibilityText}</span>` : ""}
        </p>

        <h4>
            چرا پیشنهاد شده؟
        </h4>

        ${
            reasons
            ?
            `<ul>${reasons}</ul>`
            :
            `<p class="hint">بر اساس ویژگی‌های کلی دیتاست امتیاز گرفته است.</p>`
        }

        ${
            limitations
            ?
            `<h4>محدودیت‌ها</h4><ul>${limitations}</ul>`
            :
            `<p class="hint">محدودیت مشخصی برای این مدل ثبت نشده است</p>`
        }

        <button type="button" data-algorithm="${escapeHtml(model.algorithm)}" class="${isBest ? "" : "btn--secondary"}">

            انتخاب این مدل

        </button>

    </div>

    `;

}


async function selectAlgorithm(algorithm){

    window.selectedAlgorithm = algorithm;

    const versions =
        wizard.project.version_count || 1;

    const data = await withLoading(
        versions > 1
            ? `در حال آموزش مدل و تحلیل دوباره ${formatNumber(versions)} نسخه داده...`
            : "در حال آموزش مدل و ساخت داشبورد...",
        () => api(
            `/api/projects/${wizard.project.id}/run`,
            { json: { ...wizardSettings(), algorithm } }
        )
    );

    if(!data){
        return;
    }

    setStep("results");

    showToast("تحلیل کامل شد و در پروژه ذخیره شد", "success");

    projectCache.set(data.project.id, data.project);

    location.hash = `#/project/${data.project.id}`;

}
