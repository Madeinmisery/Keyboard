// Copyright (C) 2016 The Android Open Source Project
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

#include "abi_diff.h"

#include <header_abi_util.h>

#include <llvm/Support/raw_ostream.h>

#include <memory>
#include <string>
#include <vector>

#include <stdlib.h>

abi_util::CompatibilityStatusIR HeaderAbiDiff::GenerateCompatibilityReport() {
  using abi_util::TextFormatToIRReader;
  std::unique_ptr<abi_util::TextFormatToIRReader> old_reader =
      TextFormatToIRReader::CreateTextFormatToIRReader(text_format_old_,
                                                       {old_dump_});
  std::unique_ptr<abi_util::TextFormatToIRReader> new_reader =
      TextFormatToIRReader::CreateTextFormatToIRReader(text_format_new_,
                                                       {new_dump_});
  if (!old_reader || !new_reader || !old_reader->ReadDump() ||
      !new_reader->ReadDump()) {
    llvm::errs() << "Could not create Text Format readers\n";
    ::exit(1);
  }
  std::unique_ptr<abi_util::IRDiffDumper> ir_diff_dumper =
      abi_util::IRDiffDumper::CreateIRDiffDumper(text_format_diff_, cr_);
  abi_util::CompatibilityStatusIR status =
      CompareTUs(old_reader.get(), new_reader.get(), ir_diff_dumper.get());
  if (!ir_diff_dumper->Dump()) {
    llvm::errs() << "Could not dump diff report\n";
    ::exit(1);
  }
  return status;
}

template <typename KeyGetter, typename ValueGetter>
static void AddTypesToMap(AbiElementMap<const abi_util::TypeIR *> *dst,
                          const abi_util::TextFormatToIRReader *tu,
                          KeyGetter get_key, ValueGetter get_value) {
  AddToMap(dst, tu->GetRecordTypes(), get_key, get_value);
  AddToMap(dst, tu->GetEnumTypes(), get_key, get_value);
  AddToMap(dst, tu->GetPointerTypes(), get_key, get_value);
  AddToMap(dst, tu->GetBuiltinTypes(), get_key, get_value);
  AddToMap(dst, tu->GetArrayTypes(), get_key, get_value);
  AddToMap(dst, tu->GetLvalueReferenceTypes(), get_key, get_value);
  AddToMap(dst, tu->GetRvalueReferenceTypes(), get_key, get_value);
  AddToMap(dst, tu->GetQualifiedTypes(), get_key, get_value);
}

abi_util::CompatibilityStatusIR HeaderAbiDiff::CompareTUs(
    const abi_util::TextFormatToIRReader *old_tu,
    const abi_util::TextFormatToIRReader *new_tu,
    abi_util::IRDiffDumper *ir_diff_dumper) {
  // Collect all old and new types in maps, so that we can refer to them by
  // type name / linker_set_key later.
  AbiElementMap<const abi_util::TypeIR *> old_types;
  AbiElementMap<const abi_util::TypeIR *> new_types;
  AddTypesToMap(&old_types, old_tu,
                [](auto e) {return e->first;},
                [](auto e) {return &(e->second);});
  AddTypesToMap(&new_types, new_tu,
                [](auto e) {return e->first;},
                [](auto e) {return &(e->second);});

  // Collect fills in added, removed ,unsafe and safe function diffs.
  if (!CollectDynsymExportables(old_tu->GetFunctions(), new_tu->GetFunctions(),
                                old_tu->GetElfFunctions(),
                                new_tu->GetElfFunctions(),
                                old_types, new_types,
                                ir_diff_dumper) ||
      !CollectDynsymExportables(old_tu->GetGlobalVariables(),
                                new_tu->GetGlobalVariables(),
                                old_tu->GetElfObjects(),
                                new_tu->GetElfObjects(),
                                old_types, new_types,
                                ir_diff_dumper)) {
    llvm::errs() << "Unable to collect dynsym exportables\n";
    ::exit(1);
  }

  // By the time this call is reached, all referenced types have been diffed.
  // So all additional calls on ir_diff_dumper get DiffKind::Unreferenced.
  if (check_all_apis_ && !CollectUserDefinedTypes(old_tu, new_tu, old_types,
                                                  new_types, ir_diff_dumper)) {
    llvm::errs() << "Unable to collect user defined types\n";
    ::exit(1);
  }

  abi_util::CompatibilityStatusIR combined_status =
      ir_diff_dumper->GetCompatibilityStatusIR();

  ir_diff_dumper->AddLibNameIR(lib_name_);
  ir_diff_dumper->AddArchIR(arch_);
  ir_diff_dumper->AddCompatibilityStatusIR(combined_status);
  return combined_status;
}

bool HeaderAbiDiff::CollectUserDefinedTypes(
    const abi_util::TextFormatToIRReader *old_tu,
    const abi_util::TextFormatToIRReader *new_tu,
    const AbiElementMap<const abi_util::TypeIR *> &old_types_map,
    const AbiElementMap<const abi_util::TypeIR *> &new_types_map,
    abi_util::IRDiffDumper *ir_diff_dumper) {
  return CollectUserDefinedTypesInternal(
      old_tu->GetRecordTypes(), new_tu->GetRecordTypes(), old_types_map,
      new_types_map, ir_diff_dumper) &&
      CollectUserDefinedTypesInternal(old_tu->GetEnumTypes(),
                                      new_tu->GetEnumTypes(), old_types_map,
                                      new_types_map, ir_diff_dumper);
}

template <typename T>
bool HeaderAbiDiff::CollectUserDefinedTypesInternal(
    const AbiElementMap<T> &old_ud_types,
    const AbiElementMap<T> &new_ud_types,
    const AbiElementMap<const abi_util::TypeIR *> &old_types_map,
    const AbiElementMap<const abi_util::TypeIR *> &new_types_map,
    abi_util::IRDiffDumper *ir_diff_dumper) {

  // No elf information for records and enums.
  AbiElementMap<const T *> old_ud_types_map;
  AbiElementMap<const T *> new_ud_types_map;

  abi_util::AddToMap(&old_ud_types_map, old_ud_types,
                     [](auto e) { return e->first;},
                     [](auto e) {return &(e->second);});

  abi_util::AddToMap(&new_ud_types_map, new_ud_types,
                     [](auto e) { return e->first;},
                     [](auto e) {return &(e->second);});

  return Collect(old_types_map, new_types_map, nullptr, nullptr,
                 ir_diff_dumper) &&
      PopulateCommonElements(old_ud_types_map, new_ud_types_map, old_types_map,
                             new_types_map, ir_diff_dumper,
                             abi_util::DiffMessageIR::Unreferenced);
}

template <typename T, typename ElfSymbolType>
bool HeaderAbiDiff::CollectDynsymExportables(
    const AbiElementMap<T> &old_exportables,
    const AbiElementMap<T> &new_exportables,
    const AbiElementMap<ElfSymbolType> &old_elf_symbols,
    const AbiElementMap<ElfSymbolType> &new_elf_symbols,
    const AbiElementMap<const abi_util::TypeIR *> &old_types_map,
    const AbiElementMap<const abi_util::TypeIR *> &new_types_map,
    abi_util::IRDiffDumper *ir_diff_dumper) {
  AbiElementMap<const T *> old_exportables_map;
  AbiElementMap<const T *> new_exportables_map;
  AbiElementMap<const abi_util::ElfSymbolIR *> old_elf_symbol_map;
  AbiElementMap<const abi_util::ElfSymbolIR *> new_elf_symbol_map;

  abi_util::AddToMap(&old_exportables_map, old_exportables,
                     [](auto e) { return e->first;},
                     [](auto e) {return &(e->second);});
  abi_util::AddToMap(&new_exportables_map, new_exportables,
                     [](auto e) { return e->first;},
                     [](auto e) { return &(e->second);});

  abi_util::AddToMap(
      &old_elf_symbol_map, old_elf_symbols,
      [](auto e) { return e->first;},
      [](auto e) {return &(e->second);});

  abi_util::AddToMap(
      &new_elf_symbol_map, new_elf_symbols,
      [](auto e) { return e->first;},
      [](auto e) {return &(e->second);});

  if (!Collect(old_exportables_map,
               new_exportables_map, &old_elf_symbol_map, &new_elf_symbol_map,
               ir_diff_dumper) ||
      !CollectElfSymbols(old_elf_symbol_map, new_elf_symbol_map,
                         ir_diff_dumper) ||
      !PopulateCommonElements(old_exportables_map, new_exportables_map,
                              old_types_map, new_types_map, ir_diff_dumper,
                              abi_util::DiffMessageIR::Referenced)) {
    llvm::errs() << "Diffing dynsym exportables failed\n";
    return false;
  }
  return true;
}

// Collect added and removed Elements. The elf set is needed since some symbols
// might not have meta-data about them collected through the AST. For eg: if a
// function Foo is defined in an assembly file on target A, but in a c/c++ file
// on target B, foo does not have meta-data surrounding it when building target
// A, this does not mean it is not in the ABI + API of the library.

template <typename T>
bool HeaderAbiDiff::Collect(
    const AbiElementMap<const T*> &old_elements_map,
    const AbiElementMap<const T*> &new_elements_map,
    const AbiElementMap<const abi_util::ElfSymbolIR *> *old_elf_map,
    const AbiElementMap<const abi_util::ElfSymbolIR *> *new_elf_map,
    abi_util::IRDiffDumper *ir_diff_dumper) {
  if (!PopulateRemovedElements(
      old_elements_map, new_elements_map, new_elf_map, ir_diff_dumper,
      abi_util::DiffMessageIR::Removed) ||
      !PopulateRemovedElements(new_elements_map, old_elements_map, old_elf_map,
                               ir_diff_dumper,
                               abi_util::IRDiffDumper::DiffKind::Added)) {
    llvm::errs() << "Populating functions in report failed\n";
    return false;
  }
  return true;
}

bool HeaderAbiDiff::CollectElfSymbols(
    const AbiElementMap<const abi_util::ElfSymbolIR *> &old_symbols,
    const AbiElementMap<const abi_util::ElfSymbolIR *> &new_symbols,
    abi_util::IRDiffDumper *ir_diff_dumper) {
  std::vector<const abi_util::ElfSymbolIR *> removed_elements =
      abi_util::FindRemovedElements(old_symbols, new_symbols);

  std::vector<const abi_util::ElfSymbolIR *> added_elements =
      abi_util::FindRemovedElements(new_symbols, old_symbols);

  return PopulateElfElements(removed_elements, ir_diff_dumper,
                             abi_util::IRDiffDumper::DiffKind::Removed) &&
         PopulateElfElements(added_elements, ir_diff_dumper,
                             abi_util::IRDiffDumper::DiffKind::Added);
}

bool HeaderAbiDiff::PopulateElfElements(
    std::vector<const abi_util::ElfSymbolIR *> &elf_elements,
    abi_util::IRDiffDumper *ir_diff_dumper,
    abi_util::IRDiffDumper::DiffKind diff_kind) {
  for (auto &&elf_element : elf_elements) {
    if (!ir_diff_dumper->AddElfSymbolMessageIR(elf_element, diff_kind)) {
      return false;
    }
  }
  return true;
}

template <typename T>
bool HeaderAbiDiff::PopulateRemovedElements(
    const AbiElementMap<const T*> &old_elements_map,
    const AbiElementMap<const T*> &new_elements_map,
    const AbiElementMap<const abi_util::ElfSymbolIR *> *elf_map,
    abi_util::IRDiffDumper *ir_diff_dumper,
    abi_util::IRDiffDumper::DiffKind diff_kind) {
  std::vector<const T *> removed_elements =
      abi_util::FindRemovedElements(old_elements_map, new_elements_map);
  if (!DumpLoneElements(removed_elements, elf_map, ir_diff_dumper, diff_kind)) {
    llvm::errs() << "Dumping added / removed element to report failed\n";
    return false;
  }
  return true;
}

// Find the common elements (common records, common enums, common functions etc)
// Dump the differences (we need type maps for this diff since we'll get
// reachable types from here)
template <typename T>
bool HeaderAbiDiff::PopulateCommonElements(
    const AbiElementMap<const T *> &old_elements_map,
    const AbiElementMap<const T *> &new_elements_map,
    const AbiElementMap<const abi_util::TypeIR *> &old_types,
    const AbiElementMap<const abi_util::TypeIR *> &new_types,
    abi_util::IRDiffDumper *ir_diff_dumper,
    abi_util::IRDiffDumper::DiffKind diff_kind) {
  std::vector<std::pair<const T *, const T *>> common_elements =
      abi_util::FindCommonElements(old_elements_map, new_elements_map);
  if (!DumpDiffElements(common_elements, old_types, new_types,
                        ir_diff_dumper, diff_kind)) {
    llvm::errs() << "Dumping difference in common element to report failed\n";
    return false;
  }
  return true;
}

template <typename T>
bool HeaderAbiDiff::DumpLoneElements(
    std::vector<const T *> &elements,
    const AbiElementMap<const abi_util::ElfSymbolIR *> *elf_map,
    abi_util::IRDiffDumper *ir_diff_dumper,
    abi_util::IRDiffDumper::DiffKind diff_kind) {
  // If the record / enum has source file information, skip it.
  std::smatch source_file_match;
  std::regex source_file_regex(" at ");
  for (auto &&element : elements) {
    if (abi_diff_wrappers::IgnoreSymbol<T>(
        element, ignored_symbols_,
        [](const T *e) {return e->GetLinkerSetKey();})) {
      continue;
    }
    // The element does exist in the .dynsym table, we do not have meta-data
    // surrounding the element.
    const std::string &element_linker_set_key = element->GetLinkerSetKey();
    if ((elf_map != nullptr) &&
        (elf_map->find(element_linker_set_key) != elf_map->end())) {
      continue;
    }
    if (std::regex_search(element_linker_set_key, source_file_match,
                          source_file_regex)) {
      continue;
    }
    if (!ir_diff_dumper->AddLinkableMessageIR(element, diff_kind)) {
      llvm::errs() << "Couldn't dump added /removed element\n";
      return false;
    }
  }
  return true;
}

template <typename T>
bool HeaderAbiDiff::DumpDiffElements(
    std::vector<std::pair<const T *,const T *>> &pairs,
    const AbiElementMap<const abi_util::TypeIR *> &old_types,
    const AbiElementMap<const abi_util::TypeIR *> &new_types,
    abi_util::IRDiffDumper *ir_diff_dumper,
    abi_util::IRDiffDumper::DiffKind diff_kind) {
  for (auto &&pair : pairs) {
    const T *old_element = pair.first;
    const T *new_element = pair.second;

    if (abi_diff_wrappers::IgnoreSymbol<T>(
        old_element, ignored_symbols_,
        [](const T *e) {return e->GetLinkerSetKey();})) {
      continue;
    }
    abi_diff_wrappers::DiffWrapper<T> diff_wrapper(old_element, new_element,
                                                   ir_diff_dumper, old_types,
                                                   new_types, &type_cache_);
    if (!diff_wrapper.DumpDiff(diff_kind)) {
      llvm::errs() << "Failed to diff elements\n";
      return false;
    }
  }
  return true;
}
