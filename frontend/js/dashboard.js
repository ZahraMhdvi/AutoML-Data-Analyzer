
const PALETTE = ["#4f46e5", "#0ea5e9", "#14b8a6", "#f59e0b", "#ec4899", "#8b5cf6", "#22c55e", "#ef4444"];
const SCATTER_COLORS = ["#4f46e5", "#0ea5e9", "#14b8a6", "#f59e0b", "#ec4899", "#8b5cf6", "#22c55e", "#ef4444", "#a16207", "#0f766e"];
const NOISE_COLOR = "#94a3b8";

const activeCharts = [];


function rgba(hex, alpha){
    const r = parseInt(hex.substring(1, 3), 16);
    const g = parseInt(hex.substring(3, 5), 16);
    const b = parseInt(hex.substring(5, 7), 16);
    return `rgba(${r}, ${g}, ${b}, ${alpha})`;
}


function trackChart(chart){
    activeCharts.push(chart);
    return chart;
}


function destroyCharts(){
    while(activeCharts.length){
        try { activeCharts.pop().destroy(); } catch(err){ /* already destroyed */ }
    }
    if(window.Chart && Chart.instances){
        Object.values(Chart.instances).forEach(chart => {
            try { chart.destroy(); } catch(err){ /* ignore */ }
        });
    }
}


function chartFont(){
    return '"Vazirmatn", "Segoe UI", Tahoma, Arial, sans-serif';
}


if(window.Chart){
    Chart.defaults.font.family = chartFont();
    Chart.defaults.color = "#475569";
    Chart.defaults.borderColor = "#e2e8f0";
    if(navigator.webdriver){
        Chart.defaults.animation = false;   }
}


function legendOptions(position = "bottom"){
    return { position, rtl: isRTL(), textDirection: isRTL() ? "rtl" : "ltr", labels: { boxWidth: 12, padding: 14 } };
}


function tooltipOptions(){
    return { rtl: isRTL(), textDirection: isRTL() ? "rtl" : "ltr" };
}


function numberTicks(){
    return { callback: value => formatNumber(value) };
}


function renderDashboard(data, container){

    container = container || document.getElementById("result");

    destroyCharts();

    const problemType = data.problem_type || (data.report && data.report.problem_type);

    if(problemType === "clustering"){
        renderClusteringDashboard(data, container);
    }
    else {
        renderClassificationDashboard(data, container);
    }

    container.insertAdjacentHTML("beforeend", renderDataSummary(data));
    container.insertAdjacentHTML("beforeend", renderIssues(data.issues, t("issues.runTitle")));

}


function kpi(label, value, hint, help){
    return `
        <div class="kpi" ${help ? `title="${escapeHtml(help)}"` : ""}>
            <span class="kpi__label">${label}</span>
            <span class="kpi__value">${value}</span>
            ${hint ? `<span class="kpi__hint">${hint}</span>` : ""}
        </div>
    `;
}


function renderDataSummary(data){

    const summary = data.data_summary;

    if(!summary){
        return "";
    }

    const reasons = summary.dropped_column_reasons || [];
    const drops = summary.row_drops || [];

    return `
    <div class="card card--muted">
        <h3>${t("dashboard.data.title")}</h3>
        <ul class="facts">
            <li><span>${t("dashboard.data.rows")}</span><b>${formatNumber(summary.rows)}</b></li>
            <li><span>${t("dashboard.data.rowsUsed")}</span><b>${formatNumber(summary.rows_used)}</b></li>
            ${summary.train_rows !== undefined ? `<li><span>${t("dashboard.data.trainTest")}</span><b>${formatNumber(summary.train_rows)} / ${formatNumber(summary.test_rows)}</b></li>` : ""}
            <li><span>${t("dashboard.data.inputFeatures")}</span><b>${formatNumber((summary.input_features || []).length)}</b></li>
            <li><span>${t("dashboard.data.encodedFeatures")}</span><b>${formatNumber(summary.features)}</b></li>
        </ul>
        ${drops.length ? `<p class="hint">${t("dashboard.data.rowDrops")} ${drops.map(d => escapeHtml(t(`rowDrop.${d.reason}`, { count: d.count }))).join(t("common.listSeparator"))}</p>` : ""}
        ${reasons.length ? `
            <h4>${t("dashboard.data.droppedColumns")}</h4>
            <div class="chips chips--small">
                ${reasons.map(r => `<span class="chip"><b dir="auto">${escapeHtml(r.column)}</b>&nbsp;· ${escapeHtml(t(`dropReason.${r.reason}`))}</span>`).join("")}
            </div>` : ""}
    </div>
    `;

}



function renderProtocolCard(data){

    const protocol = data.protocol || {};
    const split = protocol.split || {};
    const cv = data.cross_validation;

    let cvText = "-";
    if(cv && cv.macro_f1){
        cvText = t("dashboard.protocol.cvValue", {
            folds: cv.folds,
            mean: formatNumber(cv.macro_f1.mean, 3),
            std: formatNumber(cv.macro_f1.std, 3)
        });
    }
    else if(cv && cv.skipped){
        cvText = t(`dashboard.protocol.cvSkipped.${cv.skipped}`);
    }

    return `
    <div class="card">
        <h3>${t("dashboard.protocol.title")}</h3>
        <ul class="facts facts--compact">
            <li><span>${t("dashboard.protocol.split")}</span><b>${t("dashboard.protocol.splitValue", { train: split.train_rows, test: split.test_rows })}</b></li>
            <li><span>${t("dashboard.protocol.stratified")}</span><b>${protocol.stratified ? t("common.yes") : t("common.no")}</b></li>
            <li><span>${t("dashboard.protocol.seed")}</span><b dir="ltr">${escapeHtml(protocol.random_seed)}</b></li>
            <li><span>${t("dashboard.protocol.cv")}</span><b>${cvText}</b></li>
            <li><span>${t("dashboard.protocol.preprocessing")}</span><b>${t("dashboard.protocol.preprocessingValue")}</b></li>
            <li><span>${t("dashboard.protocol.latency")}</span><b>${formatNumber(data.latency_ms, 0)} ms</b></li>
        </ul>
        <details class="disclosure">
            <summary>${t("dashboard.protocol.hyperparameters")}</summary>
            <pre class="code" dir="ltr">${escapeHtml(JSON.stringify(protocol.hyperparameters || {}, null, 2))}</pre>
        </details>
    </div>
    `;

}


function renderAblationCard(ablation){

    if(!ablation){
        return "";
    }

    const a = ablation.condition_a_with_generator_features || {};
    const b = ablation.condition_b_without_generator_features;
    const drift = ablation.label_drift_if_regenerated;

    return `
    <div class="card card--accent">
        <h3>${t("ablation.title")}</h3>
        <p>${t("ablation.intro")}</p>
        <table class="data-table">
            <thead><tr><th>${t("ablation.condition")}</th><th>${t("metrics.accuracy")}</th><th>${t("metrics.macro_f1")}</th><th>${t("metrics.balanced_accuracy")}</th></tr></thead>
            <tbody>
                <tr><th>${t("ablation.conditionA")}</th><td>${formatPercent(a.accuracy)}</td><td>${formatPercent(a.macro_f1)}</td><td>${formatPercent(a.balanced_accuracy)}</td></tr>
                <tr><th>${t("ablation.conditionB")}</th><td>${b ? formatPercent(b.accuracy) : "-"}</td><td>${b ? formatPercent(b.macro_f1) : "-"}</td><td>${b ? formatPercent(b.balanced_accuracy) : "-"}</td></tr>
            </tbody>
        </table>
        <ul class="facts facts--compact">
            <li><span>${t("ablation.delta")}</span><b>${ablation.delta_macro_f1 === null || ablation.delta_macro_f1 === undefined ? "-" : formatNumber(ablation.delta_macro_f1, 3)}</b></li>
            <li><span>${t("ablation.reconstructability")}</span><b>${formatPercent(ablation.reconstructability_R)}</b></li>
            <li><span>${t("ablation.entropy")}</span><b>${formatNumber(ablation.normalized_entropy_H, 3)}</b></li>
            <li><span>${t("ablation.generators")}</span><b dir="auto">${(ablation.generator_features || []).map(escapeHtml).join(t("common.listSeparator"))}</b></li>
            ${drift ? `<li><span>${t("ablation.drift")}</span><b>${t("ablation.driftValue", { changed: drift.changed, rows: drift.rows, ratio: formatPercent(drift.changed_ratio) })}</b></li>` : ""}
        </ul>
        <p class="hint">${t("ablation.note")}</p>
    </div>
    `;

}


function renderClassificationDashboard(data, container){

    const m = data.metrics;
    const typeKey = data.target_type || "observed";
    const fixed = m.fixed_holdout_v1;

    container.innerHTML = `

    <div class="dash-head">
        <h2>${t("dashboard.classification.title", { algorithm: data.algorithm })}</h2>
        <span class="badge ${typeKey === "pseudo" ? "badge--warn" : "badge--ok"}">${targetTypeLabel(typeKey, data.target_source)}</span>
    </div>

    ${typeKey === "pseudo" ? `<div class="notice notice--warn">${t("dashboard.classification.pseudoWarning")}</div>` : ""}

    <div class="kpi-grid">
        ${kpi(t("metrics.accuracy"), formatPercent(m.accuracy), null, getMetricExplanation("accuracy"))}
        ${kpi(t("metrics.balanced_accuracy"), formatPercent(m.balanced_accuracy), null, getMetricExplanation("balanced_accuracy"))}
        ${kpi(t("metrics.macro_f1"), formatPercent(m.macro_f1), null, getMetricExplanation("macro_f1"))}
        ${kpi(t("metrics.weighted_f1"), formatPercent(m.weighted_f1), null, getMetricExplanation("weighted_f1"))}
        ${kpi(t("metrics.precision"), formatPercent(m.macro_precision), t("metrics.macroAvg"), getMetricExplanation("precision"))}
        ${kpi(t("metrics.recall"), formatPercent(m.macro_recall), t("metrics.macroAvg"), getMetricExplanation("recall"))}
    </div>

    <p class="hint">${t("dashboard.classification.testNote", { rows: m.test_size })}</p>

    ${fixed ? `<div class="notice notice--soft">${t("dashboard.classification.fixedHoldout", { rows: fixed.rows, f1: formatPercent(fixed.macro_f1), acc: formatPercent(fixed.accuracy) })}</div>` : ""}

    ${renderAblationCard(data.ablation)}

    <div class="grid-2">
        <div class="card">
            <h3>${t("dashboard.classification.metricsChart")}</h3>
            <div class="chart-box chart-box--md"><canvas id="metricsChart"></canvas></div>
        </div>
        ${renderProtocolCard(data)}
    </div>

    <div class="grid-2">
        <div class="card">
            <h3>${t("dashboard.classification.confusion")}</h3>
            <p class="hint">${t("dashboard.classification.confusionHint")}</p>
            <div id="confusionChart"></div>
        </div>
        <div class="card">
            <h3>${t("dashboard.classification.perClass")}</h3>
            ${renderPerClass(m.per_class)}
        </div>
    </div>

    <div class="card" id="featureImportanceContainer">
        <h3>${t("dashboard.importance.title")}</h3>
        <p class="hint">${t("dashboard.importance.method")}</p>
        <div class="chart-box chart-box--lg"><canvas id="featureChart"></canvas></div>
        <p class="hint">${t("dashboard.importance.disclaimer")}</p>
    </div>
    `;

    renderMetricsChart(m);
    renderFeatureImportance(data.feature_importance && data.feature_importance.permutation);

    if(m.confusion_matrix && m.classes){
        renderConfusionMatrix(m.confusion_matrix, m.classes);
    }

}


function renderPerClass(rows){

    if(!rows || !rows.length){
        return "";
    }

    return `
        <table class="data-table">
            <thead><tr><th>${t("dashboard.classification.class")}</th><th>${t("metrics.precision")}</th><th>${t("metrics.recall")}</th><th>F1</th><th>${t("dashboard.classification.support")}</th></tr></thead>
            <tbody>
                ${rows.map(r => `<tr><th dir="auto">${escapeHtml(classLabel(r.class))}</th><td>${formatPercent(r.precision)}</td><td>${formatPercent(r.recall)}</td><td>${formatPercent(r.f1)}</td><td>${formatNumber(r.support)}</td></tr>`).join("")}
            </tbody>
        </table>
    `;

}


function renderConfusionMatrix(matrix, classes){

    const container = document.getElementById("confusionChart");
    const max = Math.max(...matrix.flat()) || 1;

    let html = `
    <div class="heatmap-wrapper">
    <table class="heatmap-table">
        <tr><th class="heatmap-corner">${t("dashboard.classification.actualPredicted")}</th>
        ${classes.map(c => `<th dir="auto">${escapeHtml(classLabel(c))}</th>`).join("")}</tr>
    `;

    matrix.forEach((row, i) => {
        html += `<tr><th dir="auto">${escapeHtml(classLabel(classes[i]))}</th>`;
        row.forEach((value, j) => {
            const alpha = Math.max(value / max, 0.08);
            const color = i === j ? rgba("#4f46e5", alpha) : rgba("#f59e0b", alpha * 0.9);
            const text = alpha > 0.55 ? "#ffffff" : "#0f172a";
            html += `<td style="background:${color};color:${text}">${formatNumber(value)}</td>`;
        });
        html += `</tr>`;
    });

    html += `</table></div>`;

    container.innerHTML = html;

}


function renderMetricsChart(m){

    const labels = [t("metrics.accuracy"), t("metrics.balanced_accuracy"), t("metrics.macro_f1"), t("metrics.weighted_f1")];
    const values = [m.accuracy, m.balanced_accuracy, m.macro_f1, m.weighted_f1].map(v => (v || 0) * 100);

    trackChart(new Chart(document.getElementById("metricsChart"), {
        type: "bar",
        data: { labels, datasets: [{ label: t("dashboard.classification.percent"), data: values, backgroundColor: PALETTE.slice(0, 4), borderRadius: 8, maxBarThickness: 56 }] },
        options: {
            responsive: true,
            maintainAspectRatio: false,
            plugins: { legend: { display: false }, tooltip: { ...tooltipOptions(), callbacks: { label: ctx => formatPercent(ctx.raw / 100) } } },
            scales: {
                y: { beginAtZero: true, max: 100, title: { display: true, text: t("dashboard.classification.percent") }, ticks: numberTicks() },
                x: { reverse: isRTL(), ticks: { maxRotation: 0, autoSkip: false } }
            }
        }
    }));

}


function renderFeatureImportance(perm){

    const container = document.getElementById("featureImportanceContainer");

    if(!perm || !perm.values || !perm.values.length){
        container.innerHTML = `<h3>${t("dashboard.importance.title")}</h3><p class="hint">${t("dashboard.importance.none")}</p>`;
        return;
    }

    const top = perm.values.slice(0, 12);

    trackChart(new Chart(document.getElementById("featureChart"), {
        type: "bar",
        data: {
            labels: top.map(x => x.feature),
            datasets: [{
                label: t("dashboard.importance.axis"),
                data: top.map(x => x.importance),
                backgroundColor: top.map(x => x.importance >= 0 ? rgba("#4f46e5", 0.85) : rgba("#94a3b8", 0.85)),
                borderRadius: 6
            }]
        },
        options: {
            indexAxis: "y",
            responsive: true,
            maintainAspectRatio: false,
            plugins: { legend: { display: false }, tooltip: { ...tooltipOptions(), callbacks: { label: ctx => `${formatNumber(ctx.raw, 4)} ± ${formatNumber(top[ctx.dataIndex].std, 4)}` } } },
            scales: {
                x: { reverse: isRTL(), title: { display: true, text: t("dashboard.importance.axis") }, ticks: numberTicks() },
                y: { position: isRTL() ? "right" : "left" }
            }
        }
    }));

}



function renderClusteringDashboard(data, container){

    const m = data.metrics;
    const stability = m.stability;
    const external = m.external;
    const selection = (data.protocol || {}).model_selection;

    container.innerHTML = `

    <div class="dash-head">
        <h2>${t("dashboard.clustering.title", { algorithm: data.algorithm })}</h2>
        <span class="badge badge--soft">${t("dashboard.clustering.unsupervised")}</span>
    </div>

    <div class="kpi-grid">
        ${kpi(t("metrics.cluster_count"), formatNumber(m.cluster_count))}
        ${kpi(t("metrics.silhouette"), m.silhouette_score === null ? "-" : formatNumber(m.silhouette_score, 3), m.silhouette_score === null ? "" : getSilhouetteText(m.silhouette_score), getMetricExplanation("silhouette"))}
        ${kpi(t("metrics.davies_bouldin"), m.davies_bouldin_index === null ? "-" : formatNumber(m.davies_bouldin_index, 3), t("metrics.lowerBetter"), getMetricExplanation("davies_bouldin"))}
        ${kpi(t("metrics.calinski_harabasz"), m.calinski_harabasz_index === null ? "-" : formatNumber(m.calinski_harabasz_index, 1), t("metrics.higherBetter"), getMetricExplanation("calinski_harabasz"))}
        ${kpi(t("metrics.noise_ratio"), formatPercent(m.noise_ratio), t("dashboard.clustering.noisePoints", { count: m.noise_points }), getMetricExplanation("noise_ratio"))}
        ${kpi(t("metrics.stability"), stability ? formatNumber(stability.mean_ari, 3) : "-", stability ? t("dashboard.clustering.stabilityHint", { runs: stability.runs, std: formatNumber(stability.std_ari, 3) }) : "", getMetricExplanation("stability"))}
    </div>

    <div class="notice notice--soft">${t("dashboard.clustering.interpretation")}</div>

    ${(m.warnings || []).length ? `<div class="notice notice--warn">${m.warnings.map(w => escapeHtml(t(`clusterWarning.${w}`))).join(" · ")}</div>` : ""}

    ${external ? `<div class="notice">${t("dashboard.clustering.external", { ari: formatNumber(external.adjusted_rand_index, 3), nmi: formatNumber(external.normalized_mutual_info, 3) })}</div>` : ""}

    <div class="grid-2">
        <div class="card">
            <h3>${t("dashboard.clustering.sizes")}</h3>
            <div class="chart-box chart-box--md"><canvas id="clusterSizeChart"></canvas></div>
        </div>
        <div class="card">
            <h3>${t("dashboard.clustering.selection")}</h3>
            ${renderSelectionInfo(selection, data.protocol)}
        </div>
    </div>

    <div class="card">
        <h3>${t("dashboard.clustering.scatter")}</h3>
        <p class="hint">${t("dashboard.clustering.scatterHint")}</p>
        <div class="chart-box chart-box--xl"><canvas id="clusterScatterChart"></canvas></div>
    </div>

    <div class="card">
        <h3>${t("dashboard.clustering.profiles")}</h3>
        <p class="hint">${t("dashboard.clustering.profilesHint")}</p>
        ${renderProfiles(m.cluster_profiles)}
    </div>
    `;

    renderClusterSizeChart(m.cluster_sizes);
    renderClusterScatter(m.cluster_points);

}


function renderSelectionInfo(selection, protocol){

    const params = (protocol && protocol.hyperparameters) || {};
    const rows = [`<li><span>${t("dashboard.clustering.params")}</span><b dir="ltr" class="mono small">${escapeHtml(JSON.stringify(params))}</b></li>`];

    if(selection && selection.criterion){
        rows.push(`<li><span>${t("dashboard.clustering.criterion")}</span><b>${t(`selectionCriterion.${selection.criterion.startsWith("silhouette_non") ? "dbscan" : "silhouette"}`)}</b></li>`);
    }
    if(selection && selection.candidates && selection.candidates.length){
        rows.push(`<li><span>${t("dashboard.clustering.candidates")}</span><b dir="ltr" class="small">${selection.candidates.map(c => `k=${c.k}: ${c.silhouette.toFixed(3)}`).join(" · ")}</b></li>`);
    }
    if(!selection){
        rows.push(`<li><span>${t("dashboard.clustering.criterion")}</span><b>${t("dashboard.clustering.userK")}</b></li>`);
    }
    rows.push(`<li><span>${t("dashboard.clustering.groundTruth")}</span><b>${t("common.no")}</b></li>`);

    return `<ul class="facts facts--compact">${rows.join("")}</ul>`;

}


function renderProfiles(profiles){

    if(!profiles || !profiles.length){
        return `<p class="hint">${t("dashboard.clustering.noProfiles")}</p>`;
    }

    return `
    <div class="profile-grid">
        ${profiles.map(p => `
            <div class="cluster-card">
                <div class="cluster-card__head">
                    <span class="cluster-dot" style="background:${p.is_noise ? NOISE_COLOR : SCATTER_COLORS[(p.cluster) % SCATTER_COLORS.length]}"></span>
                    <b>${p.is_noise ? t("dashboard.clustering.noise") : t("dashboard.clustering.cluster", { id: p.cluster })}</b>
                    <span class="hint">${t("dashboard.clustering.members", { count: p.size })}</span>
                </div>
                <ul>
                    ${p.important_features.map(f => `
                        <li><span dir="auto">${escapeHtml(f.feature)}</span>
                        <b class="${f.direction === "above_average" ? "up" : "down"}">${f.direction === "above_average" ? "▲" : "▼"} ${formatNumber(Math.abs(f.z_difference), 2)}σ</b>
                        <small>${t("dashboard.clustering.meanVs", { mean: formatNumber(f.cluster_mean, 2), overall: formatNumber(f.overall_mean, 2) })}</small></li>`).join("")}
                </ul>
            </div>`).join("")}
    </div>
    `;

}


function renderClusterSizeChart(sizes){

    const ctx = document.getElementById("clusterSizeChart");

    if(!ctx || !sizes){
        return;
    }

    const labels = Object.keys(sizes);

    trackChart(new Chart(ctx, {
        type: "bar",
        data: {
            labels: labels.map(id => t("dashboard.clustering.cluster", { id })),
            datasets: [{ label: t("dashboard.clustering.membersAxis"), data: Object.values(sizes), backgroundColor: labels.map((_, i) => SCATTER_COLORS[Number(labels[i]) % SCATTER_COLORS.length]), borderRadius: 8, maxBarThickness: 56 }]
        },
        options: {
            responsive: true,
            maintainAspectRatio: false,
            plugins: { legend: { display: false }, tooltip: tooltipOptions() },
            scales: {
                y: { beginAtZero: true, title: { display: true, text: t("dashboard.clustering.membersAxis") }, ticks: numberTicks() },
                x: { reverse: isRTL() }
            }
        }
    }));

}


function renderClusterScatter(points){

    const ctx = document.getElementById("clusterScatterChart");

    if(!ctx || !points){
        return;
    }

    const groups = {};
    points.forEach(p => {
        (groups[p.cluster] = groups[p.cluster] || []).push({ x: p.x, y: p.y });
    });

    const datasets = Object.keys(groups).sort((a, b) => Number(a) - Number(b)).map(cluster => ({
        label: cluster === "-1" ? t("dashboard.clustering.noise") : t("dashboard.clustering.cluster", { id: cluster }),
        data: groups[cluster],
        backgroundColor: cluster === "-1" ? rgba(NOISE_COLOR, 0.5) : rgba(SCATTER_COLORS[Number(cluster) % SCATTER_COLORS.length], 0.55),
        pointRadius: 3.5,
        pointHoverRadius: 6
    }));

    trackChart(new Chart(ctx, {
        type: "scatter",
        data: { datasets },
        options: {
            maintainAspectRatio: false,
            plugins: { legend: legendOptions(), tooltip: tooltipOptions() },
            scales: {
                x: { reverse: isRTL(), title: { display: true, text: t("dashboard.clustering.pc1") }, ticks: numberTicks() },
                y: { position: isRTL() ? "right" : "left", title: { display: true, text: t("dashboard.clustering.pc2") }, ticks: numberTicks() }
            }
        }
    }));

}
