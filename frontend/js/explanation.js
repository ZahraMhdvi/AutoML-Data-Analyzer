
function getProblemExplanation(type){

    if(!type){
        return null;
    }

    const key = type.toLowerCase();

    return {
        title: t(`problem.${key}.title`),
        description: t(`problem.${key}.description`),
        examples: t(`problem.${key}.examples`)
    };

}


function statusLabel(status){
    return t(`problem.status.${status}`);
}


function statusBadgeClass(status){
    return {
        recommended: "badge--ok",
        potentially_suitable: "badge--warn",
        not_suitable: "badge--danger"
    }[status] || "badge--soft";
}


function getMetricExplanation(metric){
    return has(`metrics.help.${metric}`) ? t(`metrics.help.${metric}`) : t("metrics.help.none");
}


function getSilhouetteText(score){

    if(score >= 0.7) return t("clustering.quality.excellent");
    if(score >= 0.5) return t("clustering.quality.good");
    if(score >= 0.25) return t("clustering.quality.fair");
    if(score >= 0) return t("clustering.quality.weak");
    return t("clustering.quality.poor");

}


function classLabel(label){
    const key = `targetClass.${String(label).replace(/\s+/g, "")}`;
    return has(key) ? t(key) : String(label);
}


function capabilityLabel(code){
    return has(`capability.${code}`) ? t(`capability.${code}`) : code;
}


function targetTypeLabel(type, source){
    if(type === "pseudo" && (source === "llm" || source === "statistical")){
        return t(`targetType.pseudo_${source}`);
    }
    return t(`targetType.${type}`);
}
