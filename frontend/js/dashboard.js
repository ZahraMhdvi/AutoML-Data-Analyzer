let featureChartInstance = null;
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


    if(
        data.report.problem_type === "clustering"
    ){

        renderClusteringDashboard(data);

    }
    else{

        renderClassificationDashboard(data);

    }

}

function renderClusteringDashboard(data){


    const metrics = data.metrics;


    document.getElementById("result")
    .innerHTML = `


    <h2>
        داشبورد مدل ${data.algorithm}
    </h2>


    <div class="cards">


        <div class="card">

            <h3>
            تعداد کلاسترها
            </h3>

            <h2>
            ${metrics.cluster_count}
            </h2>

        </div>



        <div class="card">

            <h3>
            Noise Points
            </h3>

            <h2>
            ${metrics.noise_points}
            </h2>

        </div>



        <div class="card">

            <h3>
            Silhouette Score
            </h3>

            <h2>
            ${
            metrics.silhouette_score
            ?
            (metrics.silhouette_score * 100).toFixed(2)+"%"
            :
            "-"
            }
            </h2>

        </div>


    </div>
    <div class="card">
    
        <h3>
        اندازه کلاسترها
        </h3>
    
        <canvas id="clusterSizeChart"></canvas>
    
    </div>
    <div class="card">

    <h3>
        نمایش کلاسترها
    </h3>

    <div style="height:500px">

    <canvas id="clusterScatterChart"></canvas>

    </div>

    </div>

    `;
    renderClusterSizeChart(metrics.cluster_sizes);
    renderClusterScatter(metrics.cluster_points);
}

function renderClassificationDashboard(data){


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
    <div id="featureImportanceContainer">
        <div class="card">
    
        <h3>
            Feature Importance
        </h3>
    
        <canvas 
            id="featureChart"
            style="height:400px">
        </canvas>
    
    </div>

    </div>
    `;



    renderMetricsChart(metrics);
    renderFeatureImportance(metrics.feature_importance);



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
}




function renderFeatureImportance(features){


    const container =
        document.getElementById(
            "featureImportanceContainer"
        );


    if(
        !features ||
        features.length === 0
    ){

        container.innerHTML = "";

        return;

    }


    container.innerHTML = `

    <div class="card">

        <h3>
            Feature Importance
        </h3>

        <canvas id="featureChart"></canvas>

    </div>

    `;



    const sorted =
        features
        .filter(
            x => x.feature !== "Customer_ID"
        )
        .sort(
            (a,b)=>
            b.importance - a.importance
        )
        .slice(0,10);



    const values =
        sorted.map(
            x => x.importance * 100
        );



    const ctx =
        document.getElementById(
            "featureChart"
        );


    ctx.height = 400;



    if(featureChartInstance){

        featureChartInstance.destroy();

    }


    featureChartInstance =
        new Chart(
            ctx,
            {

            type:"bar",

            data:{

                labels:
                    sorted.map(
                        x=>x.feature
                    ),

                datasets:[{

                    label:
                    "Importance (%)",

                    data:
                    values

                }]

            },


            options:{

                indexAxis:"y",

                scales:{

                    x:{

                        beginAtZero:true,

                        max:
                        Math.max(...values)+5

                    }

                }

            }

        });


}



function renderClusterSizeChart(clusterSizes){


    const ctx =
        document.getElementById(
            "clusterSizeChart"
        );


    new Chart(
        ctx,
        {

        type:"bar",

        data:{

            labels:
                Object.keys(clusterSizes),


            datasets:[{

                label:
                "Cluster Size",


                data:
                Object.values(clusterSizes)

            }]

        }

    });


}



function renderClusterScatter(points){


    const ctx =
        document.getElementById(
            "clusterScatterChart"
        );


    const clusters = {};


    points.forEach(point => {


        if(!clusters[point.cluster]){

            clusters[point.cluster] = [];

        }


        clusters[point.cluster].push({

            x: point.x,

            y: point.y

        });


    });



    const datasets =
        Object.keys(clusters)
        .map(cluster => ({


            label:
            "Cluster " + cluster,


            data:
            clusters[cluster],


            pointRadius:2


        }));



    new Chart(
        ctx,
        {

        type:"scatter",

        data:{

            datasets:datasets

        },


        options:{


    maintainAspectRatio:false,


    plugins:{

        legend:{

            position:"bottom",

            labels:{

                boxWidth:15,

                padding:15

            }

        }

    },


    scales:{

        x:{

            title:{
                display:true,
                text:"PCA 1"
            }

        },


        y:{

            title:{
                display:true,
                text:"PCA 2"
            }

        }

    }

}

    });


}