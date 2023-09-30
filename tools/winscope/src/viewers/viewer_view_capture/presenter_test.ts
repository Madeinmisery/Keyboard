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

import {TracePositionUpdate} from 'app/app_event';
import {RealTimestamp, TimestampType} from 'common/time';
import {HierarchyTreeBuilder} from 'test/unit/hierarchy_tree_builder';
import {MockStorage} from 'test/unit/mock_storage';
import {TraceBuilder} from 'test/unit/trace_builder';
import {UnitTestUtils} from 'test/unit/utils';
import {Parser} from 'trace/parser';
import {Trace} from 'trace/trace';
import {Traces} from 'trace/traces';
import {HierarchyTreeNode} from 'viewers/common/ui_tree_utils';
import {UserOptions} from 'viewers/common/user_options';
import {Presenter} from 'viewers/viewer_view_capture/presenter';
import {UiData} from 'viewers/viewer_view_capture/ui_data';

describe('PresenterViewCapture', () => {
  let parser: Parser<object>;
  let trace: Trace<object>;
  let uiData: UiData;
  let presenter: Presenter;
  let positionUpdate: TracePositionUpdate;
  let selectedTree: HierarchyTreeNode;

  beforeAll(async () => {
    parser = await UnitTestUtils.getParser(
      'traces/elapsed_and_real_timestamp/com.google.android.apps.nexuslauncher_0.vc'
    );
    trace = new TraceBuilder<object>()
      .setEntries([
        parser.getEntry(0, TimestampType.REAL),
        parser.getEntry(1, TimestampType.REAL),
        parser.getEntry(2, TimestampType.REAL),
      ])
      .build();
    positionUpdate = TracePositionUpdate.fromTraceEntry(trace.getEntry(0));
    selectedTree = new HierarchyTreeBuilder()
      .setName('Name@Id')
      .setStableId('stableId')
      .setKind('kind')
      .setDiffType('diff type')
      .setId(53)
      .build();
  });

  beforeEach(() => {
    presenter = createPresenter(trace);
  });

  it('is robust to empty trace', async () => {
    const emptyTrace = new TraceBuilder<object>().setEntries([]).build();
    const presenter = createPresenter(emptyTrace);

    const positionUpdateWithoutTraceEntry = TracePositionUpdate.fromTimestamp(
      new RealTimestamp(0n)
    );
    await presenter.onAppEvent(positionUpdateWithoutTraceEntry);
    expect(uiData.hierarchyUserOptions).toBeTruthy();
    expect(uiData.tree).toBeFalsy();
  });

  it('processes trace position updates', async () => {
    await presenter.onAppEvent(positionUpdate);

    expect(uiData.rects.length).toBeGreaterThan(0);
    expect(uiData.highlightedItem?.length).toEqual(0);
    const hierarchyOpts = Object.keys(uiData.hierarchyUserOptions);
    expect(hierarchyOpts).toBeTruthy();
    const propertyOpts = Object.keys(uiData.propertiesUserOptions);
    expect(propertyOpts).toBeTruthy();
    expect(Object.keys(uiData.tree!).length > 0).toBeTrue();
  });

  it('creates input data for rects view', async () => {
    await presenter.onAppEvent(positionUpdate);
    expect(uiData.rects.length).toBeGreaterThan(0);
    expect(uiData.rects[0].topLeft).toEqual({x: 0, y: 0});
    expect(uiData.rects[0].bottomRight).toEqual({x: 1080, y: 249});
  });

  it('updates pinned items', async () => {
    const pinnedItem = new HierarchyTreeBuilder().setName('FirstPinnedItem').setId('id').build();
    await presenter.onAppEvent(positionUpdate);
    presenter.updatePinnedItems(pinnedItem);
    expect(uiData.pinnedItems).toContain(pinnedItem);
  });

  it('updates highlighted item', async () => {
    await presenter.onAppEvent(positionUpdate);
    expect(uiData.highlightedItem).toEqual('');

    const id = '4';
    presenter.updateHighlightedItem(id);
    expect(uiData.highlightedItem).toBe(id);
  });

  it('updates hierarchy tree', async () => {
    await presenter.onAppEvent(positionUpdate);

    expect(
      // TaskbarDragLayer -> TaskbarView
      uiData.tree?.children[0].id
    ).toEqual('com.android.launcher3.taskbar.TaskbarView@80213537');

    const userOptions: UserOptions = {
      showDiff: {
        name: 'Show diff',
        enabled: false,
      },
      simplifyNames: {
        name: 'Simplify names',
        enabled: false,
      },
      onlyVisible: {
        name: 'Only visible',
        enabled: true,
      },
    };
    presenter.updateHierarchyTree(userOptions);
    expect(uiData.hierarchyUserOptions).toEqual(userOptions);
    expect(
      // TaskbarDragLayer -> TaskbarScrimView
      uiData.tree?.children[0].id
    ).toEqual('com.android.launcher3.taskbar.TaskbarScrimView@114418695');
  });

  it('filters hierarchy tree', async () => {
    const userOptions: UserOptions = {
      showDiff: {
        name: 'Show diff',
        enabled: false,
      },
      simplifyNames: {
        name: 'Simplify names',
        enabled: true,
      },
      onlyVisible: {
        name: 'Only visible',
        enabled: false,
      },
    };
    await presenter.onAppEvent(positionUpdate);
    presenter.updateHierarchyTree(userOptions);
    presenter.filterHierarchyTree('BubbleBarView');

    expect(
      // TaskbarDragLayer -> BubbleBarView if filter works as expected
      uiData.tree?.children[0].id
    ).toEqual('com.android.launcher3.taskbar.bubbles.BubbleBarView@256010548');
  });

  it('sets properties tree and associated ui data', async () => {
    await presenter.onAppEvent(positionUpdate);
    presenter.newPropertiesTree(selectedTree);
    expect(uiData.propertiesTree).toBeTruthy();
  });

  it('updates properties tree', async () => {
    const userOptions: UserOptions = {
      showDiff: {
        name: 'Show diff',
        enabled: true,
      },
      showDefaults: {
        name: 'Show defaults',
        enabled: true,
        tooltip: `
                      If checked, shows the value of all properties.
                      Otherwise, hides all properties whose value is
                      the default for its data type.
                    `,
      },
    };

    await presenter.onAppEvent(positionUpdate);
    presenter.newPropertiesTree(selectedTree);
    expect(uiData.propertiesTree?.diffType).toBeFalsy();

    presenter.updatePropertiesTree(userOptions);
    expect(uiData.propertiesUserOptions).toEqual(userOptions);
    expect(uiData.propertiesTree?.diffType).toBeTruthy();
  });

  it('filters properties tree', async () => {
    await presenter.onAppEvent(positionUpdate);

    const userOptions: UserOptions = {
      showDiff: {
        name: 'Show diff',
        enabled: true,
      },
      showDefaults: {
        name: 'Show defaults',
        enabled: true,
        tooltip: `
                        If checked, shows the value of all properties.
                        Otherwise, hides all properties whose value is
                        the default for its data type.
                      `,
      },
    };
    presenter.updatePropertiesTree(userOptions);
    let nonTerminalChildren = uiData.propertiesTree?.children?.filter(
      (it) => typeof it.propertyKey === 'string'
    );
    expect(nonTerminalChildren?.length).toEqual(25);
    presenter.filterPropertiesTree('alpha');

    nonTerminalChildren = uiData.propertiesTree?.children?.filter(
      (it) => typeof it.propertyKey === 'string'
    );
    expect(nonTerminalChildren?.length).toEqual(1);
  });

  const createPresenter = (trace: Trace<object>): Presenter => {
    const traces = new Traces();
    traces.setTrace(parser.getTraceType(), trace);
    return new Presenter(parser.getTraceType(), traces, new MockStorage(), (newData: UiData) => {
      uiData = newData;
    });
  };
});
