/*
 * Copyright (C) 2022 The Android Open Source Project
 *
 * Licensed under the Apache License, Version 2.0 (the "License");
 * you may not use this file except in compliance with the License.
 * You may obtain a copy of the License at
 *
 *      http://www.apache.org/licenses/LICENSE-2.0
 *
 * Unless required by applicable law or agreed to in writing, software
 * distributed under the License is distributed on an "AS IS" BASIS,
 * WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
 * See the License for the specific language governing permissions and
 * limitations under the License.
 */
import * as path from "path";
import {CommonTestUtils} from "../common/utils";
import {by, element} from "protractor";

class E2eTestUtils extends CommonTestUtils {
  static getProductionIndexHtmlPath(): string {
    return path.join(CommonTestUtils.getProjectRootPath(), "dist/prod/index.html");
  }

  static async uploadFixture(path: string) {
    const inputFile = element(by.css("input[type=\"file\"]"));
    await inputFile.sendKeys(E2eTestUtils.getFixturePath(path));
  }

  static async clickViewTracesButton() {
    const loadData = element(by.css(".load-btn"));
    await loadData.click();
  }
}

export {E2eTestUtils};
