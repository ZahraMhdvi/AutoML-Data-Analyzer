let analysisData = null;
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
            analysisData = result.data;



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


    const explanation =
        getProblemExplanation(
            problem.problem_type
        );


    const reasons =
        problem.reasons
        .map(
            r => `<li>${translateReason(r)}</li>`
        )
        .join("");



    const examples =
        explanation.examples
        .map(
            e => `<li>${e}</li>`
        )
        .join("");



    return `

    <div class="card">


        <h3>
            ${explanation.title}
        </h3>


        <p>
            ${explanation.description}
        </p>



        <h4>
            چرا پیشنهاد شده؟
        </h4>


        <ul>
            ${reasons}
        </ul>



        <h4>
            مثال کاربرد
        </h4>


        <ul>
            ${examples}
        </ul>



        <p>
            میزان تناسب:
            <b>
            ${getScoreText(problem.score)}
            </b>
        </p>



        <button onclick="selectProblem('${problem.problem_type}')">

            انتخاب این روش

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


    const recommended =
        analysisData.recommended_targets;


    const possible =
        analysisData.possible_targets;



    let html = `

        <h2>
            انتخاب نتیجه‌ای که می‌خواهید پیش‌بینی شود
        </h2>

    `;



    if(recommended.length > 0){


        html += `

        <h3>
            پیشنهاد اصلی سیستم
        </h3>

        `;


        recommended.forEach(target => {


            html += `

            <div class="card">

                <h4>
                    ${target.column}
                </h4>

                <p>
                    میزان اطمینان:
                    بسیار بالا
                </p>

                <ul>

                    ${target.reason
                    .map(
                        r=>`<li>${r}</li>`
                    )
                    .join("")}

                </ul>


                <button>
                    انتخاب ${target.column}
                </button>


            </div>

            `;


        });


    }



    if(possible.length > 0){


        html += `

        <h3>
            گزینه‌های دیگر
        </h3>

        `;


        possible.forEach(target=>{


            html += `

            <button>
                ${target.column}
            </button>

            `;


        });


    }



    if(
        analysisData.target_required
    ){

        html += `

        <div class="card">

            <h3>
                نتیجه مشخصی پیدا نشد
            </h3>


            <p>
                آیا می‌خواهید خودتان نتیجه‌ای تعریف کنید
                یا سیستم پیشنهاد دهد؟
            </p>


            <button>
                تعریف نتیجه توسط من
            </button>


            <button>
                پیشنهاد توسط سیستم
            </button>


        </div>

        `;

    }


    container.innerHTML = html;


}

function translateReason(reason) {


    const dictionary = {


        "Classification is possible":
        "اطلاعات لازم برای پیش‌بینی یک نتیجه مشخص وجود دارد",


        "Strong target candidate detected":
        "یک ستون نتیجه مناسب در داده‌ها پیدا شد",


        "Enough features available for clustering":
        "اطلاعات کافی برای پیدا کردن گروه‌های مشابه وجود دارد",


        "Multiple numerical features available":
        "چندین ویژگی عددی برای مقایسه داده‌ها وجود دارد",


        "Dataset size is suitable for clustering":
        "تعداد داده‌ها برای پیدا کردن الگو مناسب است",


        "Target column exists, classification may be more suitable":
        "یک نتیجه مشخص در داده‌ها وجود دارد و شاید پیش‌بینی آن مناسب‌تر باشد"

    };


    return dictionary[reason] || reason;

}