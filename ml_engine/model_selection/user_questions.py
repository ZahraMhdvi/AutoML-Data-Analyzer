CLASSIFICATION_QUESTIONS = [

    {
        "id": "main_goal",

        "question":
        "مهم‌ترین چیزی که از مدل انتظار دارید چیست؟",

        "options": [

            {
                "label":
                "بیشترین دقت ممکن را می‌خواهم",

                "value":
                "accuracy"
            },

            {
                "label":
                "سرعت بالاتر برای من مهم‌تر است",

                "value":
                "speed"
            },

            {
                "label":
                "می‌خواهم دلیل تصمیم مدل را بتوانم بفهمم",

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
    },


    {
        "id": "feature_dimension",

        "question":
        "آیا تعداد ویژگی‌های شما نسبت به تعداد داده‌ها زیاد است؟",

        "options": [

            {
                "label":
                "بله، ویژگی‌های زیادی نسبت به تعداد داده‌ها دارم",

                "value":
                "high_dimension"
            },

            {
                "label":
                "خیر، تعداد ویژگی‌ها معمولی است",

                "value":
                "normal_dimension"
            }

        ]
    },


    {
        "id": "noise_presence",

        "question":
        "آیا احتمال وجود داده‌های غیرعادی یا اطلاعات اشتباه در داده‌ها وجود دارد؟",

        "options": [

            {
                "label":
                "بله، احتمال وجود داده‌های غیرعادی وجود دارد",

                "value":
                "has_noise"
            },

            {
                "label":
                "خیر، داده‌ها تقریباً تمیز هستند",

                "value":
                "no_noise"
            },

            {
                "label":
                "مطمئن نیستم",

                "value":
                "unknown_noise"
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
                "خیر، می‌خواهم سیستم خودش تعداد گروه‌ها را پیدا کند",

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
                "بله، ممکن است داده‌های پرت وجود داشته باشد",

                "value":
                "has_noise"
            },

            {
                "label":
                "خیر، داده‌ها تقریباً مشابه هستند",

                "value":
                "no_noise"
            },

            {
                "label":
                "مطمئن نیستم",

                "value":
                "unknown_noise"
            }

        ]
    },


    {
        "id":
        "cluster_shape",

        "question":
        "انتظار دارید گروه‌هایی که پیدا می‌شوند چه شکلی باشند؟",

        "options": [

            {
                "label":
                "گروه‌ها تقریباً مشابه و منظم هستند",

                "value":
                "similar_clusters"
            },

            {
                "label":
                "ممکن است گروه‌ها شکل‌های متفاوت و پیچیده داشته باشند",

                "value":
                "irregular_clusters"
            }

        ]
    },


    {
        "id":
        "hierarchical_analysis",

        "question":
        "آیا ارتباط و شباهت بین گروه‌ها برای شما مهم است؟",

        "options": [

            {
                "label":
                "بله، ساختار ارتباط بین گروه‌ها مهم است",

                "value":
                "need_hierarchy"
            },

            {
                "label":
                "خیر، فقط تقسیم‌بندی نهایی گروه‌ها مهم است",

                "value":
                "only_groups"
            }

        ]
    }

]