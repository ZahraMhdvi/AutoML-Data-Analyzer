


import pandas as pd
from sklearn.base import BaseEstimator, TransformerMixin


OTHER_CATEGORY = "__other__"


def categorical_columns(frame):
    return [
        column
        for column in frame.columns
        if not pd.api.types.is_numeric_dtype(frame[column])
        or pd.api.types.is_bool_dtype(frame[column])
    ]


class CategoricalEncoder(BaseEstimator, TransformerMixin):

    def __init__(self, dataframe=None, max_categories=30):
        self.dataframe = dataframe
        self.max_categories = max_categories

    def get_categorical_columns(self, frame=None):
        return categorical_columns(self.dataframe if frame is None else frame)


    def fit(self, X, y=None):
        self.columns_ = categorical_columns(X)
        self.mapping_ = {}
        self.capped_ = {}

        for column in self.columns_:
            counts = X[column].astype(str).value_counts()
            categories = list(counts.index)

            if len(categories) > self.max_categories:
                kept = categories[: self.max_categories - 1]
                self.capped_[column] = len(categories) - len(kept)
                categories = sorted(kept) + [OTHER_CATEGORY]
            else:
                categories = sorted(categories)

            self.mapping_[column] = categories


        self.output_columns_ = None
        self.output_columns_ = list(self.transform(X.iloc[:0]).columns)
        self.unseen_counts_ = {}
        return self


    def transform(self, X):
        df = X.copy()
        self.unseen_counts_ = {}

        for column in self.columns_:
            if column not in df.columns:
                continue

            categories = self.mapping_[column]
            values = df[column].astype(str)

            known = set(categories)
            if OTHER_CATEGORY in known:
                values = values.where(values.isin(known), OTHER_CATEGORY)

            unseen = int((~values.isin(known)).sum())
            if unseen:
                self.unseen_counts_[column] = unseen

            if len(categories) == 2:
                df[column] = (values == categories[1]).astype(int)
            elif len(categories) <= 1:
                df[column] = 0
            else:
                position = df.columns.get_loc(column)
                dummies = pd.DataFrame(
                    {f"{column}_{category}": (values == category).astype(int) for category in categories},
                    index=df.index,
                )
                df = df.drop(columns=[column])
                left, right = df.iloc[:, :position], df.iloc[:, position:]
                df = pd.concat([left, dummies, right], axis=1)

        if self.output_columns_ is None:
            self.output_columns_ = list(df.columns)
        else:
            df = df.reindex(columns=self.output_columns_, fill_value=0)

        return df

    def get_params_report(self):
        return {
            column: {
                "type": "binary" if len(categories) == 2 else "one_hot",
                "categories": categories,
                "capped_categories": self.capped_.get(column, 0),
            }
            for column, categories in self.mapping_.items()
        }


    def encode(self):
        return self.fit(self.dataframe).transform(self.dataframe)
