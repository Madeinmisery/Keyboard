/*
 * Copyright (C) 2024 The Android Open Source Project
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

import {assertDefined} from 'common/assert_utils';
import {TransformType} from 'parsers/surface_flinger/transform_utils';
import {PropertyTreeBuilder} from 'test/unit/property_tree_builder';
import {TreeNodeUtils} from 'test/unit/tree_node_utils';
import {
  BUFFER_FORMATTER,
  COLOR_FORMATTER,
  DEFAULT_PROPERTY_FORMATTER,
  EMPTY_ARRAY_STRING,
  EMPTY_OBJ_STRING,
  LAYER_ID_FORMATTER,
  POSITION_FORMATTER,
  RECT_FORMATTER,
  REGION_FORMATTER,
  SIZE_FORMATTER,
  TRANSFORM_FORMATTER,
} from './formatters';
import {PropertySource, PropertyTreeNode} from './property_tree_node';

describe('Formatters', () => {
  describe('PropertyFormatter', () => {
    it('translates simple values correctly', () => {
      expect(
        DEFAULT_PROPERTY_FORMATTER.format(new PropertyTreeNode('', '', PropertySource.PROTO, 12345))
      ).toEqual('12345');
      expect(
        DEFAULT_PROPERTY_FORMATTER.format(
          new PropertyTreeNode('', '', PropertySource.PROTO, 'test_string')
        )
      ).toEqual('test_string');
      expect(
        DEFAULT_PROPERTY_FORMATTER.format(new PropertyTreeNode('', '', PropertySource.PROTO, 0.4))
      ).toEqual('0.4');
    });

    it('translates values with toString method correctly', () => {
      expect(
        DEFAULT_PROPERTY_FORMATTER.format(
          new PropertyTreeNode('', '', PropertySource.PROTO, BigInt(123))
        )
      ).toEqual('123');
    });

    it('translates default values correctly', () => {
      expect(
        DEFAULT_PROPERTY_FORMATTER.format(new PropertyTreeNode('', '', PropertySource.PROTO, []))
      ).toEqual(EMPTY_ARRAY_STRING);
      expect(
        DEFAULT_PROPERTY_FORMATTER.format(new PropertyTreeNode('', '', PropertySource.PROTO, false))
      ).toEqual('false');
      expect(
        DEFAULT_PROPERTY_FORMATTER.format(new PropertyTreeNode('', '', PropertySource.PROTO, null))
      ).toEqual('null');
    });
  });

  describe('ColorFormatter', () => {
    it('translates empty color to string correctly', () => {
      expect(COLOR_FORMATTER.format(TreeNodeUtils.makeColorNode(-1, -1, -1, 1))).toEqual(
        `${EMPTY_OBJ_STRING}, alpha: 1`
      );
      expect(COLOR_FORMATTER.format(TreeNodeUtils.makeColorNode(1, 1, 1, 0))).toEqual(
        `${EMPTY_OBJ_STRING}, alpha: 0`
      );
    });

    it('translates non-empty color to string correctly', () => {
      expect(COLOR_FORMATTER.format(TreeNodeUtils.makeColorNode(1, 2, 3, 1))).toEqual(
        '(1, 2, 3, 1)'
      );
      expect(COLOR_FORMATTER.format(TreeNodeUtils.makeColorNode(1, 2, 3, 0.5))).toEqual(
        '(1, 2, 3, 0.5)'
      );
    });
  });

  describe('RectFormatter', () => {
    it('translates empty rect to string correctly', () => {
      expect(RECT_FORMATTER.format(TreeNodeUtils.makeRectNode(0, 0, -1, -1))).toEqual(
        EMPTY_OBJ_STRING
      );
      expect(RECT_FORMATTER.format(TreeNodeUtils.makeRectNode(0, 0, 0, 0))).toEqual(
        EMPTY_OBJ_STRING
      );
    });

    it('translates non-empty rect to string correctly', () => {
      expect(RECT_FORMATTER.format(TreeNodeUtils.makeRectNode(0, 0, 1, 1))).toEqual(
        '(0, 0) - (1, 1)'
      );
      expect(RECT_FORMATTER.format(TreeNodeUtils.makeRectNode(0, 0, 10, 10))).toEqual(
        '(0, 0) - (10, 10)'
      );
    });
  });

  describe('BufferFormatter', () => {
    it('translates buffer to string correctly', () => {
      const buffer = TreeNodeUtils.makeBufferNode();
      expect(BUFFER_FORMATTER.format(buffer)).toEqual('w: 1, h: 0, stride: 0, format: 1');
    });
  });

  describe('LayerIdFormatter', () => {
    it('translates -1 id correctly', () => {
      expect(
        LAYER_ID_FORMATTER.format(new PropertyTreeNode('', '', PropertySource.PROTO, -1))
      ).toEqual('none');
    });

    it('translates valid id correctly', () => {
      expect(
        LAYER_ID_FORMATTER.format(new PropertyTreeNode('', '', PropertySource.PROTO, 1))
      ).toEqual('1');
      expect(
        LAYER_ID_FORMATTER.format(new PropertyTreeNode('', '', PropertySource.PROTO, -10))
      ).toEqual('-10');
    });
  });

  describe('TransformFormatter', () => {
    it('translates type correctly', () => {
      expect(
        TRANSFORM_FORMATTER.format(TreeNodeUtils.makeTransformNode(TransformType.EMPTY))
      ).toEqual('IDENTITY');
      expect(
        TRANSFORM_FORMATTER.format(TreeNodeUtils.makeTransformNode(TransformType.TRANSLATE_VAL))
      ).toEqual('TRANSLATE');
      expect(
        TRANSFORM_FORMATTER.format(TreeNodeUtils.makeTransformNode(TransformType.SCALE_VAL))
      ).toEqual('SCALE');
      expect(
        TRANSFORM_FORMATTER.format(TreeNodeUtils.makeTransformNode(TransformType.FLIP_H_VAL))
      ).toEqual('IDENTITY|FLIP_H');
      expect(
        TRANSFORM_FORMATTER.format(TreeNodeUtils.makeTransformNode(TransformType.FLIP_V_VAL))
      ).toEqual('IDENTITY|FLIP_V');
      expect(
        TRANSFORM_FORMATTER.format(TreeNodeUtils.makeTransformNode(TransformType.ROT_90_VAL))
      ).toEqual('IDENTITY|ROT_90');
      expect(
        TRANSFORM_FORMATTER.format(TreeNodeUtils.makeTransformNode(TransformType.ROT_INVALID_VAL))
      ).toEqual('IDENTITY|ROT_INVALID');
    });
  });

  describe('SizeFormatter', () => {
    it('translates size correctly', () => {
      expect(SIZE_FORMATTER.format(TreeNodeUtils.makeSizeNode(1, 2))).toEqual('1 x 2');
    });
  });

  describe('PositionFormatter', () => {
    it('translates position correctly', () => {
      expect(POSITION_FORMATTER.format(TreeNodeUtils.makePositionNode(1, 2))).toEqual('x: 1, y: 2');
    });
  });

  describe('RegionFormatter', () => {
    it('translates region correctly', () => {
      const region = new PropertyTreeBuilder()
        .setRootId('test node')
        .setName('region')
        .setChildren([{name: 'rect', value: []}])
        .build();

      const rectNode = assertDefined(region.getChildByName('rect'));
      rectNode.addOrReplaceChild(TreeNodeUtils.makeRectNode(0, 0, 1080, 2340));

      expect(REGION_FORMATTER.format(region)).toEqual('SkRegion((0, 0, 1080, 2340))');
    });
  });
});