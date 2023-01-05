import {StoreObject} from 'common/persistent_store_proxy';

export type TraceConfiguration = {
  [key: string]: string | boolean | undefined | StoreObject;
  name: string | undefined;
  run: boolean | undefined;
  isTraceCollection: boolean | undefined;
  config: ConfigurationOptions | undefined;
};

export type TraceConfigurationMap = {
  [key: string]: TraceConfiguration;
};

type ConfigurationOptions = {
  [key: string]: string | boolean | undefined | StoreObject;
  enableConfigs: EnableConfiguration[];
  selectionConfigs: SelectionConfiguration[];
};

export type EnableConfiguration = {
  name: string;
  key: string;
  enabled: boolean;
};

export type SelectionConfiguration = {
  key: string;
  name: string;
  options: string[];
  value: string;
};

export type configMap = {
  [key: string]: string[] | string;
};

const wmTraceSelectionConfigs: Array<SelectionConfiguration> = [
  {
    key: 'wmbuffersize',
    name: 'buffer size (KB)',
    options: ['4000', '8000', '16000', '32000'],
    value: '32000',
  },
  {
    key: 'tracingtype',
    name: 'tracing type',
    options: ['frame', 'transaction'],
    value: 'frame',
  },
  {
    key: 'tracinglevel',
    name: 'tracing level',
    options: ['verbose', 'debug', 'critical'],
    value: 'verbose',
  },
];

const sfTraceEnableConfigs: Array<EnableConfiguration> = [
  {
    name: 'input',
    key: 'input',
    enabled: true,
  },
  {
    name: 'composition',
    key: 'composition',
    enabled: true,
  },
  {
    name: 'metadata',
    key: 'metadata',
    enabled: false,
  },
  {
    name: 'hwc',
    key: 'hwc',
    enabled: true,
  },
  {
    name: 'trace buffers',
    key: 'tracebuffers',
    enabled: true,
  },
  {
    name: 'virtual displays',
    key: 'virtualdisplays',
    enabled: false,
  },
];

const sfTraceSelectionConfigs: Array<SelectionConfiguration> = [
  {
    key: 'sfbuffersize',
    name: 'buffer size (KB)',
    options: ['4000', '8000', '16000', '32000'],
    value: '32000',
  },
];

export const traceConfigurations: TraceConfigurationMap = {
  layers_trace: {
    name: 'Surface Flinger',
    run: true,
    isTraceCollection: undefined,
    config: {
      enableConfigs: sfTraceEnableConfigs,
      selectionConfigs: sfTraceSelectionConfigs,
    },
  },
  window_trace: {
    name: 'Window Manager',
    run: true,
    isTraceCollection: undefined,
    config: {
      enableConfigs: [],
      selectionConfigs: wmTraceSelectionConfigs,
    },
  },
  screen_recording: {
    name: 'Screen Recording',
    isTraceCollection: undefined,
    run: true,
    config: undefined,
  },
  ime_tracing: {
    name: 'IME Tracing',
    run: true,
    isTraceCollection: true,
    config: {
      enableConfigs: [
        {
          name: 'Input Method Clients',
          key: 'ime_trace_clients',
          enabled: true,
        },
        {
          name: 'Input Method Service',
          key: 'ime_trace_service',
          enabled: true,
        },
        {
          name: 'Input Method Manager Service',
          key: 'ime_trace_managerservice',
          enabled: true,
        },
      ],
      selectionConfigs: [],
    },
  },
  ime_trace_clients: {
    name: 'Input Method Clients',
    isTraceCollection: undefined,
    run: true,
    config: undefined,
  },
  ime_trace_service: {
    name: 'Input Method Service',
    isTraceCollection: undefined,
    run: true,
    config: undefined,
  },
  ime_trace_managerservice: {
    name: 'Input Method Manager Service',
    isTraceCollection: undefined,
    run: true,
    config: undefined,
  },
  accessibility_trace: {
    name: 'Accessibility',
    isTraceCollection: undefined,
    run: false,
    config: undefined,
  },
  transactions: {
    name: 'Transaction',
    isTraceCollection: undefined,
    run: false,
    config: undefined,
  },
  proto_log: {
    name: 'ProtoLog',
    isTraceCollection: undefined,
    run: false,
    config: undefined,
  },
  wayland_trace: {
    name: 'Wayland',
    isTraceCollection: undefined,
    run: false,
    config: undefined,
  },
};

export const TRACES: {[key: string]: TraceConfigurationMap} = {
  default: {
    window_trace: traceConfigurations['window_trace'],
    accessibility_trace: traceConfigurations['accessibility_trace'],
    layers_trace: traceConfigurations['layers_trace'],
    transactions: traceConfigurations['transactions'],
    proto_log: traceConfigurations['proto_log'],
    screen_recording: traceConfigurations['screen_recording'],
    ime_tracing: traceConfigurations['ime_tracing'],
  },
  arc: {
    wayland_trace: traceConfigurations['wayland_trace'],
  },
};
