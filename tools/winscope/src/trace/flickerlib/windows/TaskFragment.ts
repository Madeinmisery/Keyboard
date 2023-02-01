/*
 * Copyright 2021, The Android Open Source Project
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

import {TaskFragment} from '../common';
import {shortenName} from '../mixin';
import {WindowContainer} from './WindowContainer';

TaskFragment.fromProto = (
  proto: any,
  isActivityInTree: boolean,
  nextSeq: () => number
): TaskFragment => {
  if (proto == null) {
    return null;
  } else {
    const windowContainer = WindowContainer.fromProto(
      /* proto */ proto.windowContainer,
      /* protoChildren */ proto.windowContainer?.children ?? [],
      /* isActivityInTree */ isActivityInTree,
      /* computedZ */ nextSeq
    );
    const entry = new TaskFragment(
      proto.activityType,
      proto.displayId,
      proto.minWidth,
      proto.minHeight,
      windowContainer
    );

    addAttributes(entry, proto);
    return entry;
  }
};

function addAttributes(entry: TaskFragment, proto: any) {
  entry.proto = proto;
  entry.kind = entry.constructor.name;
  entry.shortName = shortenName(entry.name);
}

export {TaskFragment};
