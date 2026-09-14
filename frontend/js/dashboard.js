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

        <div id="confusionChart"></div>

    </div>


    `;



    renderMetricsChart(metrics);



    if(metrics.confusion_matrix){

                if(
            metrics.confusion_matrix &&
            metrics.classes
        ){

            renderConfusionMatrix(
                metrics.confusion_matrix,
                metrics.classes
            );

        }

    }

}


function renderConfusionMatrix(matrix, classes) {


    const container =
        document.getElementById(
            "confusionChart"
        );


    let max =
        Math.max(
            ...matrix.flat()
        ) || 1;



    let html = `

    <div class="heatmap-wrapper">

        <table class="heatmap-table">


            <tr>

                <th></th>

                ${
                    classes.map(
                        c =>
                        `<th>${c}</th>`
                    ).join("")
                }

            </tr>

    `;



    matrix.forEach(
        (row,i)=>{


            html += `

            <tr>

                <th>
                    ${classes[i]}
                </th>

            `;


            row.forEach(
                (value,j)=>{


                    const opacity =
                        Math.max(
                            value / max,
                            0.2
                        );


                    const color =
                        i === j
                        ?
                        `rgba(46,204,113,${opacity})`
                        :
                        `rgba(231,76,60,${opacity})`;



                    html += `

                    <td
                    style="
                    background:${color};
                    "
                    >

                    ${value}

                    </td>

                    `;


                }
            );


            html += `</tr>`;


        }
    );



    html += `

        </table>

    </div>

    `;


    container.innerHTML = html;
    console.log(
        "HEATMAP HTML",
        html
    );
}