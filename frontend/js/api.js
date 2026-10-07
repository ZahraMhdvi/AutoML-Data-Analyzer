

const API_BASE = (() => {

    const { protocol, port } = window.location;

    if (protocol === "file:" || port === "5500") {
        return "http://127.0.0.1:8000";
    }

    return "";

})();


const TOKEN_KEY = "automl_token";


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
            /* storage unavailable: keep the session in memory only */
        }
    },

    clear() {
        this.token = null;
        this.user = null;
        try {
            localStorage.removeItem(TOKEN_KEY);
        } catch (err) {
            /* ignore */
        }
    }

};


class ApiError extends Error {

    constructor(message, status) {
        super(message);
        this.status = status;
    }

}


function extractErrorMessage(body, status) {

    if (body) {

        if (typeof body.detail === "string") {
            return body.detail;
        }

        if (Array.isArray(body.detail) && body.detail.length) {
            return "اطلاعات ارسال‌شده کامل نیست";
        }

        if (body.error) {
            return body.error.message || body.error;
        }
    }

    if (status >= 500) {
        return "خطای داخلی سرور؛ دوباره تلاش کنید";
    }

    return "درخواست با خطا مواجه شد";

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
        throw new ApiError(
            "ارتباط با سرور برقرار نشد. مطمئن شوید برنامه سمت سرور در حال اجراست.",
            0
        );
    }

    let data = null;

    try {
        data = await response.json();
    }
    catch (err) {
        data = null;
    }

    if (response.status === 401 && session.token && !options.skipAuthRedirect) {
        session.clear();
        showToast(extractErrorMessage(data, 401), "error");
        location.hash = "#/login";
        throw new ApiError(extractErrorMessage(data, 401), 401);
    }

    if (!response.ok) {
        throw new ApiError(extractErrorMessage(data, response.status), response.status);
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
            showToast(err.message || "خطایی رخ داد", "error");
        }
        return null;
    }
    finally {
        hideLoading();
    }

}
