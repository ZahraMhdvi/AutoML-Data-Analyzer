from ml_engine.model_execution.trainer import ModelTrainer
from ml_engine.model_execution.evaluator import ModelEvaluator
from ml_engine.model_execution.split_manager import DataSplitter



class ModelExecutionService:


    def __init__(self):

        self.trainer = ModelTrainer()

        self.evaluator = ModelEvaluator()

        self.splitter = DataSplitter()



    def execute(
            self,
            algorithm,
            X,
            y,
            problem_type
    ):


        if problem_type == "classification":


            X_train, X_test, y_train, y_test = (
                self.splitter.split(
                    X,
                    y
                )
            )


            model = self.trainer.train(
                algorithm,
                X_train,
                y_train
            )


            metrics = self.evaluator.evaluate(
                model,
                X_test,
                y_test,
                problem_type
            )



        elif problem_type == "clustering":


            model = self.trainer.train(
                algorithm,
                X
            )


            metrics = self.evaluator.evaluate(
                model,
                X,
                None,
                problem_type
            )


        else:

            raise ValueError(
                "Unsupported problem type"
            )



        return {

            "algorithm": algorithm,

            "metrics": metrics

        }