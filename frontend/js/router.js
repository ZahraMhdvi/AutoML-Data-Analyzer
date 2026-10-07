

const PUBLIC_ROUTES = ["login", "signup"];


async function ensureUser(){

    if(session.user){
        return session.user;
    }

    if(!session.token){
        return null;
    }

    try {

        const data =
            await api("/api/auth/me", { skipAuthRedirect: true });

        setUser(data.user);

        return data.user;

    }
    catch(err){

        if(err.status === 401){
            session.clear();
            return null;
        }

        throw err;

    }

}


async function route(){

    const hash =
        location.hash.replace(/^#\/?/, "");

    const parts =
        hash.split("/").filter(Boolean);

    const page =
        parts[0] || "projects";

    hideLoading();

    document.querySelectorAll(".modal:not([hidden])").forEach(modal => closeModal(modal.id));

    if(typeof destroyCharts === "function"){
        destroyCharts();
    }

    let user;

    try {
        user = await ensureUser();
    }
    catch(err){

        showView("authView");
        showToast(err.message, "error");

        return;

    }

    if(PUBLIC_ROUTES.includes(page)){

        if(user){
            location.replace("#/projects");
            return;
        }

        showAuth(page);

        return;

    }

    if(!user){

        if(hash && !PUBLIC_ROUTES.includes(page)){
            sessionStorageSet("afterLogin", "#/" + hash);
        }

        location.replace("#/login");

        return;

    }

    if(page === "projects"){
        showProjects();
        return;
    }

    if(page === "new"){
        showNewProject();
        return;
    }

    if(page === "project" && parts[1]){

        const projectId =
            Number(parts[1]);

        if(!Number.isInteger(projectId)){
            location.replace("#/projects");
            return;
        }

        if(parts[2] === "setup"){
            showProjectSetup(projectId);
        }
        else {
            showProjectDashboard(projectId);
        }

        return;

    }

    location.replace("#/projects");

}


window.addEventListener("hashchange", route);


session.load();

route();
