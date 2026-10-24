

const API_BASE = (() => {

    const { protocol, port } = window.location;

    if (protocol === "file:" || port === "5500") {
        return "http://127.0.0.1:8000";
    }

    return "";

})();


const TOKEN_KEY = "automl_token";

async function download(path, filename) {

    const response = await fetch(API_BASE + path, { headers: session.token ? { Authorization: "Bearer " + session.token } : {} });

    if (!response.ok) {
        let data = null;
        try { data = await response.json(); } catch (err) { data = null; }
        throw new ApiError(extractErrorMessage(data, response.status), response.status);
    }

    const blob = await response.blob();
    const url = URL.createObjectURL(blob);
    const link = document.createElement("a");
    link.href = url;
    link.download = filename;
    document.body.appendChild(link);
    link.click();
    link.remove();
    setTimeout(() => URL.revokeObjectURL(url), 1000);

}


const session = {

    token: null,

    user: null,

    load() {
        try {
            this.token = localStorage.getItem(TOKEN_KEY);
        } catch (err) {
            this.token = null;
        }
        return this.token;
    },

    save(token, user) {
        this.token = token;
        this.user = user;
        try {
            localStorage.setItem(TOKEN_KEY, token);
        } catch (err) {

        }
    },

    clear() {
        this.token = null;
        this.user = null;
        try {
            localStorage.removeItem(TOKEN_KEY);
        } catch (err) {

        }
    }

};


class ApiError extends Error {

    constructor(message, status, code, params) {
        super(message);
        this.status = status;
        this.code = code || null;
        this.params = params || {};
    }

}



function parseError(body, status) {

    const detail = body && body.detail;

    if (detail && typeof detail === "object" && !Array.isArray(detail) && detail.code) {
        return { code: detail.code, params: detail.params || {}, message: tCode("errors", detail, detail.message) };
    }

    if (typeof detail === "string") {
        return { code: null, params: {}, message: detail };
    }

    if (status >= 500) {
        return { code: "INTERNAL_ERROR", params: {}, message: t("errors.INTERNAL_ERROR") };
    }

    return { code: "HTTP_ERROR", params: {}, message: t("errors.HTTP_ERROR") };

}


function extractErrorMessage(body, status) {
    return parseError(body, status).message;
}



async function api(path, options = {}) {

    const headers = {};

    let body;

    if (options.json !== undefined) {
        headers["Content-Type"] = "application/json";
        body = JSON.stringify(options.json);
    }
    else if (options.form) {
        body = options.form;
    }

    if (session.token) {
        headers["Authorization"] = "Bearer " + session.token;
    }

    const method =
        options.method || (body !== undefined ? "POST" : "GET");

    let response;

    try {
        response = await fetch(API_BASE + path, { method, headers, body });
    }
    catch (err) {
        throw new ApiError(t("errors.NETWORK_ERROR"), 0, "NETWORK_ERROR");
    }

    let data = null;

    try {
        data = await response.json();
    }
    catch (err) {
        data = null;
    }

    if (response.status === 401 && session.token && !options.skipAuthRedirect) {
        const error = parseError(data, 401);
        session.clear();
        showToast(error.message, "error");
        location.hash = "#/login";
        throw new ApiError(error.message, 401, error.code, error.params);
    }

    if (!response.ok) {
        const error = parseError(data, response.status);
        throw new ApiError(error.message, response.status, error.code, error.params);
    }

    return data;

}



async function withLoading(text, task) {

    showLoading(text);

    try {
        return await task();
    }
    catch (err) {
        if (err.status !== 401) {
            showToast(err.message || t("errors.INTERNAL_ERROR"), "error");
        }
        return null;
    }
    finally {
        hideLoading();
    }

}
