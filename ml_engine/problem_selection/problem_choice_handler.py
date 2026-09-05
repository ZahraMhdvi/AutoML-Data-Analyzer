from ml_engine.problem_selection.problem_report import (
    ProblemRecommendation
)



class ProblemChoiceHandler:


    def choose(
            self,
            recommendations: dict,
            selected_problem: str
    ) -> str:


        if selected_problem not in recommendations:

            raise ValueError(
                "Invalid problem type selected"
            )


        recommendation = recommendations[selected_problem]


        if not recommendation.available:

            raise ValueError(
                "Selected problem type is not available"
            )


        return selected_problem