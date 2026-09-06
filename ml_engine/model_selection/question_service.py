from ml_engine.model_selection.user_questions import (
    CLASSIFICATION_QUESTIONS,
    CLUSTERING_QUESTIONS
)



class QuestionService:


    def get_questions(self,problem_type):

        if problem_type == "classification":
            return CLASSIFICATION_QUESTIONS

        elif problem_type == "clustering":
            return CLUSTERING_QUESTIONS

        else:
            raise ValueError(
                "Unsupported problem type"
            )