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

import {TraceType, ViewNode} from 'trace/trace_type';
import {HierarchyTreeNode, PropertiesTreeNode} from 'viewers/common/ui_tree_utils';
import {UserOptions} from 'viewers/common/user_options';
import {UiRect} from 'viewers/components/rects/types2d';

export class UiData {
  readonly dependencies: TraceType[] = [TraceType.VIEW_CAPTURE];
  readonly displayPropertyGroups = false;

  constructor(
    readonly rects: UiRect[],
    public sfRects: UiRect[] | undefined,
    public tree: HierarchyTreeNode | null,
    public hierarchyUserOptions: UserOptions,
    public propertiesUserOptions: UserOptions,
    public pinnedItems: HierarchyTreeNode[],
    public highlightedItem: string,
    public propertiesTree: PropertiesTreeNode | null,
    public selectedViewNode: ViewNode
  ) {}
}
