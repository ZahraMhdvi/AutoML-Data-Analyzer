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


    document.getElementById("result")
    .innerHTML = `


    <h2>
        پیشنهاد مدل مناسب
    </h2>


    <pre>
        ${JSON.stringify(
            result,
            null,
            2
        )}
    </pre>


    `;

}