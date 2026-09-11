const problemExplanations = {


    classification: {

        title: "پیش‌بینی یک نتیجه مشخص",

        description:
            "در این روش، سیستم از اطلاعات موجود استفاده می‌کند تا یک نتیجه مشخص را برای داده‌های جدید پیش‌بینی کند.",


        examples: [
            "پیش‌بینی احتمال ترک مشتری",
            "پیش‌بینی خرید یا عدم خرید",
            "پیش‌بینی یک وضعیت مشخص"
        ]

    },


    clustering: {


        title: "پیدا کردن گروه‌های مشابه",

        description:
            "در این روش، سیستم بدون داشتن نتیجه از قبل، داده‌ها را بررسی می‌کند و موارد مشابه را در گروه‌های مختلف قرار می‌دهد.",


        examples: [
            "تقسیم مشتریان بر اساس رفتار",
            "شناخت گروه‌های مشابه کاربران",
            "کشف الگوهای پنهان در داده‌ها"
        ]

    }


};



function getProblemExplanation(type) {

    return problemExplanations[
        type.toLowerCase()
    ];

}



function getScoreText(score) {


    if(score >= 80)
        return "بسیار مناسب";


    if(score >= 60)
        return "مناسب";


    if(score >= 40)
        return "قابل بررسی";


    return "ضعیف";

}