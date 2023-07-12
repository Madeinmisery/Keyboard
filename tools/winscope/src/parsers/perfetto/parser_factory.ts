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

import {FunctionUtils, OnProgressUpdateType} from 'common/function_utils';
import {globalConfig} from 'common/global_config';
import {UrlUtils} from 'common/url_utils';
import {Parser} from 'trace/parser';
import {TraceFile} from 'trace/trace_file';
import {initWasm, resetEngineWorker, WasmEngineProxy} from 'trace_processor/wasm_engine_proxy';
import {ParserSurfaceFlinger} from './parser_surface_flinger';
import {ParserTransactions} from './parser_transactions';

export class ParserFactory {
  private static readonly PARSERS = [ParserSurfaceFlinger, ParserTransactions];
  private static readonly CHUNK_SIZE_BYTES = 100 * 1024 * 1024;
  private static traceProcessor?: WasmEngineProxy;

  async createParsers(
    traceFile: TraceFile,
    onProgressUpdate: OnProgressUpdateType = FunctionUtils.DO_NOTHING
  ): Promise<Array<Parser<object>>> {
    const parsers: Array<Parser<object>> = [];

    const traceProcessor = await this.initializeTraceProcessor();
    for (
      let chunkStart = 0;
      chunkStart < traceFile.file.size;
      chunkStart += ParserFactory.CHUNK_SIZE_BYTES
    ) {
      onProgressUpdate(chunkStart / traceFile.file.size * 100);
      const chunkEnd = chunkStart + ParserFactory.CHUNK_SIZE_BYTES;
      const data = await traceFile.file.slice(chunkStart, chunkEnd).arrayBuffer();
      try {
        await traceProcessor.parse(new Uint8Array(data));
      } catch (e) {
        console.error('Trace processor failed to parse data:', e);
        return [];
      }
    }
    await traceProcessor.notifyEof();
    onProgressUpdate(100);

    for (const ParserType of ParserFactory.PARSERS) {
      try {
        const parser = new ParserType(traceFile, traceProcessor);
        await parser.parse();
        parsers.push(parser);
      } catch (error) {
        // skip current parser
      }
    }

    return parsers;
  }

  private async initializeTraceProcessor(): Promise<WasmEngineProxy> {
    if (!ParserFactory.traceProcessor) {
      const traceProcessorRootUrl =
        globalConfig.MODE === 'KARMA_TEST'
          ? UrlUtils.getRootUrl() + 'base/deps_build/trace_processor/to_be_served/'
          : UrlUtils.getRootUrl();
      initWasm(traceProcessorRootUrl);
      const engineId = 'random-id';
      const enginePort = resetEngineWorker();
      ParserFactory.traceProcessor = new WasmEngineProxy(engineId, enginePort);
    }

    await ParserFactory.traceProcessor.resetTraceProcessor({
      cropTrackEvents: false,
      ingestFtraceInRawTable: false,
      analyzeTraceProtoContent: false,
    });

    return ParserFactory.traceProcessor;
  }
}
