/*
 * Copyright 2022, The Android Open Source Project
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
import {ProxyClient} from 'trace_collection/proxy_client';
import {configMap} from './trace_collection_utils';

export interface Device {
  [key: string]: DeviceProperties;
}

export interface DeviceProperties {
  authorised: boolean;
  model: string;
}

export interface Connection {
  adbSuccess: () => boolean;
  setProxyKey?(key: string): any;
  devices(): Device;
  selectedDevice(): DeviceProperties;
  selectedDeviceId(): string;
  restart(): any;
  selectDevice(id: string): any;
  state(): any;
  onConnectChange(newState: any): any;
  resetLastDevice(): any;
  isDevicesState(): boolean;
  isStartTraceState(): boolean;
  isErrorState(): boolean;
  isEndTraceState(): boolean;
  isLoadDataState(): boolean;
  isConnectingState(): boolean;
  throwNoTargetsError(): any;
  startTrace(
    reqEnableConfig?: Array<string>,
    reqSelectedSfConfig?: configMap,
    reqSelectedWmConfig?: configMap
  ): any;
  endTrace(): any;
  adbData(): Array<File>;
  dumpState(): any;
  proxy?: ProxyClient;
}
