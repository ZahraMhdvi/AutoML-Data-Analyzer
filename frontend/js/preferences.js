function showPreferences(){


    document.getElementById("result").innerHTML = `


    <h2>
        تنظیمات تحلیل
    </h2>


    <div class="card">


        <h3>
            هدف اصلی شما چیست؟
        </h3>


        <label>
            <input 
            type="radio"
            name="goal"
            value="accuracy">
            بالاترین دقت
        </label>


        <br>


        <label>
            <input 
            type="radio"
            name="goal"
            value="speed">
            سرعت بیشتر
        </label>


        <br>


        <label>
            <input 
            type="radio"
            name="goal"
            value="interpretability">
            قابل توضیح بودن مدل
        </label>



    </div>



    <div class="card">


        <h3>
            وضعیت رشد داده
        </h3>


        <label>
            <input 
            type="radio"
            name="growth"
            value="static_data">
            ثابت
        </label>


        <br>


        <label>
            <input 
            type="radio"
            name="growth"
            value="growing_data">
            در حال رشد
        </label>


    </div>




    <div class="card">


        <h3>
            تعداد ویژگی‌ها
        </h3>


        <label>
            <input
            type="radio"
            name="dimension"
            value="normal_dimension">
            معمولی
        </label>


        <br>


        <label>
            <input
            type="radio"
            name="dimension"
            value="high_dimension">
            زیاد
        </label>


    </div>




    <div class="card">


        <h3>
            نویز در داده
        </h3>


        <label>
            <input
            type="radio"
            name="noise"
            value="has_noise">
            وجود دارد
        </label>


        <br>


        <label>
            <input
            type="radio"
            name="noise"
            value="no_noise">
            وجود ندارد
        </label>


    </div>



    <button onclick="submitPreferences()">

        ادامه

    </button>


    `;


}



function submitPreferences(){


    const preferences = {


        main_goal:
        document.querySelector(
            'input[name="goal"]:checked'
        )?.value,


        data_growth:
        document.querySelector(
            'input[name="growth"]:checked'
        )?.value,


        feature_dimension:
        document.querySelector(
            'input[name="dimension"]:checked'
        )?.value,


        noise_presence:
        document.querySelector(
            'input[name="noise"]:checked'
        )?.value


    };



    window.selectedPreferences = preferences;
    setStep("model");
    runModelSelection();


}
