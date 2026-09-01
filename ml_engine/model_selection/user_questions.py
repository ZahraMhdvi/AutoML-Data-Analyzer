CLASSIFICATION_QUESTIONS = [

    {
        "id": "main_goal",

        "question":
        "مهم‌ترین چیزی که از مدل انتظار دارید چیست؟",

        "options": [

            {
                "label":
                "بیشترین دقت ممکن",

                "value":
                "accuracy"
            },


            {
                "label":
                "سرعت بالاتر",

                "value":
                "speed"
            },


            {
                "label":
                "قابل توضیح بودن نتیجه",

                "value":
                "interpretability"
            }

        ]
    },


    {
        "id": "data_growth",

        "question":
        "آیا در آینده داده‌های جدید به سیستم اضافه می‌شود؟",

        "options": [

            {
                "label":
                "بله، مرتب داده جدید اضافه می‌شود",

                "value":
                "continuous_data"
            },


            {
                "label":
                "خیر، داده تقریباً ثابت است",

                "value":
                "static_data"
            }

        ]
    }

]




CLUSTERING_QUESTIONS = [

    {
        "id":
        "cluster_count_known",


        "question":
        "آیا از قبل می‌دانید داده‌ها باید به چند گروه تقسیم شوند؟",


        "options": [

            {

                "label":
                "بله، تعداد گروه‌ها مشخص است",

                "value":
                "known_clusters"

            },


            {

                "label":
                "خیر، می‌خواهم سیستم خودش گروه‌ها را پیدا کند",

                "value":
                "unknown_clusters"

            }

        ]

    },


    {
        "id":
        "noise_presence",


        "question":
        "آیا احتمال وجود داده‌های غیرعادی یا نقاط متفاوت وجود دارد؟",


        "options": [

            {

                "label":
                "بله، ممکن است داده‌های پرت داشته باشم",

                "value":
                "has_noise"

            },


            {

                "label":
                "خیر، داده‌ها تقریباً مشابه هستند",

                "value":
                "no_noise"

            }

        ]

    }

]