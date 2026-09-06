from ml_engine.model_selection.question_service import (QuestionService)


service = QuestionService()
classification_questions = service.get_questions("classification")
print("CLASSIFICATION")
print(classification_questions)
clustering_questions = service.get_questions("clustering")
print("\nCLUSTERING")
print(clustering_questions)