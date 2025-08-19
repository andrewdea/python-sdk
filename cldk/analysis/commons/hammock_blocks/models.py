from pydantic import BaseModel
from typing import List, Optional


class HammockBlock(BaseModel):
    """Represents a Hammock block."""

    block_id: int
    block_full_qualifier: str
    project_full_qualifier: str
    block_type: str
    start_line: int = -1
    end_line: int = -1
    meta_data: dict = {}
    children: List[int] = []
    parent: Optional[int] = None
    # call_sites: List[JCallSite] = []
    # local_variables: List[JVariableDeclaration] = []
    # # accessed_variables: List[JSymbol] = []
    # class_attributes: List[JVariableDeclaration] = []
    # func_parameters: List[JCallableParameter] = []
    # relations: List["JHammockBlockRelation"] = []


class HammockBlockRelation(BaseModel):
    """Represents a Hammock block relation."""

    relation_type: str
    related_block_id: int
    related_block_full_qualifier: str
    related_project_full_qualifier: str
    related_block_type: str
    # related_variables: Optional[
    #     Tuple[
    #         PySymbol,
    #         Optional[PyVariableDeclaration | PyCallableParameter | PyClassAttribute],
    #     ]
    # ] = None
    # related_call_site: Optional[PyCallsite] = None
