import pytest

from pathosonar.annotation import Annotator


def test_unknown_executable_path(testdb):
    with pytest.raises(ValueError, match="Annotator executable path is not provided."):
        annotator = Annotator("", "", "")
        annotator.snpeff_annotate("", "", "")
