// Copyright (C) 2021 The Android Open Source Project
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

#include "utils/source_path_utils.h"

#include <gtest/gtest.h>

#include <cstdlib>
#include <filesystem>
#include <fstream>
#include <vector>

namespace header_checker {
namespace utils {

class TempDir {
 public:
  TempDir() {
    std::string temp_dir_template =
        std::filesystem::temp_directory_path() / "SourcePathUtilsTest_XXXXXX";
    std::vector<char> temp_dir_vec(temp_dir_template.begin(),
                                   temp_dir_template.end());
    temp_dir_vec.push_back('\0');
    if (mkdtemp(temp_dir_vec.data()) == NULL) {
      return;
    }
    temp_dir_vec.pop_back();
    path_.assign(temp_dir_vec.begin(), temp_dir_vec.end());
  }

  ~TempDir() {
    if (!path_.empty()) {
      std::filesystem::remove_all(path_);
    }
  }

  const std::filesystem::path &GetPath() const { return path_; }

 private:
  std::filesystem::path path_;
};

TEST(SourcePathUtilsTest, CollectAllExportedHeaders) {
  TempDir temp_dir;
  const std::filesystem::path &header_dir = temp_dir.GetPath();
  ASSERT_FALSE(header_dir.empty());

  const std::filesystem::path header = header_dir / "header.h";
  std::ofstream fs(header);
  fs << "// test";
  fs.close();

  std::error_code ec;
  const std::filesystem::path subdir = header_dir / "subdir";
  std::filesystem::create_directory(subdir, ec);
  ASSERT_FALSE(ec);

  const std::filesystem::path subdir_link = header_dir / "subdir_link";
  std::filesystem::create_directory_symlink(subdir, subdir_link, ec);
  ASSERT_FALSE(ec);

  const std::filesystem::path hidden_subdir_link = header_dir / ".subdir_link";
  std::filesystem::create_directory_symlink(subdir, hidden_subdir_link, ec);
  ASSERT_FALSE(ec);

  const std::filesystem::path header_link = subdir / "header_link.h";
  std::filesystem::create_symlink(header, header_link, ec);
  ASSERT_FALSE(ec);

  const std::filesystem::path hidden_header_link = subdir / ".header_link.h";
  std::filesystem::create_symlink(header, hidden_header_link, ec);
  ASSERT_FALSE(ec);

  const std::filesystem::path non_header_link = subdir / "header_link.txt";
  std::filesystem::create_symlink(header, non_header_link, ec);
  ASSERT_FALSE(ec);

  std::vector<std::string> exported_header_dirs{header_dir};
  std::vector<RootDir> root_dirs{{header_dir, "include"}};
  std::set<std::string> headers =
      CollectAllExportedHeaders(exported_header_dirs, root_dirs);

  std::set<std::string> expected_headers{"include/header.h",
                                         "include/subdir/header_link.h",
                                         "include/subdir_link/header_link.h"};
  ASSERT_EQ(headers, expected_headers);
}

TEST(SourcePathUtilsTest, NormalizeAbsolutePaths) {
  const std::vector<std::string> args{"/root/dir"};
  const RootDirs root_dirs = ParseRootDirs(args);
  ASSERT_EQ(1, root_dirs.size());
  ASSERT_EQ("/root/dir", root_dirs[0].path);
  ASSERT_EQ("", root_dirs[0].replacement);

  EXPECT_EQ("", NormalizePath("/root/dir", root_dirs));
  EXPECT_EQ("test", NormalizePath("/root/dir/test", root_dirs));
  EXPECT_EQ("/root/unit/test",
            NormalizePath("/root/dir/../unit/test", root_dirs));
}


TEST(SourcePathUtilsTest, NormalizeCwdPaths) {
  const RootDirs cwd = ParseRootDirs(std::vector<std::string>());
  ASSERT_EQ(1, cwd.size());
  ASSERT_NE("", cwd[0].path);
  ASSERT_EQ("", cwd[0].replacement);

  EXPECT_EQ("", NormalizePath("", cwd));
  EXPECT_EQ("unit/test", NormalizePath("./unit/test/.", cwd));
  EXPECT_EQ("unit/test", NormalizePath("unit//test//", cwd));
  EXPECT_EQ("test", NormalizePath("unit/../test", cwd));
  EXPECT_EQ("unit/test", NormalizePath(cwd[0].path + "/unit/test", cwd));
  EXPECT_EQ('/', NormalizePath("../unit/test", cwd)[0]);
}


TEST(SourcePathUtilsTest, NormalizePathsWithMultipleRootDirs) {
  const std::vector<std::string> args{"/before:/", "/before/dir:after"};
  const RootDirs root_dirs = ParseRootDirs(args);
  ASSERT_EQ(2, root_dirs.size());
  ASSERT_EQ("/before/dir", root_dirs[0].path);
  ASSERT_EQ("after", root_dirs[0].replacement);
  ASSERT_EQ("/before", root_dirs[1].path);
  ASSERT_EQ("/", root_dirs[1].replacement);

  EXPECT_EQ("/directory", NormalizePath("/before/directory", root_dirs));
  EXPECT_EQ("after", NormalizePath("/before/dir", root_dirs));
}


TEST(SourcePathUtilsTest, NormalizeRelativePaths) {
  const std::vector<std::string> args{"../before/.:..//after/."};
  const RootDirs root_dirs = ParseRootDirs(args);
  ASSERT_EQ(1, root_dirs.size());
  ASSERT_EQ('/', root_dirs[0].path[0]);
  ASSERT_EQ("../after", root_dirs[0].replacement);

  EXPECT_EQ("../after", NormalizePath("../before", root_dirs));
}


}  // namespace utils
}  // namespace header_checker
