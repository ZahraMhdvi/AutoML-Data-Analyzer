from ml_engine.model_selection.model_selection_context import (
    ModelSelectionContext
)



context = ModelSelectionContext(

    problem_type="classification",

    profile={
        "shape":{
            "rows":100,
            "columns":5
        }
    },

    columns={
        "Age":{
            "semantic_type":"numerical"
        }
    },

    target="Bought",

    clean_data_shape={
        "rows":95,
        "columns":6
    },

    user_preferences={"high_accuracy":True })

print(context)