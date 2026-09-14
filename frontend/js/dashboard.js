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

            <h3>
            Accuracy
            </h3>

            <h2>
            ${(metrics.accuracy * 100).toFixed(2)}%
            </h2>

        </div>



        <div class="card">

            <h3>
            Precision
            </h3>

            <h2>
            ${(metrics.precision * 100).toFixed(2)}%
            </h2>

        </div>



        <div class="card">

            <h3>
            Recall
            </h3>

            <h2>
            ${(metrics.recall * 100).toFixed(2)}%
            </h2>

        </div>



        <div class="card">

            <h3>
            F1
            </h3>

            <h2>
            ${(metrics.f1 * 100).toFixed(2)}%
            </h2>

        </div>


    </div>


    `;


}