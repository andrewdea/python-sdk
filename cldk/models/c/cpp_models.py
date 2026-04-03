from __future__ import annotations

from typing import List, Optional, Any
from enum import Enum
from pydantic import BaseModel, ConfigDict, Field, field_validator
from cldk.models.c import CppClass

# -------------------------
# Enums (string-backed)
# -------------------------


class CppAccessSpecifier(str, Enum):
    """Access specifier for class members"""

    PUBLIC = "public"
    PROTECTED = "protected"
    PRIVATE = "private"


class CppRecordKind(str, Enum):
    """Kind of record (class/struct/union)"""

    CLASS = "class"
    STRUCT = "struct"
    UNION = "union"


class CppEdgeKind(str, Enum):
    """Type of call graph edge"""

    DIRECT = "direct"
    VIRTUAL = "virtual"
    FUNCTION_POINTER = "function-pointer"
    OBJECT_CREATION = "object-creation"
    OPERATOR_CALL = "operator-call"
    OBJECT_DESTRUCTION = "object-destruction"
    VIRTUAL_OVERRIDE = "virtual-override"
    STD_FUNCTION_CALL = "std-function-call"


class CppTemplateParamKind(str, Enum):
    """Kind of template parameter"""

    TYPE = "type"
    NON_TYPE = "non_type"
    TEMPLATE = "template"


class CppTemplateRelationKind(str, Enum):
    """Template relation kind"""

    PRIMARY_TEMPLATE = "primary_template"
    PARTIAL_SPECIALIZATION = "partial_specialization"
    EXPLICIT_SPECIALIZATION = "explicit_specialization"
    IMPLICIT_INSTANTIATION = "implicit_instantiation"
    EXPLICIT_INSTANTIATION = "explicit_instantiation"


class CppLinkageKind(str, Enum):
    """Linkage kind"""

    EXTERNAL = "external"
    INTERNAL = "internal"
    NONE = "none"
    UNIQUE_EXTERNAL = "unique_external"


# -------------------------
# Base helper
# -------------------------


class PybindBaseModel(BaseModel):
    """
    Allows constructing directly from pybind objects.
    """

    model_config = ConfigDict(from_attributes=True)

    @classmethod
    def from_pybind(cls, obj: Any):
        return cls.model_validate(obj)


# -------------------------
# Core types
# -------------------------


class SourceLocation(PybindBaseModel):
    file: str
    start_line: int
    start_column: int
    end_line: int
    end_column: int


class CppEntity(PybindBaseModel):
    name: str
    usr: str
    location: SourceLocation
    is_definition: bool
    comment: Optional[str] = None


# -------------------------
# Simple types
# -------------------------


class CppInclude(PybindBaseModel):
    included_file: str
    line: int
    is_system: bool


class CppParameter(PybindBaseModel):
    name: str
    type: str
    type_usr: Optional[str] = None
    has_default: bool = False
    default_value: Optional[str] = None


class CppTemplateParameter(PybindBaseModel):
    """Template parameter information"""

    name: str
    kind: CppTemplateParamKind
    type: str = ""  # For non-type parameters
    default_value: Optional[str] = None

    @field_validator("kind", mode="before")
    @classmethod
    def convert_kind(cls, v):
        """Convert C++ enum or string to Python enum"""
        if isinstance(v, str):
            # Handle string values
            v_lower = v.lower()
            if v_lower == "type":
                return CppTemplateParamKind.TYPE
            elif v_lower == "non_type":
                return CppTemplateParamKind.NON_TYPE
            elif v_lower == "template":
                return CppTemplateParamKind.TEMPLATE
            return v
        if hasattr(v, "name"):
            # Handle C++ enum
            name = v.name.lower()
            if name == "type":
                return CppTemplateParamKind.TYPE
            elif name == "nontype":
                return CppTemplateParamKind.NON_TYPE
            elif name == "template":
                return CppTemplateParamKind.TEMPLATE
        return v


class CppTemplateData(PybindBaseModel):
    """Template metadata"""

    parameters: List[CppTemplateParameter] = Field(default_factory=list)
    relation_kind: Optional[CppTemplateRelationKind] = None
    primary_template_usr: Optional[str] = None
    specialization_args: List[str] = Field(default_factory=list)
    requires_clause: Optional[str] = None
    is_specialization: bool = False
    is_partial_specialization: bool = False

    @field_validator("relation_kind", mode="before")
    @classmethod
    def convert_relation_kind(cls, v):
        """Convert C++ enum to Python enum"""
        if v is None:
            return v
        if hasattr(v, "name"):
            # Convert enum name to snake_case
            name = v.name
            # PrimaryTemplate -> primary_template
            result = "".join(
                [
                    "_" + c.lower() if c.isupper() and i > 0 else c.lower()
                    for i, c in enumerate(name)
                ]
            )
            return result
        return v


class CppField(PybindBaseModel):
    """Field/member variable in a class/struct"""

    name: str
    type: str
    type_usr: Optional[str] = None
    access: CppAccessSpecifier
    location: SourceLocation
    is_mutable: bool = False
    is_static: bool = False
    is_constexpr: bool = False
    initializer: Optional[str] = None
    attributes: List[str] = Field(default_factory=list)

    @field_validator("access", mode="before")
    @classmethod
    def convert_access(cls, v):
        """Convert C++ enum to string"""
        if hasattr(v, "name"):
            return v.name.lower()
        return v


class CppBaseClass(PybindBaseModel):
    """Base class information for inheritance"""

    name: str
    usr: str
    access: CppAccessSpecifier
    is_virtual: bool = False

    @field_validator("access", mode="before")
    @classmethod
    def convert_access(cls, v):
        """Convert C++ enum to string"""
        if hasattr(v, "name"):
            return v.name.lower()
        return v


class CppEnumConstant(PybindBaseModel):
    """Enum constant with its value"""

    name: str
    value: Optional[str] = None  # String representation of the value
    location: SourceLocation
    attributes: List[str] = Field(default_factory=list)

    @field_validator("value", mode="before")
    @classmethod
    def convert_value(cls, v):
        """Convert int to string or handle None"""
        if v is None:
            return None
        if isinstance(v, int):
            return str(v)
        return v


# -------------------------
# Complex types
# -------------------------


class CppFunction(CppEntity):
    """Function or method declaration/definition"""

    return_type: str
    parameters: List[CppParameter] = Field(default_factory=list)

    specifiers: List[str] = Field(default_factory=list)  # List of specifier strings
    linkage: Optional[CppLinkageKind] = None

    is_constructor: bool = False
    is_destructor: bool = False
    is_conversion_operator: bool = False
    is_copy_constructor: bool = False
    is_move_constructor: bool = False
    is_copy_assignment: bool = False
    is_move_assignment: bool = False
    is_method: bool = False

    parent_record_name: Optional[str] = None
    parent_record_usr: Optional[str] = None
    parent_record_type: Optional[str] = None

    operator_symbol: Optional[str] = None
    ref_qualifier: Optional[str] = None
    noexcept_expression: Optional[str] = None
    template_info: Optional[CppTemplateData] = None
    access: Optional[CppAccessSpecifier] = None

    attributes: List[str] = Field(default_factory=list)

    @field_validator("specifiers", mode="before")
    @classmethod
    def convert_specifiers(cls, v):
        """Convert C++ enum or bitfield to list of strings"""
        # Handle pybind11 enum objects - extract the integer value
        if hasattr(v, "value"):
            v = v.value

        if isinstance(v, int):
            # Bitfield - convert to list of flag names
            flags = []
            if v == 0:
                return []
            # FunctionSpecifier bit flags (from SymbolExtraction.h)
            flag_map = {
                1: "inline",  # 1 << 0
                2: "constexpr",  # 1 << 1
                4: "consteval",  # 1 << 2
                8: "static",  # 1 << 3
                16: "virtual",  # 1 << 4
                32: "pure_virtual",  # 1 << 5
                64: "deleted",  # 1 << 6
                128: "defaulted",  # 1 << 7
                256: "explicit",  # 1 << 8
                512: "override",  # 1 << 9
                1024: "final",  # 1 << 10
                2048: "const",  # 1 << 11
                4096: "volatile",  # 1 << 12
                8192: "noexcept",  # 1 << 13
                16384: "variadic",  # 1 << 14
                32768: "friend",  # 1 << 15
                65536: "constinit",  # 1 << 16
            }
            for bit, name in flag_map.items():
                if v & bit:
                    flags.append(name)
            return flags if flags else []
        elif isinstance(v, list):
            return v
        return []

    @field_validator("linkage", mode="before")
    @classmethod
    def convert_linkage(cls, v):
        """Convert C++ enum to Python enum"""
        if v is None:
            return v
        if hasattr(v, "name"):
            return v.name.lower()
        return v

    @field_validator("parent_record_type", mode="before")
    @classmethod
    def convert_parent_record_type(cls, v):
        """Convert C++ enum to string"""
        if hasattr(v, "name"):
            return v.name.lower()
        return v

    @field_validator("access", mode="before")
    @classmethod
    def convert_access(cls, v):
        """Convert C++ enum to string"""
        if v is None:
            return v
        if hasattr(v, "name"):
            return v.name.lower()
        return v


class CppVariable(CppEntity):
    """Variable declaration/definition"""

    type: str
    type_usr: Optional[str] = None

    is_static: bool = False
    is_const: bool = False
    is_constexpr: bool = False
    is_constinit: bool = False
    is_consteval: bool = False
    is_extern: bool = False
    is_thread_local: bool = False
    is_global: bool = False
    has_initializer: bool = False

    initializer: Optional[str] = None
    linkage: Optional[CppLinkageKind] = None

    attributes: List[str] = Field(default_factory=list)

    @field_validator("linkage", mode="before")
    @classmethod
    def convert_linkage(cls, v):
        """Convert C++ enum to Python enum"""
        if v is None:
            return v
        if hasattr(v, "name"):
            return v.name.lower()
        return v


class CppEnum(CppEntity):
    """Enum declaration"""

    is_scoped: bool = False  # enum class vs enum
    underlying_type: str
    constants: List[CppEnumConstant] = Field(default_factory=list)
    attributes: List[str] = Field(default_factory=list)

    @field_validator("constants", mode="before")
    @classmethod
    def convert_constants(cls, v):
        """Handle EnumConstant conversion"""
        if isinstance(v, list):
            result = []
            for item in v:
                if hasattr(item, "__dict__"):
                    # It's a pybind object, convert it
                    result.append(item)
                else:
                    result.append(item)
            return result
        return v


class CppTypedef(CppEntity):
    """Typedef declaration"""

    underlying_type: str
    attributes: List[str] = Field(default_factory=list)


class CppUsing(CppEntity):
    """Using declaration or alias"""

    is_alias: bool = False  # True for using alias, False for using declaration
    target_name: str
    target_usr: str

    underlying_type: Optional[str] = None
    template_info: Optional[CppTemplateData] = None

    attributes: List[str] = Field(default_factory=list)


class CppMacro(CppEntity):
    """Macro definition"""

    definition: str
    parameters: List[str] = Field(default_factory=list)
    is_function_like: bool = False


class CppRecord(CppEntity):
    """Class, struct, or union declaration"""

    kind: CppRecordKind

    is_final: bool = False
    is_abstract: bool = False
    is_polymorphic: bool = False
    is_trivially_copyable: bool = False
    is_anonymous: bool = False
    is_lambda: bool = False

    fields: List[CppField] = Field(default_factory=list)
    bases: List[CppBaseClass] = Field(default_factory=list)

    template_info: Optional[CppTemplateData] = None

    attributes: List[str] = Field(default_factory=list)

    nested_records: List["CppRecord"] = Field(default_factory=list)
    methods: List[CppFunction] = Field(default_factory=list)
    nested_enums: List[CppEnum] = Field(default_factory=list)
    nested_typedefs: List[CppTypedef] = Field(default_factory=list)
    nested_usings: List[CppUsing] = Field(default_factory=list)

    @field_validator("kind", mode="before")
    @classmethod
    def convert_kind(cls, v):
        """Convert C++ enum to string"""
        if hasattr(v, "name"):
            return v.name.lower()
        return v


class CppNamespace(CppEntity):
    """Namespace declaration"""

    is_inline: bool = False
    is_anonymous: bool = False

    attributes: List[str] = Field(default_factory=list)

    namespaces: List["CppNamespace"] = Field(default_factory=list)
    functions: List[CppFunction] = Field(default_factory=list)
    records: List[CppRecord] = Field(default_factory=list)
    variables: List[CppVariable] = Field(default_factory=list)
    enums: List[CppEnum] = Field(default_factory=list)
    typedefs: List[CppTypedef] = Field(default_factory=list)
    usings: List[CppUsing] = Field(default_factory=list)


# -------------------------
# Translation unit
# -------------------------


class CppTranslationUnit(PybindBaseModel):
    """Translation unit (source file) representation"""

    file_path: str
    is_header: bool = False
    language: str

    includes: List[CppInclude] = Field(default_factory=list)
    namespaces: List[CppNamespace] = Field(default_factory=list)
    functions: List[CppFunction] = Field(default_factory=list)
    records: List[CppRecord] = Field(default_factory=list)
    global_variables: List[CppVariable] = Field(default_factory=list)
    enums: List[CppEnum] = Field(default_factory=list)
    typedefs: List[CppTypedef] = Field(default_factory=list)
    usings: List[CppUsing] = Field(default_factory=list)
    macros: List[CppMacro] = Field(default_factory=list)
    classes: List[CppClass] = Field(default_factory=list)


# -------------------------
# Call graph
# -------------------------


class CppCallGraphEdge(PybindBaseModel):
    """Call graph edge representing a function call"""

    caller_name: str
    caller_usr: str
    caller_file: str
    caller_line: int
    call_site_line: int

    callee_name: str
    callee_usr: str
    callee_file: str
    callee_line: int

    kind: CppEdgeKind
    is_from_macro: bool = False
    macro_name: str = ""  # Empty string instead of None to match C++ binding

    @field_validator("kind", mode="before")
    @classmethod
    def convert_kind(cls, v):
        """Convert C++ enum to string"""
        if hasattr(v, "name"):
            # Convert enum name to kebab-case
            name = v.name
            # Handle special cases
            if name == "Direct":
                return "direct"
            elif name == "Virtual":
                return "virtual"
            elif name == "FunctionPointer":
                return "function-pointer"
            elif name == "ObjectCreation":
                return "object-creation"
            elif name == "OperatorCall":
                return "operator-call"
            elif name == "ObjectDestruction":
                return "object-destruction"
            elif name == "VirtualOverride":
                return "virtual-override"
            elif name == "StdFunctionCall":
                return "std-function-call"
            return name.lower()
        return v


# -------------------------
# Root
# -------------------------


class CppApplication(PybindBaseModel):
    """Complete C++ application model"""

    project_root: str
    translation_units: List[CppTranslationUnit] = Field(default_factory=list)
    call_graph_edges: List[CppCallGraphEdge] = Field(default_factory=list)
    file_to_tu_index: dict[str, int] = Field(default_factory=dict)


# ------------------------
# Helpers
# ------------------------


class VariableFilter(BaseModel):
    file_name: Optional[str] = None
    name: Optional[str] = None
    usr: Optional[str] = None

    is_global: Optional[bool] = None
    is_const: Optional[bool] = None
    is_static: Optional[bool] = None
    is_constexpr: Optional[bool] = None

    type: Optional[str] = None  # substring match
