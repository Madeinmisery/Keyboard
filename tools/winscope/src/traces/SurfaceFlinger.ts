/*
 * Copyright 2020, The Android Open Source Project
 *
 * Licensed under the Apache License, Version 2.0 (the "License");
 * you may not use this file except in compliance with the License.
 * You may obtain a copy of the License at
 *
 *     http://www.apache.org/licenses/LICENSE-2.0
 *
 * Unless required by applicable law or agreed to in writing, software
 * distributed under the License is distributed on an "AS IS" BASIS,
 * WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
 * See the License for the specific language governing permissions and
 * limitations under the License.
 */

import { FILE_TYPES, TRACE_TYPES } from '@/decode.js';
import TraceBase from './TraceBase';

export default class SurfaceFlinger extends TraceBase {
  sfTraceFile: any;

  constructor(files) {
    const sfTraceFile = files[FILE_TYPES.SURFACE_FLINGER_TRACE];
    super(sfTraceFile.data, sfTraceFile.timeline, files);

    this.sfTraceFile = sfTraceFile;
  }

  get type() {
    return TRACE_TYPES.SURFACE_FLINGER;
  }
}
