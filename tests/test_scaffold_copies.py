"""The scaffold's version-independent helpers must match their copies in v2.

`python -m dug_data_model.scaffold new` copies these files into each new version, so that a
released version is a snapshot that a later change to the scaffold cannot alter. That is why
they are copies rather than one shared module. The cost is that a fix made to one copy can be
forgotten in the other, and the next generated version would then bring the bug back; this
catches that. If a version ever needs its own behaviour in one of these files, drop the file
from COPIED for that version and say why.
"""

from pathlib import Path

import pytest

PACKAGE = Path(__file__).parent.parent / "src" / "dug_data_model"
COPIED = ["utils.py", "validation.py"]


@pytest.mark.parametrize("name", COPIED)
def test_v2_copy_matches_the_scaffold(name):
    assert (PACKAGE / "v2" / name).read_text() == (PACKAGE / "scaffold" / name).read_text()
