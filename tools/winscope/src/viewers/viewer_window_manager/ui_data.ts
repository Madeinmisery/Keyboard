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
import {TraceType} from 'trace/trace_type';
import {Rectangle} from 'viewers/common/rectangle';
import {HierarchyTreeNode, PropertiesTreeNode} from 'viewers/common/ui_tree_utils';
import {UserOptions} from 'viewers/common/user_options';

export class UiData {
  dependencies: Array<TraceType>;
  rects: Rectangle[] = [];
  displayIds: number[] = [];
  highlightedItems: Array<string> = [];
  pinnedItems: Array<HierarchyTreeNode> = [];
  hierarchyUserOptions: UserOptions = {};
  propertiesUserOptions: UserOptions = {};
  tree: HierarchyTreeNode | null = null;
  propertiesTree: PropertiesTreeNode | null = null;

  constructor(dependencies?: Array<TraceType>) {
    this.dependencies = dependencies ?? [];
  }
}
