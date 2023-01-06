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

import {Parser} from 'parsers/parser';
import {ParserFactory} from 'parsers/parser_factory';
import {CommonTestUtils} from 'test/common/utils';
import {LayerTraceEntry, WindowManagerState} from 'trace/flickerlib/common';
import {Timestamp, TimestampType} from 'trace/timestamp';
import {TraceFile} from 'trace/trace';
import {TraceType} from 'trace/trace_type';

class UnitTestUtils extends CommonTestUtils {
  static async getParser(filename: string): Promise<Parser> {
    const file = new TraceFile(await CommonTestUtils.getFixtureFile(filename), undefined);
    const [parsers, errors] = await new ParserFactory().createParsers([file]);
    expect(parsers.length).toEqual(1);
    return parsers[0];
  }

  static async getWindowManagerState(): Promise<WindowManagerState> {
    return UnitTestUtils.getTraceEntry('traces/elapsed_timestamp/WindowManager.pb');
  }

  static async getLayerTraceEntry(): Promise<LayerTraceEntry> {
    return await UnitTestUtils.getTraceEntry('traces/elapsed_timestamp/SurfaceFlinger.pb');
  }

  static async getImeTraceEntries(): Promise<Map<TraceType, any>> {
    let surfaceFlingerEntry: LayerTraceEntry | undefined;
    {
      const parser = await UnitTestUtils.getParser('traces/ime/SurfaceFlinger_with_IME.pb');
      const timestamp = new Timestamp(TimestampType.ELAPSED, 502942319579n);
      surfaceFlingerEntry = await parser.getTraceEntry(timestamp);
    }

    let windowManagerEntry: WindowManagerState | undefined;
    {
      const parser = await UnitTestUtils.getParser('traces/ime/WindowManager_with_IME.pb');
      const timestamp = new Timestamp(TimestampType.ELAPSED, 502938057652n);
      windowManagerEntry = await parser.getTraceEntry(timestamp)!;
    }

    const entries = new Map<TraceType, any>();
    entries.set(TraceType.INPUT_METHOD_CLIENTS, [
      await UnitTestUtils.getTraceEntry('traces/ime/InputMethodClients.pb'),
      null,
    ]);
    entries.set(TraceType.INPUT_METHOD_MANAGER_SERVICE, [
      await UnitTestUtils.getTraceEntry('traces/ime/InputMethodManagerService.pb'),
      null,
    ]);
    entries.set(TraceType.INPUT_METHOD_SERVICE, [
      await UnitTestUtils.getTraceEntry('traces/ime/InputMethodService.pb'),
      null,
    ]);
    entries.set(TraceType.SURFACE_FLINGER, [surfaceFlingerEntry, null]);
    entries.set(TraceType.WINDOW_MANAGER, [windowManagerEntry, null]);

    return entries;
  }

  private static async getTraceEntry(filename: string) {
    const parser = await UnitTestUtils.getParser(filename);
    const timestamp = parser.getTimestamps(TimestampType.ELAPSED)![0];
    return parser.getTraceEntry(timestamp);
  }
}

export {UnitTestUtils};
