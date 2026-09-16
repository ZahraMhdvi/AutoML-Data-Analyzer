async function runModelSelection(){


    const formData = new FormData();


    const file =
        document.getElementById(
            "datasetFile"
        ).files[0];


    formData.append(
        "file",
        file
    );
    if(window.generatedDatasetId){

    formData.append(
        "generated_dataset_id",
        window.generatedDatasetId
    );

}

    formData.append(
        "problem_type",
        window.selectedProblemType
    );


    formData.append(
    "target",
    window.selectedProblemType === "clustering"
    ? ""
    : window.selectedTarget
    );

    console.log(
        "SENDING PREFERENCES",
        window.selectedPreferences
    );
    formData.append(
    "preferences",
    JSON.stringify(window.selectedPreferences)
    );


    const response =
        await fetch(
            "http://127.0.0.1:8000/model-selection",
            {
                method:"POST",
                body:formData
            }
        );


    const result =
        await response.json();



    showModelResult(result);


}



function showModelResult(result){


    const container =
        document.getElementById("result");


    if(!result.success){


        container.innerHTML = `

        <div class="error">

            ${result.error.message}

        </div>

        `;

        return;

    }



    const recommendations =
        result.data.recommendations;



    container.innerHTML = `


    <h2>
        پیشنهاد مدل مناسب
    </h2>


    <div class="cards">


        ${
            recommendations
            .map(
                model =>
                createModelCard(model)
            )
            .join("")
        }


    </div>


    `;

}



function createModelCard(model){


    const reasons =
        model.reasons
        .map(
            r => `<li>${r}</li>`
        )
        .join("");



    const limitations =
        model.limitations
        .map(
            l => `<li>${l}</li>`
        )
        .join("");



    return `


    <div class="card">


        <h3>

            ${model.algorithm}

        </h3>



        <p>

            امتیاز سازگاری:

            <b>
            ${model.score}
            </b>

        </p>



        <h4>
            چرا پیشنهاد شده؟
        </h4>


        <ul>

            ${reasons}

        </ul>




        <ul>

            ${
            limitations
            ?
            `
            <h4>
             محدودیت‌ها
            </h4>
            <ul>
            ${limitations}
            </ul>
            `
            :
            `
            <p>
            محدودیت مشخصی برای این مدل ثبت نشده است
            </p>
            `
            }

        </ul>



        <button
        onclick="selectAlgorithm('${model.algorithm}')">

            انتخاب این مدل

        </button>



    </div>


    `;


}



function selectAlgorithm(algorithm){


    window.selectedAlgorithm = algorithm;



    runSelectedModel();

}



async function runSelectedModel(){


    const formData = new FormData();



    const file =
        document.getElementById(
            "datasetFile"
        ).files[0];



    formData.append(
        "file",
        file
    );


    if(window.generatedDatasetId){

    formData.append(
        "generated_dataset_id",
        window.generatedDatasetId
    );

}


    formData.append(
        "algorithm",
        window.selectedAlgorithm
    );



    formData.append(
        "problem_type",
        window.selectedProblemType
    );



    formData.append(
        "target",
        window.selectedProblemType === "clustering"
        ?
        ""
        :
        window.selectedTarget
    );

    formData.append(
    "preferences",
    JSON.stringify(
        window.selectedPreferences
    )
);



    const response =
    await fetch(
        "http://127.0.0.1:8000/run-model",
        {
            method:"POST",
            body:formData
        }
    );



    const result =
        await response.json();


    console.log(
    "RUN MODEL RESPONSE:",
    result
);
    showExecutionResult(result);

}


function showExecutionResult(result){


    if(!result.success){

        document.getElementById("result").innerHTML =
        `
        <div class="error">
        ${result.error.message}
        </div>
        `;

        return;
    }


    renderDashboard(
        result.data
    );

}