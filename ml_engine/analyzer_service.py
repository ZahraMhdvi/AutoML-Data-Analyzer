


from ml_engine.dataset_loader import DatasetLoader
from ml_engine.profiler import DatasetProfiler
from ml_engine.column_analyzer import ColumnAnalyzer
from ml_engine.target_detector import TargetDetector
from ml_engine.eligibility import EligibilityChecker


class DatasetAnalyzer:

    def __init__(self):

        self.loader = DatasetLoader()




    def analyze(self, file_path):

        dataframe = self.loader.load_excel(file_path)
        profiler = DatasetProfiler(dataframe)

        profile = profiler.generate_report()
        column_analyzer = ColumnAnalyzer(dataframe)

        columns = column_analyzer.analyze()

        target_detector = TargetDetector(dataframe,columns)

        targets = target_detector.detect()

        eligibility = EligibilityChecker(
            dataframe,
            columns,
            targets
        )

        result = eligibility.evaluate()
        return {
            "profile": profile,
            "columns": columns,
            "targets": targets,
            "eligibility": result
        }