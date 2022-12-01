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
import { PersistentStore } from "common/utils/persistent_store";
import { configMap, TRACES } from "./trace_collection_utils";
import { setTraces, SetTraces } from "./set_traces";
import { Device } from "./connection";
import { ProxyConnection } from "./proxy_connection";

export enum ProxyState {
  ERROR = 0,
  CONNECTING = 1,
  NO_PROXY = 2,
  INVALID_VERSION = 3,
  UNAUTH = 4,
  DEVICES = 5,
  START_TRACE = 6,
  END_TRACE = 7,
  LOAD_DATA = 8,
}

export enum ProxyEndpoint {
  DEVICES = "/devices/",
  START_TRACE = "/start/",
  END_TRACE = "/end/",
  ENABLE_CONFIG_TRACE = "/configtrace/",
  SELECTED_WM_CONFIG_TRACE = "/selectedwmconfigtrace/",
  SELECTED_SF_CONFIG_TRACE = "/selectedsfconfigtrace/",
  DUMP = "/dump/",
  FETCH = "/fetch/",
  STATUS = "/status/",
  CHECK_WAYLAND = "/checkwayland/",
}

// from here, all requests to the proxy are made
class ProxyRequest {
  async call(
    method: string,
    path: string,
    onSuccess: ((request: XMLHttpRequest) => void) | undefined,
    type?: XMLHttpRequestResponseType,
    jsonRequest: any = null
  ) {
    const request = new XMLHttpRequest();
    const client = proxyClient;
    request.onreadystatechange = function() {
      if (this.readyState !== 4) {
        return;
      }
      if (this.status === 0) {
        client.setState(ProxyState.NO_PROXY);
      } else if (this.status === 200) {
        if (this.getResponseHeader("Winscope-Proxy-Version") !== client.VERSION) {
          client.setState(ProxyState.INVALID_VERSION);
        } else if (onSuccess) {
          try {
            onSuccess(this);
          } catch(err) {
            console.error(err);
            proxyClient.setState(ProxyState.ERROR,
              `Error handling request response:\n${err}\n\n`+
              `Request:\n ${request.responseText}`);
          }
        }
      } else if (this.status === 403) {
        client.setState(ProxyState.UNAUTH);
      } else {
        if (this.responseType === "text" || !this.responseType) {
          client.errorText = this.responseText;
        } else if (this.responseType === "arraybuffer") {
          client.errorText = String.fromCharCode.apply(null, new Array(this.response));
        }
        client.setState(ProxyState.ERROR, client.errorText);
      }
    };
    request.responseType = type || "";
    request.open(method, client.WINSCOPE_PROXY_URL + path);
    const lastKey = client.store.get("adb.proxyKey");
    if (lastKey !== null) {
      client.proxyKey = lastKey;
    }
    request.setRequestHeader("Winscope-Token", client.proxyKey);
    if (jsonRequest) {
      const json = JSON.stringify(jsonRequest);
      request.setRequestHeader("Content-Type", "application/json;charset=UTF-8");
      request.send(json);
    } else {
      request.send();
    }
  }

  getDevices(view:any) {
    proxyRequest.call("GET", ProxyEndpoint.DEVICES, proxyRequest.onSuccessGetDevices);
  }

  async fetchFiles(dev:string, files: Array<string>, idx: number, view:any) {
    await proxyRequest.call("GET", `${ProxyEndpoint.FETCH}${dev}/${files[idx]}/`,
      (request) => proxyRequest.onSuccessUpdateAdbData(request, view), "arraybuffer");
  }

  setEnabledConfig(view:any, req: Array<string>) {
    proxyRequest.call("POST", `${ProxyEndpoint.ENABLE_CONFIG_TRACE}${view.proxy.selectedDevice}/`, undefined, undefined, req);
  }

  setSelectedConfig(endpoint: ProxyEndpoint, view:any, req: configMap) {
    proxyRequest.call("POST", `${endpoint}${view.proxy.selectedDevice}/`, undefined, undefined, req);
  }

  startTrace(view:any) {
    proxyRequest.call("POST", `${ProxyEndpoint.START_TRACE}${view.proxy.selectedDevice}/`, (request:XMLHttpRequest) => {
      view.keepAliveTrace(view);
    }, undefined, setTraces.reqTraces);
  }

  async endTrace(view:any) {
    await proxyRequest.call("POST", `${ProxyEndpoint.END_TRACE}${view.proxy.selectedDevice}/`,
      async (request:XMLHttpRequest) => {
        await proxyClient.updateAdbData(setTraces.reqTraces, 0, "trace", view);
      });
  }

  keepTraceAlive(view:any) {
    this.call("GET", `${ProxyEndpoint.STATUS}${view.proxy.selectedDevice}/`, (request: XMLHttpRequest) => {
      if (request.responseText !== "True") {
        view.endTrace();
      } else if (view.keep_alive_worker === null) {
        view.keep_alive_worker = setInterval(view.keepAliveTrace, 1000, view);
      }
    });
  }

  async dumpState(view:any) {
    await proxyRequest.call("POST", `${ProxyEndpoint.DUMP}${view.proxy.selectedDevice}/`,
      async (request:XMLHttpRequest) => {
        await proxyClient.updateAdbData(setTraces.reqDumps, 0, "dump", view);
      }, undefined, setTraces.reqDumps);
  }

  onSuccessGetDevices = function(request: XMLHttpRequest) {
    const client = proxyClient;
    try {
      client.devices = JSON.parse(request.responseText);
      const last = client.store.get("adb.lastDevice");
      if (last && client.devices[last] &&
              client.devices[last].authorised) {
        client.selectDevice(last);
      } else {
        if (client.refresh_worker === null) {
          client.refresh_worker = setInterval(client.getDevices, 1000);
        }
        client.setState(ProxyState.DEVICES);
      }
    } catch (err) {
      console.error(err);
      client.errorText = request.responseText;
      client.setState(ProxyState.ERROR, client.errorText);
    }
  };

  onSuccessUpdateAdbData = async (request: XMLHttpRequest, view: ProxyConnection) => {
    const idx = proxyClient.adbParams.idx;
    const files = proxyClient.adbParams.files;
    const traceType = proxyClient.adbParams.traceType;
    try {
      const enc = new TextDecoder("utf-8");
      const resp = enc.decode(request.response);
      const filesByType = JSON.parse(resp);

      for (const filetype in filesByType) {
        const files = filesByType[filetype];
        for (const encodedFileBuffer of files) {
          const buffer = Uint8Array.from(atob(encodedFileBuffer), (c) => c.charCodeAt(0));
          const blob = new Blob([buffer]);
          const newFile = new File([blob], filetype);
          proxyClient.adbData.push(newFile);
        }
      }
      if (idx < files.length - 1) {
        proxyClient.updateAdbData(files, idx + 1, traceType, view);
      } else {
        setTraces.dataReady = true;
      }
    } catch (error) {
      proxyClient.setState(ProxyState.ERROR, request.responseText);
    }
  };
}
export const proxyRequest = new ProxyRequest();

interface AdbParams {
  files: Array<string>,
  idx: number,
  traceType: string
}

// stores all the changing variables from proxy and sets up calls from ProxyRequest
export class ProxyClient {
  readonly WINSCOPE_PROXY_URL = "http://localhost:5544";
  readonly VERSION = "0.8";
  state: ProxyState = ProxyState.CONNECTING;
  stateChangeListeners: {(param:ProxyState, errorText:string): void;}[] = [];
  refresh_worker: NodeJS.Timer | null = null;
  devices: Device = {};
  selectedDevice = "";
  errorText = "";
  adbData: Array<File> = [];
  proxyKey = "";
  lastDevice = "";
  store = new PersistentStore();
  adbParams: AdbParams = {
    files: [],
    idx: -1,
    traceType: "",
  };

  setState(state:ProxyState, errorText = "") {
    this.state = state;
    this.errorText = errorText;
    for (const listener of this.stateChangeListeners) {
      listener(state, errorText);
    }
  }

  onProxyChange(fn: (state:ProxyState, errorText:string) => void) {
    this.removeOnProxyChange(fn);
    this.stateChangeListeners.push(fn);
  }

  removeOnProxyChange(removeFn: (state:ProxyState, errorText:string) => void) {
    this.stateChangeListeners = this.stateChangeListeners.filter(fn => fn !== removeFn);
  }

  getDevices() {
    if (this.state !== ProxyState.DEVICES && this.state !== ProxyState.CONNECTING) {
      clearInterval(this.refresh_worker!);
      this.refresh_worker = null;
      return;
    }
    proxyRequest.getDevices(this);
  }

  selectDevice(device_id: string) {
    this.selectedDevice = device_id;
    this.store.add("adb.lastDevice", device_id);
    this.setState(ProxyState.START_TRACE);
  }

  async updateAdbData(files:Array<string>, idx:number, traceType:string, view: ProxyConnection) {
    this.adbParams.files = files;
    this.adbParams.idx = idx;
    this.adbParams.traceType = traceType;
    await proxyRequest.fetchFiles(this.selectedDevice, files, idx, view);
  }
}

export const proxyClient = new ProxyClient();
