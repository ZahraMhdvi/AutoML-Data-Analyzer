const CLASSIFICATION_STEPS = [
    "upload",
    "problem",
    "target",
    "preferences",
    "model",
    "results"
];


const CLUSTERING_STEPS = [
    "upload",
    "problem",
    "preferences",
    "model",
    "results"
];


let currentStepOrder = CLASSIFICATION_STEPS;

let STEP_ORDER = [
    "upload",
    "problem",
    "target",
    "preferences",
    "model",
    "results"
];


function updateStepper(problemType){

    STEP_ORDER = problemType === "clustering" ? CLUSTERING_STEPS.slice() : CLASSIFICATION_STEPS.slice();

    const targetStep =
        document.querySelector('.step[data-step="target"]');

    if(targetStep){
        targetStep.style.display = problemType === "clustering" ? "none" : "flex";
    }

    refreshStepNumbers();

}


function refreshStepNumbers(){

    STEP_ORDER.forEach((step, index) => {
        const dot = document.querySelector(`.step[data-step="${step}"] .step__dot`);
        if(dot){
            dot.textContent = localizeDigits(index + 1);
        }
    });

}
function setProblemSteps(problemType){


    if(problemType === "clustering"){

        currentStepOrder = CLUSTERING_STEPS;

    }
    else{

        currentStepOrder = CLASSIFICATION_STEPS;

    }

}




function setStep(stepName){


    const currentIndex =
        currentStepOrder.indexOf(stepName);



    if(currentIndex === -1)
        return;



    document
    .querySelectorAll("#stepper .step")
    .forEach(el=>{


        const step =
            el.dataset.step;



        const index =
            currentStepOrder.indexOf(step);



        el.classList.remove(
            "step--active",
            "step--done"
        );



        if(index === -1){

            el.style.display="none";

            return;

        }



        el.style.display="flex";



        if(index < currentIndex){

            el.classList.add(
                "step--done"
            );

        }


        else if(index === currentIndex){

            el.classList.add(
                "step--active"
            );

        }


    });


}


function showLoading(text) {

    const overlay = document.getElementById("loadingOverlay");
    const label = document.getElementById("loadingText");

    if (label) {
        label.textContent = text || t("common.processing");
    }

    if (overlay) {
        overlay.classList.add("loading-overlay--visible");
    }

}


function hideLoading() {

    const overlay = document.getElementById("loadingOverlay");

    if (overlay) {
        overlay.classList.remove("loading-overlay--visible");
    }

}


function showToast(message, type) {

    const container = document.getElementById("toastContainer");

    if (!container) {
        return;
    }

    const toast = document.createElement("div");

    toast.className = `toast toast--${type || "info"}`;
    toast.textContent = message;

    container.appendChild(toast);

    requestAnimationFrame(() => {
        toast.classList.add("toast--visible");
    });

    setTimeout(() => {
        toast.classList.remove("toast--visible");
        setTimeout(() => toast.remove(), 300);
    }, 4000);

}




function escapeHtml(value) {

    return String(value ?? "")
        .replace(/&/g, "&amp;")
        .replace(/</g, "&lt;")
        .replace(/>/g, "&gt;")
        .replace(/"/g, "&quot;")
        .replace(/'/g, "&#39;");

}


function toFaDigits(value) {

    return localizeDigits(value);

}


function showView(id) {

    document.querySelectorAll(".view").forEach(view => {
        view.hidden = view.id !== id;
    });

    window.scrollTo({ top: 0 });

}




function openModal(id) {

    const modal = document.getElementById(id);

    if (!modal) {
        return;
    }

    modal.hidden = false;
    document.body.classList.add("modal-open");

    const focusable = modal.querySelector("button:not([data-close-modal]), input, [tabindex]");

    if (focusable) {
        setTimeout(() => focusable.focus(), 30);
    }

}


function closeModal(id) {

    const modal = document.getElementById(id);

    if (!modal) {
        return;
    }

    modal.hidden = true;

    if (!document.querySelector(".modal:not([hidden])")) {
        document.body.classList.remove("modal-open");
    }

}


function confirmDialog(title, text, okLabel = t("common.confirm")) {

    return new Promise(resolve => {

        document.getElementById("confirmTitle").textContent = title;
        document.getElementById("confirmText").textContent = text;

        const ok = document.getElementById("confirmOk");
        ok.textContent = okLabel;

        const modal = document.getElementById("confirmModal");

        const finish = (value) => {
            ok.removeEventListener("click", onOk);
            modal.removeEventListener("modal:closed", onCancel);
            closeModal("confirmModal");
            resolve(value);
        };

        const onOk = () => finish(true);
        const onCancel = () => finish(false);

        ok.addEventListener("click", onOk);
        modal.addEventListener("modal:closed", onCancel);

        openModal("confirmModal");

    });

}


document.addEventListener("click", event => {

    const closer = event.target.closest("[data-close-modal]");

    if (closer) {
        const modal = closer.closest(".modal");
        closeModal(modal.id);
        modal.dispatchEvent(new Event("modal:closed"));
    }

});


document.addEventListener("keydown", event => {

    if (event.key !== "Escape") {
        return;
    }

    const modal = document.querySelector(".modal:not([hidden])");

    if (modal && !document.getElementById("loadingOverlay").classList.contains("loading-overlay--visible")) {
        closeModal(modal.id);
        modal.dispatchEvent(new Event("modal:closed"));
    }

});




function setupDropzone(dropzone, fileInput, fileNameLabel, onChange) {

    if (!dropzone || !fileInput) {
        return;
    }

    const update = () => {

        const file = fileInput.files[0];

        fileNameLabel.textContent = file ? file.name : "";

        dropzone.classList.toggle("dropzone--filled", Boolean(file));

        if (onChange) {
            onChange(file);
        }

    };

    dropzone.addEventListener("click", () => fileInput.click());

    dropzone.addEventListener("keydown", event => {
        if (event.key === "Enter" || event.key === " ") {
            event.preventDefault();
            fileInput.click();
        }
    });

    fileInput.addEventListener("change", update);

    ["dragenter", "dragover"].forEach(eventName => {

        dropzone.addEventListener(eventName, (event) => {
            event.preventDefault();
            dropzone.classList.add("dropzone--active");
        });

    });

    ["dragleave", "drop"].forEach(eventName => {

        dropzone.addEventListener(eventName, (event) => {
            event.preventDefault();
            dropzone.classList.remove("dropzone--active");
        });

    });

    dropzone.addEventListener("drop", (event) => {

        const files = event.dataTransfer.files;

        if (files && files[0]) {
            fileInput.files = files;
            update();
        }

    });

    return {
        reset() {
            fileInput.value = "";
            update();
        }
    };

}
