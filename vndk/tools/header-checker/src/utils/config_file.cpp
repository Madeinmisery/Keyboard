// Copyright (C) 2019 The Android Open Source Project
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

#include "utils/config_file.h"

#include "utils/string_utils.h"

#include <json/json.h>

#include <algorithm>
#include <fstream>
#include <map>
#include <string>


namespace header_checker {
namespace utils {


ConfigSection::ConfigSection(Json::Value root_) : root(root_) {
  assert(root.isMember("flags"));
  for (auto &key : root["flags"].getMemberNames()) {
    map_[key] = root["flags"][key];
  }
}

ConfigFile::ConfigFile(const std::string &path) {
  std::ifstream stream(path);
  Json::Value root;
  stream >> root;
  for (auto &key : root.getMemberNames()) {
    map_[key] = ConfigSection(root[key]);
  }
}


}  // namespace utils
}  // namespace header_checker
