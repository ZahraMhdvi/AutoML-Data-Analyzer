from ml_engine.model_selection.dataset_feature_analyzer import (DatasetFeatureAnalyzer)
from ml_engine.model_selection.model_selection_context import (ModelSelectionContext)


context = ModelSelectionContext(

    problem_type="classification",
    profile={},
    columns={

        "Age":{
            "semantic_type":"numerical"
        },

        "Income":{
            "semantic_type":"numerical"
        },

        "Gender":{
            "semantic_type":"categorical"
        }
    },

    target="Bought",
    clean_data_shape={
        "rows":5000,
        "columns":20
    },

    user_preferences={})

analyzer = DatasetFeatureAnalyzer()
print(analyzer.analyze(context))