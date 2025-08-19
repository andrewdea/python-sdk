################################################################################
# Copyright IBM Corporation 2024
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#       http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.
################################################################################

"""
Models module
"""

from typing import List, Optional, Literal, Any, Tuple
from cldk.analysis.commons.hammock_blocks.models import (
    HammockBlock,
    HammockBlockRelation,
)
from pydantic import BaseModel


class PyArg(BaseModel):
    arg_name: str
    arg_type: str


class PyImport(BaseModel):
    from_statement: str
    # code_body: str
    imports: List[str]


class PyCallSite(BaseModel):
    method_name: str
    declaring_object: str
    arguments: List[str]
    start_line: int
    start_column: int
    end_line: int
    end_column: int


class PyMethod(BaseModel):
    code_body: str
    method_name: str
    full_signature: str
    num_params: int
    modifier: str
    is_constructor: bool
    is_static: bool
    formal_params: List[PyArg]
    call_sites: List[PyCallSite]
    return_type: str
    class_signature: str
    start_line: int
    end_line: int


class PySymbol(BaseModel):
    """Represents a symbol used or declared in Python code."""

    name: str
    scope: Literal["local", "nonlocal", "global", "class", "module"]
    kind: Literal["variable", "parameter", "attribute", "function", "class", "module"]
    type: Optional[str] = None
    qualified_name: Optional[str] = None
    is_builtin: bool = False
    lineno: int = -1
    col_offset: int = -1


class PyComment(BaseModel):
    """Represents a Python comment."""

    content: str
    start_line: int = -1
    end_line: int = -1
    start_column: int = -1
    end_column: int = -1
    is_docstring: bool = False


# TODO rename this to PyCallSite for consistency
class PyCallsite(BaseModel):
    """Represents a Python call site (function or method invocation) with contextual metadata."""

    method_name: str
    receiver_expr: Optional[str] = None
    receiver_type: Optional[str] = None
    argument_types: List[str] = []
    return_type: Optional[str] = None
    callee_signature: Optional[str] = None
    is_constructor_call: bool = False
    start_line: int = -1
    start_column: int = -1
    end_line: int = -1
    end_column: int = -1


class PyClassAttribute(BaseModel):
    """Represents a Python class attribute."""

    name: str
    type: Optional[str] = None
    comments: List[PyComment] = []
    start_line: int = -1
    end_line: int = -1


class PyVariableDeclaration(BaseModel):
    """Represents a Python variable declaration."""

    name: str
    type: Optional[str]
    initializer: Optional[str] = None
    value: Optional[Any] = None
    scope: Literal["module", "class", "function"] = "module"
    start_line: int = -1
    end_line: int = -1
    start_column: int = -1
    end_column: int = -1


class PyCallableParameter(BaseModel):
    """Represents a parameter of a Python callable (function/method)."""

    name: str
    type: Optional[str] = None
    default_value: Optional[str] = None
    start_line: int = -1
    end_line: int = -1
    start_column: int = -1
    end_column: int = -1


class PyHammockBlock(HammockBlock):
    """Represents a Hammock block in Python code."""

    call_sites: List[PyCallsite] = []
    local_variables: List[PyVariableDeclaration] = []
    accessed_variables: List[PySymbol] = []
    class_attributes: List[PyVariableDeclaration] = []
    func_parameters: List[PyCallableParameter] = []
    relations: List["PyHammockBlockRelation"] = []


class PyHammockBlockRelation(HammockBlockRelation):
    """Represents a Hammock block relation in Python code."""

    related_variables: Optional[
        Tuple[
            PySymbol,
            Optional[PyVariableDeclaration | PyCallableParameter | PyClassAttribute],
        ]
    ] = None
    related_call_site: Optional[PyCallsite] = None


class PyClass(BaseModel):
    code_body: str
    full_signature: str
    super_classes: List[str]
    is_test_class: bool
    class_name: str
    methods: List[PyMethod]


class PyModule(BaseModel):
    qualified_name: str
    functions: List[PyMethod]
    classes: List[PyClass]
    imports: List[PyImport]
    # expressions: str


class PyBuildAttributes(BaseModel):
    """Handles all the project build tool (requirements.txt/poetry/setup.py) attributes"""


class PyConfig(BaseModel):
    """Application configuration information"""
