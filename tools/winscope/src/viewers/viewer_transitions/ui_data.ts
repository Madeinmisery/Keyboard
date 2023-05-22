/*
 * Copyright (C) 2023 The Android Open Source Project
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

import {Transition} from 'trace/flickerlib/common';
import {PropertiesTreeNode} from 'viewers/common/ui_tree_utils';

export class UiData {
  constructor(
    transitions: Transition[],
    selectedTransition: Transition,
    selectedTransitionPropertiesTree?: PropertiesTreeNode
  ) {
    this.entries = transitions;
    this.selectedTransition = selectedTransition;
    this.selectedTransitionPropertiesTree = selectedTransitionPropertiesTree;
  }

  entries: Transition[] = [];
  selectedTransition: Transition | undefined;
  selectedTransitionPropertiesTree: PropertiesTreeNode | undefined;

  static EMPTY = new UiData([], undefined, undefined);
}
