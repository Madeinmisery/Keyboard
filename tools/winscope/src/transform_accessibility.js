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

import { transform, nanos_to_string, get_visible_chip } from './transform.js'

function transform_accessibility(accessibility) {
  return transform({
    obj: accessibility,
    kind: 'accessibility',
    name: 'accessibility',
    children: []
  });
}

function transform_entry(entry) {
  return transform({
    obj: entry,
    kind: 'entry',
    name: nanos_to_string(entry.elapsedRealtimeNanos),
    children: [
      [entry.accessibilityService, transform_accessibility],
    ],
    timestamp: entry.elapsedRealtimeNanos,
    stableId: 'entry'
  });
}

function transform_accessibility_trace(entries) {
  return transform({
    obj: entries,
    kind: 'entries',
    name: 'entries',
    children: [
      [entries.entry, transform_entry],
    ],
  });
}

export { transform_accessibility_trace };
