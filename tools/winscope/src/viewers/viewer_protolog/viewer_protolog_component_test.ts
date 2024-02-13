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
import {CdkVirtualScrollViewport, ScrollingModule} from '@angular/cdk/scrolling';
import {CUSTOM_ELEMENTS_SCHEMA, NO_ERRORS_SCHEMA} from '@angular/core';
import {ComponentFixture, ComponentFixtureAutoDetect, TestBed} from '@angular/core/testing';
import {FormsModule} from '@angular/forms';
import {MatFormFieldModule} from '@angular/material/form-field';
import {MatInputModule} from '@angular/material/input';
import {MatSelectModule} from '@angular/material/select';
import {BrowserAnimationsModule} from '@angular/platform-browser/animations';
import {assertDefined} from 'common/assert_utils';
import {executeScrollComponentTests} from 'viewers/common/scroll_component_test_utils';
import {Events} from './events';
import {ProtologScrollDirective} from './scroll_strategy/protolog_scroll_directive';
import {UiData, UiDataMessage} from './ui_data';
import {ViewerProtologComponent} from './viewer_protolog_component';

describe('ViewerProtologComponent', () => {
  describe('Main component', () => {
    let fixture: ComponentFixture<ViewerProtologComponent>;
    let component: ViewerProtologComponent;
    let htmlElement: HTMLElement;

    beforeEach(async () => {
      await TestBed.configureTestingModule({
        providers: [{provide: ComponentFixtureAutoDetect, useValue: true}],
        imports: [
          ScrollingModule,
          MatFormFieldModule,
          FormsModule,
          MatInputModule,
          BrowserAnimationsModule,
          MatSelectModule,
        ],
        declarations: [ViewerProtologComponent, ProtologScrollDirective],
        schemas: [CUSTOM_ELEMENTS_SCHEMA, NO_ERRORS_SCHEMA],
      }).compileComponents();
      fixture = TestBed.createComponent(ViewerProtologComponent);
      component = fixture.componentInstance;
      htmlElement = fixture.nativeElement;
    });

    it('can be created', () => {
      expect(component).toBeTruthy();
    });

    it('creates message filters', () => {
      expect(htmlElement.querySelector('.filters .log-level')).toBeTruthy();
      expect(htmlElement.querySelector('.filters .tag')).toBeTruthy();
      expect(htmlElement.querySelector('.filters .source-file')).toBeTruthy();
      expect(htmlElement.querySelector('.filters .text')).toBeTruthy();
    });

    it('renders log messages', () => {
      expect(htmlElement.querySelector('.scroll-messages')).toBeTruthy();
    });

    it('applies text filters correctly', () => {
      htmlElement.addEventListener(Events.SearchStringFilterChanged, (event) => {
        component.uiData.messages = component.uiData.messages.filter((message) =>
          message.text.includes((event as CustomEvent).detail)
        );
      });
      component.inputData = makeUiData();
      fixture.detectChanges();
      expect(component.uiData.messages.length).toEqual(200);

      const textFilterDiv = assertDefined(htmlElement.querySelector('.filters .text'));
      const inputEl = assertDefined(textFilterDiv.querySelector('input')) as HTMLInputElement;
      inputEl.value = 'keep';
      inputEl.dispatchEvent(new Event('input'));
      fixture.detectChanges();
      expect(component.uiData.messages.length).toEqual(100);
    });

    it('scrolls to current entry on button click', () => {
      component.inputData = makeUiData();
      fixture.detectChanges();
      const goToCurrentTimeButton = assertDefined(
        htmlElement.querySelector('.go-to-current-time')
      ) as HTMLButtonElement;
      const spy = spyOn(assertDefined(component.scrollComponent), 'scrollToIndex');
      goToCurrentTimeButton.click();
      expect(spy).toHaveBeenCalledWith(150);
    });
  });

  describe('Scroll component', () => {
    executeScrollComponentTests('message', setUpTestEnvironment);
    async function setUpTestEnvironment(): Promise<
      [ComponentFixture<ViewerProtologComponent>, HTMLElement, CdkVirtualScrollViewport]
    > {
      await TestBed.configureTestingModule({
        providers: [{provide: ComponentFixtureAutoDetect, useValue: true}],
        imports: [ScrollingModule],
        declarations: [ViewerProtologComponent, ProtologScrollDirective],
        schemas: [CUSTOM_ELEMENTS_SCHEMA, NO_ERRORS_SCHEMA],
      }).compileComponents();
      const fixture = TestBed.createComponent(ViewerProtologComponent);
      const protologComponent = fixture.componentInstance;
      const htmlElement = fixture.nativeElement;
      const viewport = assertDefined(protologComponent.scrollComponent);
      protologComponent.inputData = makeUiData();
      return [fixture, htmlElement, viewport];
    }
  });

  function makeUiData(): UiData {
    const allLogLevels = ['INFO', 'ERROR'];
    const allTags = ['WindowManager', 'INVALID'];
    const allSourceFiles = ['test_source_file.java', 'other_test_source_file.java'];

    const messages = [];
    const shortMessage = 'test information about message';
    const longMessage = shortMessage.repeat(10) + 'keep';
    for (let i = 0; i < 200; i++) {
      const uiDataMessage: UiDataMessage = {
        originalIndex: i,
        text: i % 2 === 0 ? shortMessage : longMessage,
        time: '2022-11-21T18:05:09.777144978',
        tag: i % 2 === 0 ? allTags[0] : allTags[1],
        level: i % 2 === 0 ? allLogLevels[0] : allLogLevels[1],
        at: i % 2 === 0 ? allSourceFiles[0] : allSourceFiles[1],
      };
      messages.push(uiDataMessage);
    }
    return new UiData(allLogLevels, allTags, allSourceFiles, messages, 150);
  }
});
