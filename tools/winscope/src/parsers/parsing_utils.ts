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

import {ArrayUtils} from 'common/array_utils';

export class ParsingUtils {
  static throwIfMagicNumberDoesntMatch(traceBuffer: Uint8Array, magicNumber: number[] | undefined) {
    if (magicNumber !== undefined) {
      const bufferContainsMagicNumber = ArrayUtils.equal(
        magicNumber,
        traceBuffer.slice(0, magicNumber.length)
      );
      if (!bufferContainsMagicNumber) {
        throw TypeError("buffer doesn't contain expected magic number");
      }
    }
  }

  // Add default values to the proto objects.
  static addDefaultProtoFields(protoObj: any): any {
    if (!protoObj || protoObj !== Object(protoObj) || !protoObj.$type) {
      return protoObj;
    }

    for (const fieldName in protoObj.$type.fields) {
      if (Object.prototype.hasOwnProperty.call(protoObj.$type.fields, fieldName)) {
        const fieldProperties = protoObj.$type.fields[fieldName];
        const field = protoObj[fieldName];

        if (Array.isArray(field)) {
          field.forEach((item, _) => {
            ParsingUtils.addDefaultProtoFields(item);
          });
          continue;
        }

        if (!field) {
          protoObj[fieldName] = fieldProperties.defaultValue;
        }

        if (fieldProperties.resolvedType && fieldProperties.resolvedType.valuesById) {
          protoObj[fieldName] =
            fieldProperties.resolvedType.valuesById[protoObj[fieldProperties.name]];
          continue;
        }
        ParsingUtils.addDefaultProtoFields(protoObj[fieldName]);
      }
    }

    return protoObj;
  }
}
