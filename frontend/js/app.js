window.analysisData = null;
window.selectedProblemType = null;
window.selectedTarget = null;
window.selectedPreferences = null;
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
            window.analysisData = result.data;



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





function selectProblem(type) {

    window.selectedProblemType = type;



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
        analysisData.recommended_targets || [];


    const possible =
        analysisData.possible_targets || [];



    let html = `

        <h2>
            انتخاب نتیجه مورد نظر
        </h2>

        <p>
            سیستم این موارد را برای پیش‌بینی مناسب تشخیص داده است.
        </p>

    `;



    if(recommended.length > 0){


        html += `

        <h3>
            پیشنهاد اصلی سیستم
        </h3>

        `;


        recommended.forEach(target => {


            html += createTargetCard(
                target,
                true
            );


        });


    }



    if(possible.length > 0){


        html += `

        <h3>
            سایر گزینه‌های قابل بررسی
        </h3>

        `;


        possible.forEach(target => {


            html += createTargetCard(
                target,
                false
            );


        });


    }


    if(analysisData.target_required){

            html += `
        
            <div class="card">
        
                <h3>
                    نتیجه مشخصی پیدا نشد
                </h3>
        
        
                <p>
                    برای انجام Classification باید Target ساخته شود.
                </p>
        
        
                <label>
        
                    <input
                    type="radio"
                    name="target_generation"
                    value="manual">
        
                    خودم Target را وارد می‌کنم
        
                </label>
        
        
                <br>
        
        
                <label>
        
                    <input
                    type="radio"
                    name="target_generation"
                    value="clustering">
        
                    سیستم با Clustering گروه‌بندی کند
        
                </label>
        
        
                <br>
        
        
                <label>
        
                    <input
                    type="radio"
                    name="target_generation"
                    value="ai">
        
                    پیشنهاد هوشمند AI
        
                </label>
        
        
                <br><br>
        
        
                <button onclick="submitTargetGenerationMode()">
        
                    ادامه
        
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


function createTargetCard(target, recommended){


    return `

    <div class="card">


        <h3>
            ${target.column}
        </h3>


        <p>

            ${
                recommended
                ?
                "پیشنهاد مناسب‌تر برای پیش‌بینی"
                :
                "گزینه جایگزین"
            }

        </p>


        <ul>

            ${
                target.reason
                .map(
                    r => `<li>${r}</li>`
                )
                .join("")
            }

        </ul>



        <button onclick="selectTarget('${target.column}')">

            انتخاب این نتیجه

        </button>


    </div>

    `;


}



function selectTarget(target){


    window.selectedTarget = target;


    console.log(
        "Selected target:",
        selectedTarget
    );


    showPreferences();


}


function submitTargetGenerationMode(){


    const mode =
        document.querySelector(
            'input[name="target_generation"]:checked'
        )?.value;



    if(!mode){

        alert(
            "یک روش انتخاب کنید"
        );

        return;

    }



    window.targetGenerationMode = mode;
    window.labelGenerationMode =
    mode === "clustering";

    if(mode === "clustering"){

    window.labelGenerationMode = true;

    window.selectedProblemType = "clustering";

    showClusteringPreferences();

    }

    if(mode === "manual"){

    showManualTargetSelection();

    }


    if(mode === "ai"){

        console.log(
            "AI target suggestion selected"
        );

    }

}


function showManualTargetSelection(){

    const container =
        document.getElementById("result");
    const targets =
    analysisData.manual_targets || [];

    console.log(
    "MANUAL TARGETS:",
    analysisData.manual_targets
);
    container.innerHTML = `

    <h2>
        انتخاب Target دستی
    </h2>


    <div class="card">

        <select id="manualTarget">

                    ${
                        targets
                        .map(
                        target =>
                        `
                        <option value="${target.column}">
                        ${target.column}
                        (score: ${target.score})
                        </option>
                        `
                        )
                        .join("")
            }

        </select>


        <br><br>


        <button onclick="submitManualTarget()">
            ادامه
        </button>


    </div>

    `;

}



function submitManualTarget(){

    const target =
        document.getElementById(
            "manualTarget"
        ).value;


    window.selectedTarget =
        target;


    window.selectedProblemType =
        "classification";


    console.log(
        "MANUAL TARGET:",
        target
    );


    showPreferences();

}