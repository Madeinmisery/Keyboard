// Copyright (C) 2018 The Android Open Source Project
//
// Licensed under the Apache License, Version 2.0 (the "License");
// you may not use this file except in compliance with the License.
// You may obtain a copy of the License at
//
//      http://www.apache.org/licenses/LICENSE-2.0
//
// Unless required by applicable law or agreed to in writing, software
// distributed under the License is distributed on an "AS IS" BASIS,
// WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
// See the License for the specific language governing permissions and
// limitations under the License.

#include <ir_representation_json.h>

#include <json/reader.h>
#include <json/writer.h>
#include <llvm/Support/raw_ostream.h>

#include <fstream>
#include <string>

namespace abi_util {

void IRToJsonConverter::AddTemplateInfo(
    JsonObject &type_decl, const abi_util::TemplatedArtifactIR *template_ir) {
  Json::Value &elements = type_decl["template_info"];
  elements = JsonArray();
  for (auto &&template_element_ir : template_ir->GetTemplateElements()) {
    Json::Value &element = elements.append(JsonObject());
    element["referenced_type"] = template_element_ir.GetReferencedType();
  }
}

void IRToJsonConverter::AddTypeInfo(JsonObject &type_decl,
                                    const TypeIR *type_ir) {
  Json::Value &type_info = type_decl["type_info"];
  type_info = JsonObject();
  type_info["linker_set_key"] = type_ir->GetLinkerSetKey();
  type_info["source_file"] = type_ir->GetSourceFile();
  type_info["name"] = type_ir->GetName();
  type_info["size"] = Json::UInt64(type_ir->GetSize());
  type_info["alignment"] = type_ir->GetAlignment();
  type_info["referenced_type"] = type_ir->GetReferencedType();
  type_info["self_type"] = type_ir->GetSelfType();
}

static JsonObject ConvertRecordFieldIR(const RecordFieldIR *record_field_ir) {
  JsonObject record_field;
  record_field["field_name"] = record_field_ir->GetName();
  record_field["referenced_type"] = record_field_ir->GetReferencedType();
  record_field["access"] = AccessIRToJson(record_field_ir->GetAccess());
  record_field["field_offset"] = Json::UInt64(record_field_ir->GetOffset());
  return record_field;
}

void IRToJsonConverter::AddRecordFields(JsonObject &record_type,
                                        const RecordTypeIR *record_ir) {
  Json::Value &fields = record_type["fields"];
  fields = JsonArray();
  for (auto &&field_ir : record_ir->GetFields()) {
    fields.append(ConvertRecordFieldIR(&field_ir));
  }
}

static JsonObject
ConvertBaseSpecifierIR(const CXXBaseSpecifierIR &base_specifier_ir) {
  JsonObject base_specifier;
  base_specifier["referenced_type"] = base_specifier_ir.GetReferencedType();
  base_specifier["is_virtual"] = base_specifier_ir.IsVirtual();
  base_specifier["access"] = AccessIRToJson(base_specifier_ir.GetAccess());
  return base_specifier;
}

void IRToJsonConverter::AddBaseSpecifiers(JsonObject &record_type,
                                          const RecordTypeIR *record_ir) {
  Json::Value &base_specifiers = record_type["base_specifiers"];
  base_specifiers = JsonArray();
  for (auto &&base_ir : record_ir->GetBases()) {
    base_specifiers.append(ConvertBaseSpecifierIR(base_ir));
  }
}

static JsonObject
ConvertVTableLayoutIR(const VTableLayoutIR &vtable_layout_ir) {
  JsonObject vtable_layout;
  Json::Value &vtable_components = vtable_layout["vtable_components"];
  vtable_components = JsonArray();
  for (auto &&vtable_component_ir : vtable_layout_ir.GetVTableComponents()) {
    Json::Value &vtable_component = vtable_components.append(JsonObject());
    vtable_component["kind"] =
        VTableComponentKindIRToJson(vtable_component_ir.GetKind());
    vtable_component["component_value"] =
        Json::Int64(vtable_component_ir.GetValue());
    vtable_component["mangled_component_name"] = vtable_component_ir.GetName();
    vtable_component["is_pure"] = vtable_component_ir.GetIsPure();
  }
  return vtable_layout;
}

void IRToJsonConverter::AddVTableLayout(JsonObject &record_type,
                                        const RecordTypeIR *record_ir) {
  const VTableLayoutIR &vtable_layout_ir = record_ir->GetVTableLayout();
  record_type["vtable_layout"] = ConvertVTableLayoutIR(vtable_layout_ir);
}

void IRToJsonConverter::AddTagTypeInfo(JsonObject &record_type,
                                       const abi_util::TagTypeIR *tag_type_ir) {
  Json::Value &tag_type = record_type["tag_info"];
  tag_type = JsonObject();
  tag_type["unique_id"] = tag_type_ir->GetUniqueId();
}

JsonObject IRToJsonConverter::ConvertRecordTypeIR(const RecordTypeIR *recordp) {
  JsonObject record_type;

  record_type["access"] = AccessIRToJson(recordp->GetAccess());
  record_type["record_kind"] = RecordKindIRToJson(recordp->GetRecordKind());
  record_type["is_anonymous"] = recordp->IsAnonymous();
  AddTypeInfo(record_type, recordp);
  AddRecordFields(record_type, recordp);
  AddBaseSpecifiers(record_type, recordp);
  AddVTableLayout(record_type, recordp);
  AddTagTypeInfo(record_type, recordp);
  AddTemplateInfo(record_type, recordp);
  return record_type;
}

JsonObject
IRToJsonConverter::ConvertElfObjectIR(const ElfObjectIR *elf_object_ir) {
  JsonObject elf_object;
  elf_object["name"] = elf_object_ir->GetName();
  return elf_object;
}

JsonObject
IRToJsonConverter::ConvertElfFunctionIR(const ElfFunctionIR *elf_function_ir) {
  JsonObject elf_function;
  elf_function["name"] = elf_function_ir->GetName();
  return elf_function;
}

void IRToJsonConverter::AddFunctionParametersAndSetReturnType(
    JsonObject &function, const CFunctionLikeIR *cfunction_like_ir) {
  function["return_type"] = cfunction_like_ir->GetReturnType();
  AddFunctionParameters(function, cfunction_like_ir);
}

void IRToJsonConverter::AddFunctionParameters(
    JsonObject &function, const CFunctionLikeIR *cfunction_like_ir) {
  Json::Value &parameters = function["parameters"];
  parameters = JsonArray();
  for (auto &&parameter_ir : cfunction_like_ir->GetParameters()) {
    Json::Value &parameter = parameters.append(JsonObject());
    parameter["referenced_type"] = parameter_ir.GetReferencedType();
    parameter["default_arg"] = parameter_ir.GetIsDefault();
    parameter["is_this_ptr"] = parameter_ir.GetIsThisPtr();
  }
}

JsonObject
IRToJsonConverter::ConvertFunctionTypeIR(const FunctionTypeIR *function_typep) {
  JsonObject function_type;
  AddTypeInfo(function_type, function_typep);
  AddFunctionParametersAndSetReturnType(function_type, function_typep);
  return function_type;
}

JsonObject IRToJsonConverter::ConvertFunctionIR(const FunctionIR *functionp) {
  JsonObject function;
  function["access"] = AccessIRToJson(functionp->GetAccess());
  function["linker_set_key"] = functionp->GetLinkerSetKey();
  function["source_file"] = functionp->GetSourceFile();
  function["function_name"] = functionp->GetName();
  AddFunctionParametersAndSetReturnType(function, functionp);
  AddTemplateInfo(function, functionp);
  return function;
}

static JsonObject ConvertEnumFieldIR(const EnumFieldIR *enum_field_ir) {
  JsonObject enum_field;
  enum_field["name"] = enum_field_ir->GetName();
  enum_field["enum_field_value"] = Json::Int64(enum_field_ir->GetValue());
  return enum_field;
}

void IRToJsonConverter::AddEnumFields(JsonObject &enum_type,
                                      const EnumTypeIR *enum_ir) {
  Json::Value &enum_fields = enum_type["enum_fields"];
  enum_fields = JsonArray();
  for (auto &&field : enum_ir->GetFields()) {
    enum_fields.append(ConvertEnumFieldIR(&field));
  }
}

JsonObject IRToJsonConverter::ConvertEnumTypeIR(const EnumTypeIR *enump) {
  JsonObject enum_type;
  enum_type["access"] = AccessIRToJson(enump->GetAccess());
  enum_type["underlying_type"] = enump->GetUnderlyingType();
  AddTypeInfo(enum_type, enump);
  AddEnumFields(enum_type, enump);
  AddTagTypeInfo(enum_type, enump);
  return enum_type;
}

JsonObject
IRToJsonConverter::ConvertGlobalVarIR(const GlobalVarIR *global_varp) {
  JsonObject global_var;
  global_var["referenced_type"] = global_varp->GetReferencedType();
  global_var["source_file"] = global_varp->GetSourceFile();
  global_var["name"] = global_varp->GetName();
  global_var["linker_set_key"] = global_varp->GetLinkerSetKey();
  global_var["access"] = AccessIRToJson(global_varp->GetAccess());
  return global_var;
}

JsonObject
IRToJsonConverter::ConvertPointerTypeIR(const PointerTypeIR *pointerp) {
  JsonObject pointer_type;
  AddTypeInfo(pointer_type, pointerp);
  return pointer_type;
}

JsonObject
IRToJsonConverter::ConvertQualifiedTypeIR(const QualifiedTypeIR *qualtypep) {
  JsonObject qualified_type;
  AddTypeInfo(qualified_type, qualtypep);
  qualified_type["is_const"] = qualtypep->IsConst();
  qualified_type["is_volatile"] = qualtypep->IsVolatile();
  qualified_type["is_restricted"] = qualtypep->IsRestricted();
  return qualified_type;
}

JsonObject
IRToJsonConverter::ConvertBuiltinTypeIR(const BuiltinTypeIR *builtin_typep) {
  JsonObject builtin_type;
  builtin_type["is_unsigned"] = builtin_typep->IsUnsigned();
  builtin_type["is_integral"] = builtin_typep->IsIntegralType();
  AddTypeInfo(builtin_type, builtin_typep);
  return builtin_type;
}

JsonObject
IRToJsonConverter::ConvertArrayTypeIR(const ArrayTypeIR *array_typep) {
  JsonObject array_type;
  AddTypeInfo(array_type, array_typep);
  return array_type;
}

JsonObject IRToJsonConverter::ConvertLvalueReferenceTypeIR(
    const LvalueReferenceTypeIR *lvalue_reference_typep) {
  JsonObject lvalue_reference_type;
  AddTypeInfo(lvalue_reference_type, lvalue_reference_typep);
  return lvalue_reference_type;
}

JsonObject IRToJsonConverter::ConvertRvalueReferenceTypeIR(
    const RvalueReferenceTypeIR *rvalue_reference_typep) {
  JsonObject rvalue_reference_type;
  AddTypeInfo(rvalue_reference_type, rvalue_reference_typep);
  return rvalue_reference_type;
}

bool JsonIRDumper::AddLinkableMessageIR(const LinkableMessageIR *lm) {
  std::string key;
  JsonObject converted;
  // No RTTI
  switch (lm->GetKind()) {
  case RecordTypeKind:
    key = "record_types";
    converted = ConvertRecordTypeIR(static_cast<const RecordTypeIR *>(lm));
    break;
  case EnumTypeKind:
    key = "enum_types";
    converted = ConvertEnumTypeIR(static_cast<const EnumTypeIR *>(lm));
    break;
  case PointerTypeKind:
    key = "pointer_types";
    converted = ConvertPointerTypeIR(static_cast<const PointerTypeIR *>(lm));
    break;
  case QualifiedTypeKind:
    key = "qualified_types";
    converted =
        ConvertQualifiedTypeIR(static_cast<const QualifiedTypeIR *>(lm));
    break;
  case ArrayTypeKind:
    key = "array_types";
    converted = ConvertArrayTypeIR(static_cast<const ArrayTypeIR *>(lm));
    break;
  case LvalueReferenceTypeKind:
    key = "lvalue_reference_types";
    converted = ConvertLvalueReferenceTypeIR(
        static_cast<const LvalueReferenceTypeIR *>(lm));
    break;
  case RvalueReferenceTypeKind:
    key = "rvalue_reference_types";
    converted = ConvertRvalueReferenceTypeIR(
        static_cast<const RvalueReferenceTypeIR *>(lm));
    break;
  case BuiltinTypeKind:
    key = "builtin_types";
    converted = ConvertBuiltinTypeIR(static_cast<const BuiltinTypeIR *>(lm));
    break;
  case FunctionTypeKind:
    key = "function_types";
    converted = ConvertFunctionTypeIR(static_cast<const FunctionTypeIR *>(lm));
    break;
  case GlobalVarKind:
    key = "global_vars";
    converted = ConvertGlobalVarIR(static_cast<const GlobalVarIR *>(lm));
    break;
  case FunctionKind:
    key = "functions";
    converted = ConvertFunctionIR(static_cast<const FunctionIR *>(lm));
    break;
  default:
    return false;
  }
  translation_unit_[key].append(converted);
  return true;
}

bool JsonIRDumper::AddElfSymbolMessageIR(const ElfSymbolIR *em) {
  std::string key;
  JsonObject elf_symbol;
  elf_symbol["name"] = em->GetName();
  switch (em->GetKind()) {
  case ElfSymbolIR::ElfFunctionKind:
    key = "elf_functions";
    break;
  case ElfSymbolIR::ElfObjectKind:
    key = "elf_objects";
    break;
  default:
    return false;
  }
  translation_unit_[key].append(elf_symbol);
  return true;
}

bool JsonIRDumper::Dump() {
  std::ofstream output(dump_path_);
  Json::StyledStreamWriter writer(/* indentation */ " ");
  writer.write(output, translation_unit_);
  return true;
}

JsonIRDumper::JsonIRDumper(const std::string &dump_path)
    : IRDumper(dump_path), translation_unit_() {
  const std::string keys[] = {
    "record_types",
    "enum_types",
    "pointer_types",
    "lvalue_reference_types",
    "rvalue_reference_types",
    "builtin_types",
    "qualified_types",
    "array_types",
    "function_types",
    "functions",
    "global_vars",
    "elf_functions",
    "elf_objects",
  };
  for (auto key : keys) {
    translation_unit_[key] = JsonArray();
  }
}

static const JsonObject json_empty_object;
static const JsonArray json_empty_array;
static const Json::Value json_0(0);
static const Json::Value json_false(false);
static const Json::Value json_empty_string("");

JsonObjectRef::JsonObjectRef(const Json::Value &json_value, bool &ok)
    : object_(json_value.isObject() ? json_value : json_empty_object), ok_(ok) {
  if (!json_value.isObject()) {
    ok_ = false;
  }
}

const Json::Value &JsonObjectRef::Get(const std::string &key,
                                      const Json::Value &default_value,
                                      bool (Json::Value::*is_expected_type)()
                                          const) const {
  if (!object_.isMember(key)) {
    return default_value;
  }
  const Json::Value &value = object_[key];
  if (!(value.*is_expected_type)()) {
    ok_ = false;
    return default_value;
  }
  return value;
}

bool JsonObjectRef::GetBool(const std::string key) const {
  return Get(key, json_false, &Json::Value::isBool).asBool();
}

int64_t JsonObjectRef::GetInt(const std::string &key) const {
  return Get(key, json_0, &Json::Value::isIntegral).asInt64();
}

uint64_t JsonObjectRef::GetUint(const std::string &key) const {
  return Get(key, json_0, &Json::Value::isIntegral).asUInt64();
}

std::string JsonObjectRef::GetString(const std::string &key) const {
  return Get(key, json_empty_string, &Json::Value::isString).asString();
}

JsonObjectRef JsonObjectRef::GetObject(const std::string &key) const {
  return JsonObjectRef(Get(key, json_empty_object, &Json::Value::isObject),
                       ok_);
}

JsonArrayRef<JsonObjectRef>
JsonObjectRef::GetObjects(const std::string &key) const {
  return JsonArrayRef<JsonObjectRef>(
      Get(key, json_empty_array, &Json::Value::isArray), ok_);
}

template <>
JsonObjectRef JsonArrayRef<JsonObjectRef>::Iterator::operator*() const {
  return JsonObjectRef(array_[index_], ok_);
}

bool JsonToIRReader::ReadDump(const std::string &dump_file) {
  Json::Value tu_json;
  Json::Reader reader;
  std::ifstream input(dump_file);

  if (reader.parse(input, tu_json, /* collectComments */ false)) {
    llvm::errs() << "Failed to parse JSON file\n";
    return false;
  }
  bool ok = true;
  JsonObjectRef tu(tu_json, ok);
  if (!ok) {
    llvm::errs() << "Translation unit is not an object\n";
    return false;
  }

  ReadFunctions(tu);
  ReadGlobalVariables(tu);
  ReadEnumTypes(tu);
  ReadRecordTypes(tu);
  ReadFunctionTypes(tu);
  ReadArrayTypes(tu);
  ReadPointerTypes(tu);
  ReadQualifiedTypes(tu);
  ReadBuiltinTypes(tu);
  ReadLvalueReferenceTypes(tu);
  ReadRvalueReferenceTypes(tu);
  ReadElfFunctions(tu);
  ReadElfObjects(tu);
  if (!ok) {
    llvm::errs() << "Failed to convert JSON to IR\n";
    return false;
  }
  return true;
}

void JsonToIRReader::ReadTypeInfo(const JsonObjectRef &type_decl,
                                  TypeIR *type_ir) {
  const JsonObjectRef type_info = type_decl.GetObject("type_info");
  type_ir->SetLinkerSetKey(type_info.GetString("linker_set_key"));
  type_ir->SetSourceFile(type_info.GetString("source_file"));
  type_ir->SetName(type_info.GetString("name"));
  type_ir->SetReferencedType(type_info.GetString("referenced_type"));
  type_ir->SetSelfType(type_info.GetString("self_type"));
  type_ir->SetSize(type_info.GetUint("size"));
  type_ir->SetAlignment(type_info.GetUint("alignment"));
}

void JsonToIRReader::ReadTagTypeInfo(const JsonObjectRef &tag_type,
                                     TagTypeIR *tag_type_ir) {
  tag_type_ir->SetUniqueId(
      tag_type.GetObject("tag_info").GetString("unique_id"));
}

void JsonToIRReader::ReadFunctionParametersAndReturnType(
    const JsonObjectRef &function, CFunctionLikeIR *function_ir) {
  function_ir->SetReturnType(function.GetString("return_type"));
  for (auto &&parameter : function.GetObjects("parameters")) {
    ParamIR param_ir(parameter.GetString("referenced_type"),
                     parameter.GetBool("default_arg"),
                     parameter.GetBool("is_this_ptr"));
    function_ir->AddParameter(std::move(param_ir));
  }
}

TemplateInfoIR
JsonToIRReader::TemplateInfoJsonToIR(const JsonObjectRef &template_info) {
  TemplateInfoIR template_info_ir;
  for (auto &&element : template_info.GetObjects("template_info")) {
    TemplateElementIR template_element_ir(element.GetString("referenced_type"));
    template_info_ir.AddTemplateElement(std::move(template_element_ir));
  }
  return template_info_ir;
}

FunctionIR JsonToIRReader::FunctionJsonToIR(const JsonObjectRef &function) {
  FunctionIR function_ir;
  function_ir.SetLinkerSetKey(function.GetString("linker_set_key"));
  function_ir.SetName(function.GetString("function_name"));
  function_ir.SetAccess(AccessJsonToIR(function.GetInt("access")));
  function_ir.SetSourceFile(function.GetString("source_file"));
  ReadFunctionParametersAndReturnType(function, &function_ir);
  function_ir.SetTemplateInfo(TemplateInfoJsonToIR(function));
  return function_ir;
}

FunctionTypeIR
JsonToIRReader::FunctionTypeJsonToIR(const JsonObjectRef &function_type) {
  FunctionTypeIR function_type_ir;
  ReadTypeInfo(function_type, &function_type_ir);
  ReadFunctionParametersAndReturnType(function_type, &function_type_ir);
  return function_type_ir;
}

VTableLayoutIR
JsonToIRReader::VTableLayoutJsonToIR(const JsonObjectRef &vtable_layout) {
  VTableLayoutIR vtable_layout_ir;
  for (auto &&vtable_component :
       vtable_layout.GetObjects("vtable_components")) {
    VTableComponentIR vtable_component_ir(
        vtable_component.GetString("mangled_component_name"),
        VTableComponentKindJsonToIR(vtable_component.GetInt("kind")),
        vtable_component.GetInt("component_value"),
        vtable_component.GetBool("is_pure"));
    vtable_layout_ir.AddVTableComponent(std::move(vtable_component_ir));
  }
  return vtable_layout_ir;
}

std::vector<RecordFieldIR> JsonToIRReader::RecordFieldsJsonToIR(
    const JsonArrayRef<JsonObjectRef> &fields) {
  std::vector<RecordFieldIR> record_type_fields_ir;
  for (auto &&field : fields) {
    RecordFieldIR record_field_ir(
        field.GetString("field_name"), field.GetString("referenced_type"),
        field.GetUint("field_offset"), AccessJsonToIR(field.GetInt("access")));
    record_type_fields_ir.emplace_back(std::move(record_field_ir));
  }
  return record_type_fields_ir;
}

std::vector<CXXBaseSpecifierIR> JsonToIRReader::BaseSpecifiersJsonToIR(
    const JsonArrayRef<JsonObjectRef> &base_specifiers) {
  std::vector<CXXBaseSpecifierIR> record_type_bases_ir;
  for (auto &&base_specifier : base_specifiers) {
    CXXBaseSpecifierIR record_base_ir(
        base_specifier.GetString("referenced_type"),
        base_specifier.GetBool("is_virtual"),
        AccessJsonToIR(base_specifier.GetInt("access")));
    record_type_bases_ir.emplace_back(std::move(record_base_ir));
  }
  return record_type_bases_ir;
}

RecordTypeIR
JsonToIRReader::RecordTypeJsonToIR(const JsonObjectRef &record_type) {
  RecordTypeIR record_type_ir;
  ReadTypeInfo(record_type, &record_type_ir);
  record_type_ir.SetTemplateInfo(TemplateInfoJsonToIR(record_type));
  record_type_ir.SetAccess(AccessJsonToIR(record_type.GetInt("access")));
  record_type_ir.SetVTableLayout(
      VTableLayoutJsonToIR(record_type.GetObject("vtable_layout")));
  record_type_ir.SetRecordFields(
      RecordFieldsJsonToIR(record_type.GetObjects("fields")));
  record_type_ir.SetCXXBaseSpecifiers(
      BaseSpecifiersJsonToIR(record_type.GetObjects("base_specifiers")));
  record_type_ir.SetRecordKind(
      RecordKindJsonToIR(record_type.GetInt("record_kind")));
  record_type_ir.SetAnonymity(record_type.GetBool("is_anonymous"));
  ReadTagTypeInfo(record_type, &record_type_ir);
  return record_type_ir;
}

std::vector<EnumFieldIR> JsonToIRReader::EnumFieldsJsonToIR(
    const JsonArrayRef<JsonObjectRef> &enum_fields) {
  std::vector<EnumFieldIR> enum_fields_ir;
  for (auto &&field : enum_fields) {
    EnumFieldIR enum_field_ir(field.GetString("name"),
                              field.GetInt("enum_field_value"));
    enum_fields_ir.emplace_back(std::move(enum_field_ir));
  }
  return enum_fields_ir;
}

EnumTypeIR JsonToIRReader::EnumTypeJsonToIR(const JsonObjectRef &enum_type) {
  EnumTypeIR enum_type_ir;
  ReadTypeInfo(enum_type, &enum_type_ir);
  enum_type_ir.SetUnderlyingType(enum_type.GetString("underlying_type"));
  enum_type_ir.SetAccess(AccessJsonToIR(enum_type.GetInt("access")));
  enum_type_ir.SetFields(
      EnumFieldsJsonToIR(enum_type.GetObjects("enum_fields")));
  ReadTagTypeInfo(enum_type, &enum_type_ir);
  return enum_type_ir;
}

void JsonToIRReader::ReadGlobalVariables(const JsonObjectRef &tu) {
  for (auto &&global_variable : tu.GetObjects("global_vars")) {
    GlobalVarIR global_variable_ir;
    global_variable_ir.SetName(global_variable.GetString("name"));
    global_variable_ir.SetAccess(
        AccessJsonToIR(global_variable.GetInt("access")));
    global_variable_ir.SetSourceFile(global_variable.GetString("source_file"));
    global_variable_ir.SetReferencedType(
        global_variable.GetString("referenced_type"));
    global_variable_ir.SetLinkerSetKey(
        global_variable.GetString("linker_set_key"));
    if (!IsLinkableMessageInExportedHeaders(&global_variable_ir)) {
      continue;
    }
    global_variables_.insert(
        {global_variable_ir.GetLinkerSetKey(), std::move(global_variable_ir)});
  }
}

void JsonToIRReader::ReadPointerTypes(const JsonObjectRef &tu) {
  for (auto &&pointer_type : tu.GetObjects("pointer_types")) {
    PointerTypeIR pointer_type_ir;
    ReadTypeInfo(pointer_type, &pointer_type_ir);
    if (!IsLinkableMessageInExportedHeaders(&pointer_type_ir)) {
      continue;
    }
    AddToMapAndTypeGraph(std::move(pointer_type_ir), &pointer_types_,
                         &type_graph_);
  }
}

void JsonToIRReader::ReadBuiltinTypes(const JsonObjectRef &tu) {
  for (auto &&builtin_type : tu.GetObjects("builtin_types")) {
    BuiltinTypeIR builtin_type_ir;
    ReadTypeInfo(builtin_type, &builtin_type_ir);
    builtin_type_ir.SetSignedness(builtin_type.GetBool("is_unsigned"));
    builtin_type_ir.SetIntegralType(builtin_type.GetBool("is_integral"));
    AddToMapAndTypeGraph(std::move(builtin_type_ir), &builtin_types_,
                         &type_graph_);
  }
}

void JsonToIRReader::ReadQualifiedTypes(const JsonObjectRef &tu) {
  for (auto &&qualified_type : tu.GetObjects("qualified_types")) {
    QualifiedTypeIR qualified_type_ir;
    ReadTypeInfo(qualified_type, &qualified_type_ir);
    qualified_type_ir.SetConstness(qualified_type.GetBool("is_const"));
    qualified_type_ir.SetVolatility(qualified_type.GetBool("is_volatile"));
    qualified_type_ir.SetRestrictedness(
        qualified_type.GetBool("is_restricted"));
    if (!IsLinkableMessageInExportedHeaders(&qualified_type_ir)) {
      continue;
    }
    AddToMapAndTypeGraph(std::move(qualified_type_ir), &qualified_types_,
                         &type_graph_);
  }
}

void JsonToIRReader::ReadArrayTypes(const JsonObjectRef &tu) {
  for (auto &&array_type : tu.GetObjects("array_types")) {
    ArrayTypeIR array_type_ir;
    ReadTypeInfo(array_type, &array_type_ir);
    if (!IsLinkableMessageInExportedHeaders(&array_type_ir)) {
      continue;
    }
    AddToMapAndTypeGraph(std::move(array_type_ir), &array_types_, &type_graph_);
  }
}

void JsonToIRReader::ReadLvalueReferenceTypes(const JsonObjectRef &tu) {
  for (auto &&lvalue_reference_type : tu.GetObjects("lvalue_reference_types")) {
    LvalueReferenceTypeIR lvalue_reference_type_ir;
    ReadTypeInfo(lvalue_reference_type, &lvalue_reference_type_ir);
    if (!IsLinkableMessageInExportedHeaders(&lvalue_reference_type_ir)) {
      continue;
    }
    AddToMapAndTypeGraph(std::move(lvalue_reference_type_ir),
                         &lvalue_reference_types_, &type_graph_);
  }
}

void JsonToIRReader::ReadRvalueReferenceTypes(const JsonObjectRef &tu) {
  for (auto &&rvalue_reference_type : tu.GetObjects("rvalue_reference_types")) {
    RvalueReferenceTypeIR rvalue_reference_type_ir;
    ReadTypeInfo(rvalue_reference_type, &rvalue_reference_type_ir);
    if (!IsLinkableMessageInExportedHeaders(&rvalue_reference_type_ir)) {
      continue;
    }
    AddToMapAndTypeGraph(std::move(rvalue_reference_type_ir),
                         &rvalue_reference_types_, &type_graph_);
  }
}

void JsonToIRReader::ReadFunctions(const JsonObjectRef &tu) {
  for (auto &&function : tu.GetObjects("functions")) {
    FunctionIR function_ir = FunctionJsonToIR(function);
    if (!IsLinkableMessageInExportedHeaders(&function_ir)) {
      continue;
    }
    functions_.insert({function_ir.GetLinkerSetKey(), std::move(function_ir)});
  }
}

void JsonToIRReader::ReadRecordTypes(const JsonObjectRef &tu) {
  for (auto &&record_type : tu.GetObjects("record_types")) {
    RecordTypeIR record_type_ir = RecordTypeJsonToIR(record_type);
    if (!IsLinkableMessageInExportedHeaders(&record_type_ir)) {
      continue;
    }
    auto it = AddToMapAndTypeGraph(std::move(record_type_ir), &record_types_,
                                   &type_graph_);
    const std::string &key = GetODRListMapKey(&(it->second));
    AddToODRListMap(key, &(it->second));
  }
}

void JsonToIRReader::ReadFunctionTypes(const JsonObjectRef &tu) {
  for (auto &&function_type : tu.GetObjects("function_types")) {
    FunctionTypeIR function_type_ir = FunctionTypeJsonToIR(function_type);
    if (!IsLinkableMessageInExportedHeaders(&function_type_ir)) {
      continue;
    }
    auto it = AddToMapAndTypeGraph(std::move(function_type_ir),
                                   &function_types_, &type_graph_);
    const std::string &key = GetODRListMapKey(&(it->second));
    AddToODRListMap(key, &(it->second));
  }
}

void JsonToIRReader::ReadEnumTypes(const JsonObjectRef &tu) {
  for (auto &&enum_type : tu.GetObjects("enum_types")) {
    EnumTypeIR enum_type_ir = EnumTypeJsonToIR(enum_type);
    if (!IsLinkableMessageInExportedHeaders(&enum_type_ir)) {
      continue;
    }
    auto it = AddToMapAndTypeGraph(std::move(enum_type_ir), &enum_types_,
                                   &type_graph_);
    AddToODRListMap(it->second.GetUniqueId() + it->second.GetSourceFile(),
                    (&it->second));
  }
}

void JsonToIRReader::ReadElfFunctions(const JsonObjectRef &tu) {
  for (auto &&elf_function : tu.GetObjects("elf_functions")) {
    ElfFunctionIR elf_function_ir(elf_function.GetString("name"));
    elf_functions_.insert(
        {elf_function_ir.GetName(), std::move(elf_function_ir)});
  }
}

void JsonToIRReader::ReadElfObjects(const JsonObjectRef &tu) {
  for (auto &&elf_object : tu.GetObjects("elf_objects")) {
    ElfObjectIR elf_object_ir(elf_object.GetString("name"));
    elf_objects_.insert({elf_object_ir.GetName(), std::move(elf_object_ir)});
  }
}
} // namespace abi_util
