function showClusteringPreferences(){


    const container =
        document.getElementById("result");


    container.innerHTML = `


    <h2>
        تنظیمات پیدا کردن گروه‌های مشابه
    </h2>


    <div class="card">


        <h3>
            هدف شما از گروه‌بندی چیست؟
        </h3>


        <label>

            <input
            type="radio"
            name="cluster_goal"
            value="customer_segmentation">

            شناخت گروه‌های مختلف کاربران

        </label>


        <br>


        <label>

            <input
            type="radio"
            name="cluster_goal"
            value="pattern_discovery">

            پیدا کردن الگوهای پنهان

        </label>


    </div>



    <div class="card">


        <h3>
            آیا تعداد گروه‌ها را می‌دانید؟
        </h3>


        <label>

            <input
            type="radio"
            name="cluster_number"
            value="unknown">

            خیر، سیستم پیشنهاد دهد

        </label>


        <br>


        <label>

            <input
            type="radio"
            name="cluster_number"
            value="known">

            بله، خودم مشخص می‌کنم

        </label>


    </div>



    <button onclick="submitClusteringPreferences()">

        ادامه

    </button>


    `;

}



function submitClusteringPreferences(){


    const clusterNumber =
        document.querySelector(
            'input[name="cluster_number"]:checked'
        )?.value;


    const clusterGoal =
        document.querySelector(
            'input[name="cluster_goal"]:checked'
        )?.value;



    const preferences = {


        cluster_count_known:
            clusterNumber === "known",


        cluster_shape:
            clusterGoal === "pattern_discovery"
            ? "irregular"
            : "unknown",


        hierarchical_analysis:
            clusterGoal === "customer_segmentation"


    };


    window.selectedPreferences = preferences;


    window.selectedProblemType = "clustering";


    window.selectedTarget = "";



        if(window.labelGenerationMode){

        runClusteringForLabelGeneration();

    }
    else{

        runModelSelection();

    }

}



async function runClusteringForLabelGeneration(){


    const formData =
        new FormData();


    const file =
        document.getElementById(
            "datasetFile"
        ).files[0];


    formData.append(
        "file",
        file
    );



    const response =
        await fetch(
            "http://127.0.0.1:8000/generate-target-from-clusters",
            {
                method:"POST",
                body:formData
            }
        );


    const result =
        await response.json();



    console.log(
        "GENERATED TARGET:",
        result
    );


}