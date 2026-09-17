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
            <div id="clusterCountInput" style="display:none">
    
        <label>
            تعداد کلاستر:
        </label>
    
        <input
        type="number"
        id="clusterCount"
        min="2"
        placeholder="مثلا 3">
    
    </div>

    </div>



    <button onclick="submitClusteringPreferences()">

        ادامه

    </button>


    `;
    document
.querySelectorAll(
    'input[name="cluster_number"]'
)
.forEach(
    radio => {

        radio.addEventListener(
            "change",
            ()=>{


                const box =
                document.getElementById(
                    "clusterCountInput"
                );


                if(
                    radio.value === "known"
                    &&
                    radio.checked
                ){

                    box.style.display =
                    "block";

                }

                else if(
                    radio.value === "unknown"
                    &&
                    radio.checked
                ){

                    box.style.display =
                    "none";

                }

            }
        );

    }
);

}



function submitClusteringPreferences(){

    const clusterCount =
    document.getElementById(
        "clusterCount"
    )?.value;
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


    cluster_count:
        clusterNumber === "known"
        ?
        Number(clusterCount)
        :
        null,


    cluster_shape:
        clusterGoal === "pattern_discovery"
        ?
        "irregular"
        :
        "unknown",


    hierarchical_analysis:
        clusterGoal === "customer_segmentation"

};


    window.selectedPreferences = preferences;


    window.selectedProblemType = "clustering";

    window.selectedTarget = "";

    setStep("model");

    runModelSelection();





}



function continueWithClustering(){


    window.selectedProblemType =
        "clustering";


    window.selectedTarget =
        "";


    setStep("model");

    runModelSelection();

}