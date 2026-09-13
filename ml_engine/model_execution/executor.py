from ml_engine.model_execution.trainer import ModelTrainer
from ml_engine.model_execution.evaluator import ModelEvaluator


class ModelExecutionService:


    def __init__(self):

        self.trainer = ModelTrainer()
        self.evaluator = ModelEvaluator()



    def execute(self,algorithm,X,y,problem_type):

        model = self.trainer.train(algorithm,X,y)
        metrics = self.evaluator.evaluate(model,X,y,problem_type)

        return {

            "algorithm": algorithm,

            "metrics": metrics

        }