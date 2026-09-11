const button = document.getElementById("analyzeBtn");


button.addEventListener(
    "click",
    async () => {


        const fileInput =
            document.getElementById("datasetFile");


        const file =
            fileInput.files[0];


        if (!file) {

            alert("فایل انتخاب کنید");

            return;
        }


        const formData =
            new FormData();


        formData.append(
            "file",
            file
        );


        const response =
            await fetch(
                "http://127.0.0.1:8000/analyze-dataset",
                {
                    method: "POST",
                    body: formData
                }
            );


        const result =
            await response.json();



        if (!result.success) {

            document.getElementById("result").innerHTML =
                `
                <div class="error">
                    ${result.error.message}
                </div>
                `;

            return;
        }


        renderAnalysis(result.data);

    }
);



function renderAnalysis(data) {


    const container =
        document.getElementById("result");


    const problems =
        data.problem_recommendations;



    container.innerHTML = `

        <h2>
            تحلیل اولیه دیتاست
        </h2>


        <div class="cards">


            ${createProblemCard(
                problems.classification
            )}


            ${createProblemCard(
                problems.clustering
            )}


        </div>


    `;

}



function createProblemCard(problem) {


    const reasons =
        problem.reasons
        .map(
            r => `<li>${r}</li>`
        )
        .join("");



    return `

    <div class="card">

        <h3>
            ${problem.problem_type}
        </h3>


        <p>
            امتیاز:
            ${problem.score}
        </p>


        <ul>
            ${reasons}
        </ul>


        <button onclick="selectProblem('${problem.problem_type}')">
            انتخاب ${problem.problem_type}
        </button>


    </div>

    `;

}



let selectedProblemType = null;


function selectProblem(type) {


    selectedProblemType = type;


    console.log(
        "Selected:",
        selectedProblemType
    );


    if(type === "classification") {

        showTargetSelection();

    }


    if(type === "clustering") {

        showClusteringPreferences();

    }

}

function showTargetSelection(){


    const container =
        document.getElementById("result");


    container.innerHTML = `

        <h2>
            انتخاب هدف پیش‌بینی
        </h2>


        <p>
            در حال دریافت Target های پیشنهادی...
        </p>

    `;

}