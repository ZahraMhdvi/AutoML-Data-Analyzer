


import numpy as np
import pandas as pd
from sklearn.model_selection import ShuffleSplit, StratifiedShuffleSplit

from ml_engine.errors import AppError


DEFAULT_TEST_SIZE = 0.2
DEFAULT_SEED = 42


def _split_one(positions, labels, test_size, seed):
    n = len(positions)

    if n < 5:
        return positions, np.array([], dtype=int), "train_only_small_batch"

    n_test = max(1, int(round(n * test_size)))

    if labels is not None:
        counts = pd.Series(labels).value_counts()
        if counts.min() >= 2 and n_test >= len(counts) and n - n_test >= len(counts):
            splitter = StratifiedShuffleSplit(n_splits=1, test_size=n_test, random_state=seed)
            train, test = next(splitter.split(np.zeros(n), labels))
            return positions[train], positions[test], "stratified"

    splitter = ShuffleSplit(n_splits=1, test_size=n_test, random_state=seed)
    train, test = next(splitter.split(np.zeros(n)))
    return positions[train], positions[test], "random"


def batch_split(n_rows, batch_ids=None, labels=None, test_size=DEFAULT_TEST_SIZE, seed=DEFAULT_SEED):


    batch_ids = np.ones(n_rows, dtype=int) if batch_ids is None else np.asarray(batch_ids)
    labels = None if labels is None else np.asarray(labels)

    train_parts, test_parts, modes = [], [], {}

    for batch in sorted(pd.unique(batch_ids)):
        positions = np.flatnonzero(batch_ids == batch)
        batch_labels = None if labels is None else labels[positions]
        train, test, mode = _split_one(positions, batch_labels, test_size, seed + int(batch) - 1)
        train_parts.append(train)
        test_parts.append(test)
        modes[int(batch)] = mode

    train = np.sort(np.concatenate(train_parts)) if train_parts else np.array([], dtype=int)
    test = np.sort(np.concatenate(test_parts)) if test_parts else np.array([], dtype=int)

    if labels is not None and len(test):

        train_classes = set(labels[train])
        missing = [position for position in test if labels[position] not in train_classes]
        if missing:
            train = np.sort(np.concatenate([train, missing]))
            test = np.setdiff1d(test, missing)

    if len(test) == 0 or len(train) == 0:
        raise AppError("SPLIT_NOT_POSSIBLE")

    info = {
        "strategy": "per_version_batch_split",
        "modes": modes,
        "test_size": test_size,
        "seed": seed,
        "train_rows": int(len(train)),
        "test_rows": int(len(test)),
        "first_batch_test_rows": int(np.sum(batch_ids[test] == sorted(pd.unique(batch_ids))[0])),
    }
    return train, test, info


class DataSplitter:


    def split(self, X, y, test_size=DEFAULT_TEST_SIZE, random_state=DEFAULT_SEED):
        train, test, _ = batch_split(len(X), labels=np.asarray(y), test_size=test_size, seed=random_state)
        y = pd.Series(np.asarray(y), index=X.index)
        return X.iloc[train], X.iloc[test], y.iloc[train].to_numpy(), y.iloc[test].to_numpy()
