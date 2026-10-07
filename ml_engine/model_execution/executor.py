from ml_engine.model_execution.trainer import ModelTrainer
from ml_engine.model_execution.evaluator import ModelEvaluator
from ml_engine.model_execution.split_manager import DataSplitter
from ml_engine.reporting.report_builder import (ReportBuilder)


class ModelExecutionService:


    def __init__(self):

        self.trainer = ModelTrainer()
        self.evaluator = ModelEvaluator()
        self.splitter = DataSplitter()
        self.report_builder = ReportBuilder()

    def execute(
            self,
            algorithm,
            X,
            y,
            problem_type,
            preferences=None,
            target_classes=None
    ):


        if problem_type == "classification":

            X_train, X_test, y_train, y_test = (
                self.splitter.split(X,y))

            model = self.trainer.train(algorithm,X_train,y_train)
            metrics = self.evaluator.evaluate(model,X_test,y_test,problem_type)


            if target_classes:
                metrics["classes"] = [
                    target_classes[int(label)]
                    if int(label) < len(target_classes)
                    else label
                    for label in metrics["classes"]
                ]


        elif problem_type == "clustering":

            model = self.trainer.train(
                algorithm,
                X,
                cluster_count=
                preferences.get("cluster_count")
                if preferences
                else None
            )
            metrics = self.evaluator.evaluate(model,X,
                None,
                problem_type
            )


        else:

            raise ValueError(
                "Unsupported problem type"
            )

        report = self.report_builder.build(
            {
                "algorithm": algorithm,
                "metrics": metrics
            },
            problem_type
        )

        return {

            "algorithm": algorithm,

            "metrics": metrics,

            "report": report

        }