import json


class LLMTargetService:


    def generate_target_definition(
            self,
            dataset_profile
    ):


        prompt_data = json.dumps(
            dataset_profile,
            indent=2
        )


        print(
            "LLM INPUT:"
        )

        print(
            prompt_data
        )


        # این قسمت بعداً API واقعی LLM می‌شود


        columns = (
            dataset_profile["numeric_columns"]
        )


        return {


            "target_name":
                "generated_target",


            "classes":[

                "Low",

                "Medium",

                "High"

            ],


            "important_features":
                columns[:3],


            "reason":
                "Generated from important dataset features"

        }