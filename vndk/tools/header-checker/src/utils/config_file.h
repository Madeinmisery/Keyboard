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

#ifndef CONFIG_FILE_H_
#define CONFIG_FILE_H_

#include <json/json.h>

#include <algorithm>
#include <cassert>
#include <iosfwd>
#include <map>
#include <string>


namespace header_checker {
namespace utils {


class ConfigSection {
 public:
  using MapType = std::map<std::string, Json::Value>;
  using const_iterator = MapType::const_iterator;


 public:
  ConfigSection() = default;
  ConfigSection(ConfigSection &&) = default;
  ConfigSection &operator=(ConfigSection &&) = default;
  ConfigSection(Json::Value root);

  bool HasProperty(const std::string &name) const {
    return map_.find(name) != map_.end();
  }

  Json::Value GetProperty(const std::string &name) const {
    auto &&it = map_.find(name);
    if (it == map_.end()) {
      return Json::Value();
    }
    return it->second;
  }

  Json::Value operator[](const std::string &name) const {
    return GetProperty(name);
  }

  const_iterator begin() const {
    return map_.begin();
  }

  const_iterator end() const {
    return map_.end();
  }

 private:
  ConfigSection(const ConfigSection &) = delete;
  ConfigSection &operator=(const ConfigSection &) = delete;

 private:
  MapType map_;
  Json::Value root;
};


class ConfigFile {
 public:
  using MapType = std::map<std::string, ConfigSection>;
  using const_iterator = MapType::const_iterator;


 public:
  ConfigFile() = default;
  ConfigFile(ConfigFile &&) = default;
  ConfigFile &operator=(ConfigFile &&) = default;
  ConfigFile(std::istream &istream);
  ConfigFile(const std::string &path);

  bool HasSection(const std::string &section_name) const {
    return map_.find(section_name) != map_.end();
  }

  const ConfigSection &GetSection(const std::string &section_name) const {
    auto &&it = map_.find(section_name);
    assert(it != map_.end());
    return it->second;
  }

  const ConfigSection &operator[](const std::string &section_name) const {
    return GetSection(section_name);
  }

  bool HasProperty(const std::string &section_name,
                   const std::string &property_name) const {
    auto &&it = map_.find(section_name);
    if (it == map_.end()) {
      return false;
    }
    return it->second.HasProperty(property_name);
  }

  Json::Value GetProperty(const std::string &section_name,
                          const std::string &property_name) const {
    auto &&it = map_.find(section_name);
    if (it == map_.end()) {
      return Json::Value();
    }
    return it->second.GetProperty(property_name);
  }


  const_iterator begin() const {
    return map_.begin();
  }

  const_iterator end() const {
    return map_.end();
  }

 private:
  ConfigFile(const ConfigFile &) = delete;
  ConfigFile &operator=(const ConfigFile &) = delete;


 private:
  MapType map_;
  Json::Value root;
};


}  // namespace utils
}  // namespace header_checker


#endif  // CONFIG_FILE_H_
