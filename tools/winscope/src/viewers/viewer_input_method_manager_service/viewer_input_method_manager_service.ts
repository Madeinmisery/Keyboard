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
import {TraceType} from 'trace/trace_type';
import {ViewerInputMethod} from 'viewers/common/viewer_input_method';
import {View, ViewType} from 'viewers/viewer';
import {PresenterInputMethodManagerService} from './presenter_input_method_manager_service';

class ViewerInputMethodManagerService extends ViewerInputMethod {
  override getViews(): View[] {
    return [
      new View(
        ViewType.TAB,
        this.getDependencies(),
        this.htmlElement,
        'Input Method Manager Service'
      ),
    ];
  }

  override getDependencies(): TraceType[] {
    return ViewerInputMethodManagerService.DEPENDENCIES;
  }

  override initialisePresenter(storage: Storage) {
    return new PresenterInputMethodManagerService(
      this.imeUiCallback,
      this.getDependencies(),
      storage
    );
  }

  static readonly DEPENDENCIES: TraceType[] = [TraceType.INPUT_METHOD_MANAGER_SERVICE];
}

export {ViewerInputMethodManagerService};
