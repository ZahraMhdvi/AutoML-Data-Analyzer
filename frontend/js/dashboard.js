function renderMetricsChart(metrics){


    const ctx =
        document
        .getElementById(
            "metricsChart"
        );


    new Chart(
        ctx,
        {

        type:"bar",

        data:{

            labels:[
                "Accuracy",
                "Precision",
                "Recall",
                "F1"
            ],


            datasets:[{

                label:
                "Score",


                data:[
                    metrics.accuracy * 100,
                    metrics.precision * 100,
                    metrics.recall * 100,
                    metrics.f1 * 100
                ]

            }]

        },


        options:{

            scales:{

                y:{
                    beginAtZero:true,
                    max:100
                }

            }

        }

    });

}



function renderDashboard(data){


    const metrics =
        data.metrics;


    document.getElementById("result")
    .innerHTML = `


    <h2>
        داشبورد مدل ${data.algorithm}
    </h2>


    <div class="cards">


        <div class="card">
            <h3>Accuracy</h3>
            <h2>
            ${(metrics.accuracy * 100).toFixed(2)}%
            </h2>
        </div>


        <div class="card">
            <h3>Precision</h3>
            <h2>
            ${(metrics.precision * 100).toFixed(2)}%
            </h2>
        </div>


        <div class="card">
            <h3>Recall</h3>
            <h2>
            ${(metrics.recall * 100).toFixed(2)}%
            </h2>
        </div>


        <div class="card">
            <h3>F1</h3>
            <h2>
            ${(metrics.f1 * 100).toFixed(2)}%
            </h2>
        </div>


    </div>



    <div class="card">

        <h3>
            مقایسه معیارها
        </h3>

        <canvas id="metricsChart"></canvas>

    </div>



    <div class="card">

        <h3>
            Confusion Matrix
        </h3>

        <canvas id="confusionChart"></canvas>

    </div>


    `;



    renderMetricsChart(metrics);



    if(metrics.confusion_matrix){

        renderConfusionMatrix(
            metrics.confusion_matrix
        );

    }

}


function renderConfusionMatrix(matrix){


    const ctx =
    document
    .getElementById(
        "confusionChart"
    );


    const labels =
        matrix.map(
            (_,index)=>
            "Class " + index
        );


    const values =
        matrix.map(
            row =>
            row.reduce(
                (sum,value)=>sum+value,
                0
            )
        );



    new Chart(
        ctx,
        {

        type:"bar",

        data:{

            labels:labels,

            datasets:[{

                label:"Samples",

                data:values

            }]

        }

        }

    );

}