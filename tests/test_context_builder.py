from ml_engine.analyzer_service import DatasetAnalyzer
from ml_engine.model_selection.preference_mapper import map_classification_preferences
from ml_engine.model_selection.preference_schema import UserPreferences

from ml_engine.preprocessing.pipeline import PreprocessingPipeline

from ml_engine.model_selection.context_builder import (ModelSelectionContextBuilder)

analyzer = DatasetAnalyzer()
analysis = analyzer.analyze("data/customers.xlsx")
df = analysis["dataframe"]
pipeline = PreprocessingPipeline(df)
clean_df = pipeline.process()
builder = ModelSelectionContextBuilder()
preferences = UserPreferences(
    main_goal="accuracy",
    data_growth="continuous_data",
    feature_dimension="high_dimension",
    noise_presence="has_noise"
)


mapped = map_classification_preferences(preferences)
context = builder.build(analysis,clean_df,mapped)
print(context)