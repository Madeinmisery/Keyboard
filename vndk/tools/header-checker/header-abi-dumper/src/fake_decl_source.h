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

#include <clang/Frontend/CompilerInstance.h>
#include <clang/Sema/ExternalSemaSource.h>
#include <clang/Sema/Sema.h>

class FakeDeclSource : public clang::ExternalSemaSource {
 private:
  const clang::CompilerInstance &ci_;

  clang::RecordDecl *CreateRecordDecl(const clang::DeclarationName &name,
                                      clang::DeclContext *decl_context);

  clang::ClassTemplateDecl *
  CreateClassTemplateDecl(clang::NamedDecl *record_decl,
                          clang::DeclContext *decl_context);

  clang::NamespaceDecl *CreateNamespaceDecl(const clang::DeclarationName &name,
                                            clang::DeclContext *decl_context);

  // Create a NamedDecl in decl_context according to the lookup name kind and
  // the declaration name kind. If this function does not support the kinds, it
  // returns nullptr.
  clang::NamedDecl *CreateDecl(clang::Sema::LookupNameKind kind,
                               const clang::DeclarationName &name,
                               clang::DeclContext *decl_context);

 public:
  FakeDeclSource(const clang::CompilerInstance &ci);

  clang::TypoCorrection
  CorrectTypo(const clang::DeclarationNameInfo &typo, int lookup_kind,
              clang::Scope *scope, clang::CXXScopeSpec *scope_spec,
              clang::CorrectionCandidateCallback &ccc,
              clang::DeclContext *member_context, bool entering_context,
              const clang::ObjCObjectPointerType *opt) override;

  bool LookupUnqualified(clang::LookupResult &result,
                         clang::Scope *scope) override;
};
