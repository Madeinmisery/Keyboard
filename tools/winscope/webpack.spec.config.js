/*
 * Copyright 2017, The Android Open Source Project
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

const fs = require('fs');
var path = require('path')
var glob = require("glob");

function getWaylandSafePath() {
  waylandPath = path.resolve(__dirname, '../../../vendor/google_arc/libs/wayland_service');
  if (fs.existsSync(waylandPath)) {
    return waylandPath;
  }
  return path.resolve(__dirname, 'src/stubs');
}

module.exports = {
  entry: {
    js: glob.sync("./spec/**/*Spec.js"),
  },
  output: {
    path: path.resolve(__dirname, './dist'),
    filename: 'bundleSpec.js'
  },
  target: 'node',
  node: {
    __dirname: false,
  },
  module: {
    rules: [
      {
        test: /\.js$/,
        loader: 'babel-loader',
        exclude: /node_modules/
      },
      {
        test: /\.proto$/,
        loader: 'proto-loader',
        options: {
          paths: [
            path.resolve(__dirname, '../../..'),
            path.resolve(__dirname, '../../../external/protobuf/src')
          ]
        }
      },
      {
        test: /\.pb/,
        loader: 'file-loader',
        options: {
          paths: [
            path.resolve(__dirname, './spec')
          ]
        }
      },
    ]
  },
  resolve: {
    alias: {
      WaylandSafePath: getWaylandSafePath(),
    },
    modules: [
      'node_modules',
      path.resolve(__dirname, '../../..')
    ],
  },
  resolveLoader: {
    modules: [
      'node_modules',
      path.resolve(__dirname, 'loaders')
    ]
  },
  devServer: {
    historyApiFallback: true,
    noInfo: true
  },
  performance: {
    hints: false
  }
}
