let featureChartInstance = null;


const PINK_PALETTE = [
    "#ec4899",
    "#f472b6",
    "#d946ef",
    "#e879f9",
    "#fb7185",
    "#f9a8d4",
    "#c084fc",
    "#db2777"
];


function convertToRGBA(hex, alpha){

    const r =
        parseInt(hex.substring(1,3),16);

    const g =
        parseInt(hex.substring(3,5),16);

    const b =
        parseInt(hex.substring(5,7),16);


    return `
        rgba(
            ${r},
            ${g},
            ${b},
            ${alpha}
        )
    `;
}


const SCATTER_COLORS = [
    "#ec4899",
    "#8b5cf6",
    "#06b6d4",
    "#f97316",
    "#22c55e",
    "#e11d48",
    "#14b8a6"
];



function formatPercent(value){

    if(
        value === null ||
        value === undefined
    ){
        return "-";
    }


    return (
        value * 100
    )
    .toFixed(2)
    + "%";

}




function renderDashboard(data){


    setStep(
        "results"
    );


    if(
        data.report.problem_type === "clustering"
    ){

        renderClusteringDashboard(
            data
        );

    }

    else{

        renderClassificationDashboard(
            data
        );

    }

}



function renderClassificationDashboard(data){


    const metrics =
        data.metrics;


    document.getElementById(
        "result"
    )
    .innerHTML = `


    <h2>
        نتیجه تحلیل مدل ${data.algorithm}
    </h2>



    <div class="cards">


        <div class="card">

            <h3>
                دقت کلی مدل
            </h3>

            <h2>
                ${formatPercent(metrics.accuracy)}
            </h2>

        </div>



        <div class="card">

            <h3>
                دقت پیش‌بینی
            </h3>

            <h2>
                ${formatPercent(metrics.precision)}
            </h2>

        </div>



        <div class="card">

            <h3>
                شناسایی موارد درست
            </h3>

            <h2>
                ${formatPercent(metrics.recall)}
            </h2>

        </div>



        <div class="card">

            <h3>
                تعادل عملکرد مدل
            </h3>

            <h2>
                ${formatPercent(metrics.f1)}
            </h2>

        </div>


    </div>





    <div class="card">

        <h3>
            مقایسه عملکرد مدل
        </h3>


        <canvas id="metricsChart"></canvas>

    </div>





    <div class="card">

        <h3>
            مقایسه نتیجه واقعی و پیش‌بینی مدل
        </h3>


        <div id="confusionChart"></div>

    </div>





    <div id="featureImportanceContainer">


        <div class="card">

            <h3>
                میزان اثرگذاری ویژگی‌ها
            </h3>


            <canvas id="featureChart"></canvas>


        </div>


    </div>


    `;



    renderMetricsChart(
        metrics
    );


    renderFeatureImportance(
        metrics.feature_importance
    );



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

function renderConfusionMatrix(
    matrix,
    classes
){


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

        <th>
            نتیجه واقعی / نتیجه مدل
        </th>


        ${
            classes.map(
                c =>
                `<th>
                    ${c}
                </th>`
            )
            .join("")
        }


    </tr>


    `;



    matrix.forEach(
        (row,index)=>{


            html += `

            <tr>


            <th>
                ${classes[index]}
            </th>

            `;



            row.forEach(
                (value,column)=>{


                    const opacity =
                        Math.max(
                            value / max,
                            0.2
                        );



                    const color =

                        index === column

                        ?

                        `rgba(
                            236,
                            72,
                            153,
                            ${opacity}
                        )`

                        :

                        `rgba(
                            192,
                            38,
                            211,
                            ${opacity}
                        )`;



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



            html += `

            </tr>

            `;


        }
    );



    html += `

    </table>

    </div>

    `;



    container.innerHTML =
        html;


}




function renderClusteringDashboard(data){


    const metrics =
        data.metrics;



    document.getElementById(
        "result"
    )
    .innerHTML = `



    <h2>

        نتیجه گروه‌بندی داده‌ها با مدل ${data.algorithm}

    </h2>





    <div class="cards">


        <div class="card">


            <h3>
                تعداد گروه‌های پیدا شده
            </h3>


            <h2>
                ${metrics.cluster_count}
            </h2>


        </div>





        <div class="card">


            <h3>
                تعداد داده‌های غیرعادی
            </h3>


            <h2>
                ${
                    metrics.noise_points ??
                    "-"
                }
            </h2>


        </div>





        <div class="card">


            <h3>
                کیفیت جدا شدن گروه‌ها
            </h3>


            <h2>

            ${
                metrics.silhouette_score !== null &&
                metrics.silhouette_score !== undefined

                ?

                `
                ${metrics.silhouette_score.toFixed(2)}
                
                <br>
                
                <small>
                ${getSilhouetteText(metrics.silhouette_score)}
                </small>
                `

                :

                "-"

            }


            </h2>


        </div>



    </div>






    <div class="card">


        <h3>
            تعداد اعضای هر گروه
        </h3>


        <canvas id="clusterSizeChart"></canvas>


    </div>






    <div class="card">


        <h3>
            پراکندگی داده‌ها در گروه‌ها
        </h3>



        <div
        style="
        height:520px
        "
        >

        <canvas id="clusterScatterChart"></canvas>


        </div>


    </div>



    `;



    renderClusterSizeChart(
        metrics.cluster_sizes
    );



    renderClusterScatter(
        metrics.cluster_points
    );


}



function renderMetricsChart(metrics){


    const ctx =
        document.getElementById(
            "metricsChart"
        );


    new Chart(
        ctx,
        {

            type:"bar",


            data:{

                labels:[

                    "عملکرد کلی مدل",

                    "دقت پیش‌بینی",

                    "شناسایی موارد درست",

                    "تعادل عملکرد"

                ],


                datasets:[{

                    label:
                    "درصد عملکرد",


                    data:[

                        metrics.accuracy * 100,

                        metrics.precision * 100,

                        metrics.recall * 100,

                        metrics.f1 * 100

                    ],


                    backgroundColor:
                    PINK_PALETTE.slice(0,4),


                    borderRadius:10

                }]


            },


            options:{


                responsive:true,


                plugins:{


                    legend:{

                        display:false

                    }


                },


                scales:{


                    y:{


                        beginAtZero:true,


                        max:100,


                        title:{


                            display:true,


                            text:
                            "درصد عملکرد"

                        }


                    },


                    x:{


                        ticks:{


                            maxRotation:0,


                            minRotation:0


                        }

                    }


                }


            }


        }

    );

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



    const sorted =

        features

        .filter(
            x =>
            x.feature !== "Customer_ID"
        )


        .sort(
            (a,b)=>
            b.importance - a.importance
        )


        .slice(0,10);




    const values =

        sorted.map(
            x =>
            x.importance * 100
        );




    const ctx =
        document.getElementById(
            "featureChart"
        );



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
                            x =>
                            x.feature
                        ),



                    datasets:[{


                        label:
                        "میزان اثرگذاری",



                        data:values,



                        backgroundColor:

                            PINK_PALETTE.slice(
                                0,
                                values.length
                            ),



                        borderRadius:10



                    }]


                },



                options:{


                    indexAxis:"y",


                    responsive:true,



                    plugins:{


                        legend:{


                            display:false


                        }


                    },



                    scales:{


                        x:{


                            beginAtZero:true,


                            title:{


                                display:true,


                                text:
                                "درصد اثرگذاری"


                            }


                        }


                    }


                }



            }

        );

}


function renderClusterSizeChart(clusterSizes){


    const ctx =
        document.getElementById(
            "clusterSizeChart"
        );



    if(!ctx || !clusterSizes)
        return;



    const labels =
        Object.keys(
            clusterSizes
        );



    const values =
        Object.values(
            clusterSizes
        );



    new Chart(

        ctx,

        {


            type:"bar",



            data:{


                labels:labels,



                datasets:[{


                    label:
                    "تعداد اعضای هر گروه",



                    data:values,



                    backgroundColor:
                    PINK_PALETTE.slice(
                        0,
                        values.length
                    ),



                    borderRadius:10


                }]


            },



            options:{


                responsive:true,



                plugins:{


                    legend:{


                        display:false


                    }


                },



                scales:{


                    y:{


                        beginAtZero:true,


                        title:{


                            display:true,


                            text:
                            "تعداد داده‌ها"


                        }


                    },



                    x:{


                        title:{


                            display:true,


                            text:
                            "گروه‌ها"


                        }


                    }


                }


            }


        }

    );


}

function renderClusterScatter(points){


    const ctx =
        document.getElementById(
            "clusterScatterChart"
        );



    if(!ctx || !points)
        return;




    const clusters = {};



    points.forEach(
        point => {


            if(!clusters[point.cluster]){

                clusters[point.cluster] = [];

            }



            clusters[point.cluster].push({

                x:
                point.x,


                y:
                point.y

            });


        }
    );





    const datasets =


        Object.keys(clusters)

        .map(

            (cluster,index)=>({



                label:

                    cluster === "-1"

                    ?

                    "داده‌های غیرعادی"

                    :

                    "گروه " + cluster,




                data:

                    clusters[cluster],





                backgroundColor:

                    convertToRGBA(
                        SCATTER_COLORS[
                            index %
                            SCATTER_COLORS.length
                        ],
                        0.45
                    ),





                pointRadius:4,



                pointHoverRadius:7



            })

        );







    new Chart(

        ctx,

        {


            type:"scatter",



            data:{


                datasets:
                datasets


            },



            options:{


                maintainAspectRatio:false,



                plugins:{


                    legend:{


                        position:
                        "bottom",


                        labels:{


                            padding:15,


                            boxWidth:15


                        }


                    }


                },



                scales:{



                    x:{


                        title:{


                            display:true,


                            text:
                            "ویژگی تحلیلی اول"


                        }


                    },



                    y:{


                        title:{


                            display:true,


                            text:
                            "ویژگی تحلیلی دوم"


                        }


                    }


                }


            }


        }

    );

}


function getSilhouetteText(score){

    if(score >= 0.7)
        return "گروه‌بندی بسیار مناسب";

    if(score >= 0.5)
        return "گروه‌بندی مناسب";

    if(score >= 0.25)
        return "گروه‌بندی قابل قبول";

    if(score >= 0)
        return "تفکیک گروه‌ها ضعیف است";

    return "گروه‌ها به خوبی جدا نشده‌اند";

}