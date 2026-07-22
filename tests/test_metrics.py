"""Unit tests for eval metrics -- pure functions, no LLM."""

from src.eval import metrics


def test_accuracy_basic():
    assert metrics.accuracy(["a", "b", "c"], ["a", "x", "c"]) == 2 / 3
    assert metrics.accuracy([], []) == 0.0


def test_perfect_and_zero():
    assert metrics.accuracy(["a", "b"], ["a", "b"]) == 1.0
    assert metrics.accuracy(["a", "a"], ["b", "b"]) == 0.0


def test_confusion_matrix():
    m = metrics.confusion_matrix(["a", "b", "a"], ["a", "a", "b"], ["a", "b"])
    assert m["a"]["a"] == 1  # gold a, pred a
    assert m["a"]["b"] == 1  # gold a, pred b
    assert m["b"]["a"] == 1  # gold b, pred a
    assert m["b"]["b"] == 0


def test_per_class_prf():
    # gold: a a b ; pred: a b b
    prf = metrics.per_class_prf(["a", "b", "b"], ["a", "a", "b"], ["a", "b"])
    # a: tp=1 fp=0 fn=1 -> P=1.0 R=0.5 F1=0.667
    assert prf["a"]["precision"] == 1.0
    assert prf["a"]["recall"] == 0.5
    assert prf["a"]["support"] == 2
    # b: tp=1 fp=1 fn=0 -> P=0.5 R=1.0
    assert prf["b"]["precision"] == 0.5
    assert prf["b"]["recall"] == 1.0


def test_macro_f1_ignores_absent_labels():
    # 'c' never appears in gold -> excluded from macro average
    f1 = metrics.macro_f1(["a", "b"], ["a", "b"], ["a", "b", "c"])
    assert f1 == 1.0


def test_urgency_distance_and_within_n():
    assert metrics.urgency_distance("P1", "P1") == 0
    assert metrics.urgency_distance("P1", "P3") == 2
    assert metrics.urgency_distance("P2", "bogus") is None
    # exact vs within-1
    pred = ["P1", "P2", "P4"]
    gold = ["P1", "P3", "P4"]  # middle is off by 1
    assert metrics.accuracy(pred, gold) == 2 / 3
    assert metrics.within_n_accuracy(pred, gold, 1) == 1.0
