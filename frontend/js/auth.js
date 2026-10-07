

function showAuth(mode){

    showView("authView");

    setNav(null);

    const isLogin =
        mode !== "signup";

    document.getElementById("loginForm").hidden = !isLogin;
    document.getElementById("signupForm").hidden = isLogin;

    document.querySelectorAll("[data-auth-tab]").forEach(tab => {

        const active =
            tab.dataset.authTab === (isLogin ? "login" : "signup");

        tab.classList.toggle("tabs__tab--active", active);
        tab.setAttribute("aria-selected", active ? "true" : "false");

    });

    document.getElementById("loginError").textContent = "";
    document.getElementById("signupError").textContent = "";

    setTimeout(() => {
        document.getElementById(isLogin ? "loginEmail" : "signupName").focus();
    }, 30);

}


document.querySelectorAll("[data-auth-tab]").forEach(tab => {

    tab.addEventListener("click", () => {
        location.hash = "#/" + tab.dataset.authTab;
    });

});


function setUser(user){

    session.user = user;

    const nav =
        document.getElementById("appNav");

    if(!user){
        nav.hidden = true;
        return;
    }

    nav.hidden = false;

    document.getElementById("userName").textContent = user.name;
    document.getElementById("userAvatar").textContent = (user.name || "?").trim().charAt(0);

}


function setNav(active){

    document.querySelectorAll("[data-nav]").forEach(link => {
        link.classList.toggle("app-nav__link--active", link.dataset.nav === active);
    });

}


async function submitAuthForm(event, kind){

    event.preventDefault();

    const errorBox =
        document.getElementById(kind === "login" ? "loginError" : "signupError");

    errorBox.textContent = "";

    let payload;

    if(kind === "login"){

        payload = {
            email: document.getElementById("loginEmail").value.trim(),
            password: document.getElementById("loginPassword").value
        };

        if(!payload.email || !payload.password){
            errorBox.textContent = "ایمیل و رمز عبور را وارد کنید";
            return;
        }

    }
    else {

        payload = {
            name: document.getElementById("signupName").value.trim(),
            email: document.getElementById("signupEmail").value.trim(),
            password: document.getElementById("signupPassword").value
        };

        if(payload.name.length < 2){
            errorBox.textContent = "نام خود را وارد کنید";
            return;
        }

        if(!/^[^@\s]+@[^@\s]+\.[^@\s]+$/.test(payload.email)){
            errorBox.textContent = "ایمیل وارد شده معتبر نیست";
            return;
        }

        if(payload.password.length < 6){
            errorBox.textContent = "رمز عبور باید حداقل ۶ کاراکتر باشد";
            return;
        }

    }

    const button =
        event.target.querySelector('button[type="submit"]');

    button.disabled = true;

    try {

        const data = await api(
            `/api/auth/${kind}`,
            { json: payload, skipAuthRedirect: true }
        );

        session.save(data.token, data.user);
        setUser(data.user);

        event.target.reset();

        showToast(
            kind === "login" ? `خوش آمدید، ${data.user.name}` : "حساب شما ساخته شد",
            "success"
        );

        const next =
            sessionStorageGet("afterLogin") || "#/projects";

        sessionStorageSet("afterLogin", null);

        location.hash = next;

    }
    catch(err){

        errorBox.textContent = err.message;

    }
    finally {

        button.disabled = false;

    }

}


document.getElementById("loginForm")
    .addEventListener("submit", event => submitAuthForm(event, "login"));

document.getElementById("signupForm")
    .addEventListener("submit", event => submitAuthForm(event, "signup"));


document.getElementById("logoutBtn")
    .addEventListener("click", async () => {

        try {
            await api("/api/auth/logout", { method: "POST", skipAuthRedirect: true });
        }
        catch(err){

        }

        session.clear();
        projectCache.clear();
        setUser(null);

        location.hash = "#/login";

    });


function sessionStorageGet(key){

    try {
        return sessionStorage.getItem(key);
    }
    catch(err){
        return null;
    }

}


function sessionStorageSet(key, value){

    try {
        if(value === null){
            sessionStorage.removeItem(key);
        }
        else {
            sessionStorage.setItem(key, value);
        }
    }
    catch(err){

    }

}
