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

import {
  ActiveBuffer,
  Color,
  EMPTY_COLOR,
  EMPTY_RECT,
  EMPTY_RECTF,
  EMPTY_TRANSFORM,
  Layer,
  LayerProperties,
} from 'flickerlib/common';

class LayerBuilder {
  setFlags(value: number): LayerBuilder {
    this.flags = value;
    return this;
  }

  setColor(color: Color): LayerBuilder {
    this.color = color;
    return this;
  }

  build(): Layer {
    const properties = new LayerProperties(
      null /* visibleRegion */,
      new ActiveBuffer(0, 0, 0, 0),
      this.flags,
      EMPTY_RECTF /* bounds */,
      this.color,
      false /* isOpaque */,
      1 /* shadowRadius */,
      1 /* cornerRadius */,
      EMPTY_RECTF /* screenBounds */,
      EMPTY_TRANSFORM /* transform */,
      0 /* effectiveScalingMode */,
      EMPTY_TRANSFORM /* bufferTransform */,
      0 /* hwcCompositionType */,
      1 /* backgroundBlurRadius */,
      EMPTY_RECT /* crop */,
      false /* isRelativeOf */,
      -1 /* zOrderRelativeOfId */,
      0 /* stackId */,
      null /* inputRegion */
    );

    return new Layer(
      'name' /* name */,
      0 /* id */,
      -1 /*parentId */,
      0 /* z */,
      '0' /* currFrameString */,
      properties
    );
  }

  private flags = 0;
  private color = EMPTY_COLOR;
}

export {LayerBuilder};
