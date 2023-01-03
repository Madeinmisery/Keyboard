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
import {PropertiesTreeNode} from 'viewers/common/ui_tree_utils';

class UiData {
  constructor(
    public allVSyncIds: string[],
    public allPids: string[],
    public allUids: string[],
    public allTypes: string[],
    public allIds: string[],
    public entries: UiDataEntry[],
    public currentEntryIndex: undefined | number,
    public selectedEntryIndex: undefined | number,
    public scrollToIndex: undefined | number,
    public currentPropertiesTree: undefined | PropertiesTreeNode
  ) {}

  public static EMPTY = new UiData(
    [],
    [],
    [],
    [],
    [],
    [],
    undefined,
    undefined,
    undefined,
    undefined
  );
}

class UiDataEntry {
  constructor(
    public originalIndexInTraceEntry: number,
    public time: string,
    public vsyncId: number,
    public pid: string,
    public uid: string,
    public type: string,
    public id: string,
    public what: string,
    public propertiesTree?: PropertiesTreeNode
  ) {}
}

class UiDataEntryType {
  public static DisplayAdded = 'DISPLAY_ADDED';
  public static DisplayRemoved = 'DISPLAY_REMOVED';
  public static DisplayChanged = 'DISPLAY_CHANGED';
  public static LayerAdded = 'LAYER_ADDED';
  public static LayerRemoved = 'LAYER_REMOVED';
  public static LayerChanged = 'LAYER_CHANGED';
  public static LayerHandleRemoved = 'LAYER_HANDLE_REMOVED';
}

export {UiData, UiDataEntry, UiDataEntryType};
