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

    const targetStep =
        document.querySelector(
            '.step[data-step="target"]'
        );


    if(problemType === "clustering"){

        STEP_ORDER = [
            "upload",
            "problem",
            "preferences",
            "model",
            "results"
        ];


        if(targetStep){
            targetStep.style.display = "none";
        }


        document.querySelector(
            '.step[data-step="preferences"] .step__dot'
        ).textContent = "۳";

        document.querySelector(
            '.step[data-step="model"] .step__dot'
        ).textContent = "۴";

        document.querySelector(
            '.step[data-step="results"] .step__dot'
        ).textContent = "۵";


    } else {


        STEP_ORDER = [
            "upload",
            "problem",
            "target",
            "preferences",
            "model",
            "results"
        ];


        if(targetStep){
            targetStep.style.display = "flex";
        }


        document.querySelector(
            '.step[data-step="target"] .step__dot'
        ).textContent = "۳";

        document.querySelector(
            '.step[data-step="preferences"] .step__dot'
        ).textContent = "۴";

        document.querySelector(
            '.step[data-step="model"] .step__dot'
        ).textContent = "۵";

        document.querySelector(
            '.step[data-step="results"] .step__dot'
        ).textContent = "۶";

    }

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
        label.textContent = text || "در حال پردازش...";
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


document.addEventListener("DOMContentLoaded", () => {

    const dropzone = document.getElementById("dropzone");
    const fileInput = document.getElementById("datasetFile");
    const fileNameLabel = document.getElementById("fileNameLabel");

    if (!dropzone || !fileInput) {
        return;
    }

    const updateFileName = () => {

        const file = fileInput.files[0];

        fileNameLabel.textContent = file ? file.name : "";

    };

    dropzone.addEventListener("click", () => fileInput.click());

    fileInput.addEventListener("change", updateFileName);

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

        const file = event.dataTransfer.files[0];

        if (file) {
            fileInput.files = event.dataTransfer.files;
            updateFileName();
        }

    });

    setStep("upload");

});
