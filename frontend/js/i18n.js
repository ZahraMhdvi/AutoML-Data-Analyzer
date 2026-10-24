

const LOCALES = {
    "en-US": { dir: "ltr", short: "EN", label: "English" },
    "fa-IR": { dir: "rtl", short: "فا", label: "فارسی" }
};

const DEFAULT_LOCALE = "en-US";
const LOCALE_KEY = "guidml_locale";

const i18n = {
    locale: DEFAULT_LOCALE,
    dicts: {}
};


function storedLocale(){
    try {
        const value = localStorage.getItem(LOCALE_KEY);
        return LOCALES[value] ? value : null;
    }
    catch(err){
        return null;
    }
}


async function loadDictionaries(){
    const load = async (locale) => {
        try {
            const response = await fetch(`i18n/${locale}.json`, { cache: "no-cache" });
            i18n.dicts[locale] = await response.json();
        }
        catch(err){
            i18n.dicts[locale] = {};
        }
    };
    await Promise.all(Object.keys(LOCALES).map(load));
}


function lookup(dict, key){
    return key.split(".").reduce((node, part) => (node && node[part] !== undefined ? node[part] : undefined), dict);
}


function t(key, params){
    let value = lookup(i18n.dicts[i18n.locale] || {}, key);
    if(value === undefined){
        value = lookup(i18n.dicts[DEFAULT_LOCALE] || {}, key);
    }
    if(value === undefined){
        return key;
    }
    if(typeof value !== "string"){
        return value;
    }
    return interpolate(value, params);
}


function has(key){
    return lookup(i18n.dicts[i18n.locale] || {}, key) !== undefined
        || lookup(i18n.dicts[DEFAULT_LOCALE] || {}, key) !== undefined;
}


function interpolate(text, params){
    if(!params){
        return text;
    }
    return text.replace(/\{(\w+)\}/g, (match, name) => {
        if(params[name] === undefined || params[name] === null){
            return match;
        }
        const value = params[name];
        if(Array.isArray(value)){
            return value.map(item => localizeDigits(item)).join(t("common.listSeparator"));
        }
        if(typeof value === "number"){
            return formatNumber(value);
        }
        return localizeDigits(value);
    });
}


/* Translate an API error/issue/evidence object {code, params}. */
function tCode(group, item, fallback){
    if(!item){
        return fallback || "";
    }
    const code = typeof item === "string" ? item : item.code;
    const params = (typeof item === "object" && item.params) || {};
    const key = `${group}.${code}`;
    if(has(key)){
        return t(key, params);
    }
    return fallback || (typeof item === "object" && item.message) || code;
}


function isRTL(){
    return LOCALES[i18n.locale].dir === "rtl";
}


function numberLocale(){
    return i18n.locale === "fa-IR" ? "fa-IR" : "en-US";
}


function localizeDigits(value){
    const text = String(value ?? "");
    return i18n.locale === "fa-IR" ? text.replace(/[0-9]/g, d => "۰۱۲۳۴۵۶۷۸۹"[d]) : text;
}


function formatNumber(value, digits){
    if(value === null || value === undefined || Number.isNaN(Number(value))){
        return "-";
    }
    const options = digits === undefined
        ? { maximumFractionDigits: 3 }
        : { minimumFractionDigits: digits, maximumFractionDigits: digits };
    return Number(value).toLocaleString(numberLocale(), options);
}


function formatPercent(value, digits = 1){
    if(value === null || value === undefined || Number.isNaN(Number(value))){
        return "-";
    }
    return Number(value).toLocaleString(numberLocale(), {
        style: "percent", minimumFractionDigits: digits, maximumFractionDigits: digits
    });
}


function formatDate(iso, withTime = true){
    if(!iso){
        return "-";
    }
    const date = new Date(iso);
    if(Number.isNaN(date.getTime())){
        return iso;
    }
    const options = withTime
        ? { year: "numeric", month: "short", day: "numeric", hour: "2-digit", minute: "2-digit" }
        : { year: "numeric", month: "short", day: "numeric" };
    const locale = i18n.locale === "fa-IR" ? "fa-IR-u-ca-persian" : "en-US-u-ca-gregory";
    try {
        return date.toLocaleString(locale, options);
    }
    catch(err){
        return date.toISOString().slice(0, 16).replace("T", " ");
    }
}


function applyStaticTranslations(root = document){
    root.querySelectorAll("[data-i18n]").forEach(el => {
        el.textContent = t(el.dataset.i18n);
    });
    root.querySelectorAll("[data-i18n-html]").forEach(el => {
        el.innerHTML = t(el.dataset.i18nHtml);
    });
    root.querySelectorAll("[data-i18n-placeholder]").forEach(el => {
        el.placeholder = t(el.dataset.i18nPlaceholder);
    });
    root.querySelectorAll("[data-i18n-aria]").forEach(el => {
        el.setAttribute("aria-label", t(el.dataset.i18nAria));
    });
    root.querySelectorAll("[data-i18n-title]").forEach(el => {
        el.title = t(el.dataset.i18nTitle);
    });
    document.title = t("app.title");
}


function applyDocumentLocale(){
    const html = document.documentElement;
    html.lang = i18n.locale === "fa-IR" ? "fa" : "en";
    html.dir = LOCALES[i18n.locale].dir;
    document.querySelectorAll("[data-locale-option]").forEach(button => {
        const active = button.dataset.localeOption === i18n.locale;
        button.classList.toggle("lang-switch__btn--active", active);
        button.setAttribute("aria-pressed", active ? "true" : "false");
    });
    if(window.Chart){
        Chart.defaults.locale = numberLocale();
    }
    applyStaticTranslations();
}


async function setLocale(locale, { persist = true, rerender = true } = {}){
    if(!LOCALES[locale]){
        return;
    }
    i18n.locale = locale;
    try { localStorage.setItem(LOCALE_KEY, locale); } catch(err){ /* ignore */ }
    applyDocumentLocale();

    if(persist && typeof session !== "undefined" && session.token){
        try {
            await api("/api/auth/me/preferences", { method: "PATCH", json: { locale }, skipAuthRedirect: true });
            if(session.user){ session.user.locale = locale; }
        }
        catch(err){ /* preference stays local */ }
    }

    if(rerender && typeof rerenderCurrentView === "function"){
        rerenderCurrentView();
    }
}


async function initI18n(){
    await loadDictionaries();
    i18n.locale = storedLocale() || DEFAULT_LOCALE;
    applyDocumentLocale();
    document.querySelectorAll("[data-locale-option]").forEach(button => {
        button.addEventListener("click", () => setLocale(button.dataset.localeOption));
    });
}
