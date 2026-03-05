from __future__ import annotations

import re
from typing import Any, Literal, override

from pydantic import computed_field

from .base import DugElement

VARIABLE_TYPE = "variable"


class DugVariable(DugElement):
    type: Literal["variable"] = VARIABLE_TYPE
    data_type: str = "text"
    is_cde: bool = False

    @override
    @computed_field
    @property
    def ml_ready_desc(self) -> str:
        """
        Return a description of this variable for use in machine learning.

        For a variable, we also want to incorporate the variable name, both verbatim and (possibly) as a

        :return: A description of this variable for use in machine learning.
        """
        variable_name = self.name

        # TODO: can we incorporate the permissible values somehow?

        # Is this variable name in CamelCase or containing numbers? If so, add spaces between words or numbers.
        cleaned_variable_name = re.sub(
            r'''
            (?<=[a-z])(?=[A-Z0-9])      |  # end lowercase → start uppercase OR number
            (?<=[A-Z])(?=[A-Z][a-z0-9]) |  # acronym → regular word/number
            (?<=[0-9])(?=[A-Za-z])         # number → letter
            ''',
            ' ',
            variable_name,
            flags=re.VERBOSE
        )

        # Is this variable name in snake_case? If so, replace underscores with spaces.
        cleaned_variable_name = re.sub(r'_+', ' ', cleaned_variable_name)

        # Only add the cleaned variable name if it differs from the original.
        if cleaned_variable_name != variable_name:
            return f"{variable_name} ({cleaned_variable_name}): {self.description}"
        return f"{variable_name}: {self.description}"

    def get_searchable_dict(self) -> dict[str, Any]:
        es_elem = super().get_searchable_dict()
        return {
            **es_elem,
            "data_type": self.data_type,
            "is_cde": self.is_cde,
        }
