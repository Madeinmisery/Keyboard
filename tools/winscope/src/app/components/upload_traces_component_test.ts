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
import {ComponentFixture, TestBed} from '@angular/core/testing';
import {MatCardModule} from '@angular/material/card';
import {MatIconModule} from '@angular/material/icon';
import {MatListModule} from '@angular/material/list';
import {MatProgressBarModule} from '@angular/material/progress-bar';
import {MatSnackBar, MatSnackBarModule} from '@angular/material/snack-bar';
import {TracePipeline} from 'app/trace_pipeline';
import {UnitTestUtils} from 'test/unit/utils';
import {LoadProgressComponent} from './load_progress_component';
import {UploadTracesComponent} from './upload_traces_component';

describe('UploadTracesComponent', () => {
  let fixture: ComponentFixture<UploadTracesComponent>;
  let component: UploadTracesComponent;
  let htmlElement: HTMLElement;
  let validSfFile: File;
  let validWmFile: File;

  beforeEach(async () => {
    await TestBed.configureTestingModule({
      imports: [
        MatCardModule,
        MatSnackBarModule,
        MatListModule,
        MatIconModule,
        MatProgressBarModule,
      ],
      providers: [MatSnackBar],
      declarations: [UploadTracesComponent, LoadProgressComponent],
    }).compileComponents();
    fixture = TestBed.createComponent(UploadTracesComponent);
    component = fixture.componentInstance;
    htmlElement = fixture.nativeElement;
    component.tracePipeline = new TracePipeline();
    validSfFile = await UnitTestUtils.getFixtureFile(
      'traces/elapsed_and_real_timestamp/SurfaceFlinger.pb'
    );
    validWmFile = await UnitTestUtils.getFixtureFile(
      'traces/elapsed_and_real_timestamp/WindowManager.pb'
    );
    fixture.detectChanges();
  });

  it('can be created', () => {
    expect(component).toBeTruthy();
  });

  it('renders the expected card title', () => {
    expect(htmlElement.querySelector('.title')?.innerHTML).toContain('Upload Traces');
  });

  it('handles file upload via drag and drop', () => {
    const spy = spyOn(component.filesUploaded, 'emit');
    const dropbox = htmlElement.querySelector('.drop-box');
    expect(dropbox).toBeTruthy();

    const dataTransfer = new DataTransfer();
    dataTransfer.items.add(validSfFile);
    dropbox?.dispatchEvent(new DragEvent('drop', {dataTransfer}));
    fixture.detectChanges();
    expect(spy).toHaveBeenCalledWith(Array.from(dataTransfer.files));
  });

  it('displays load progress bar', () => {
    component.isLoadingFiles = true;
    fixture.detectChanges();
    const progressBar = htmlElement.querySelector('load-progress');
    expect(progressBar).toBeTruthy();
  });

  it('can display uploaded traces', async () => {
    await component.tracePipeline.loadFiles([validSfFile]);
    fixture.detectChanges();
    const uploadedTracesDiv = htmlElement.querySelector('.uploaded-files');
    expect(uploadedTracesDiv).toBeTruthy();
    const traceActionsDiv = htmlElement.querySelector('.trace-actions-container');
    expect(traceActionsDiv).toBeTruthy();
  });

  it('can remove one of two uploaded traces', async () => {
    await component.tracePipeline.loadFiles([validSfFile, validWmFile]);
    fixture.detectChanges();
    expect(component.tracePipeline.getTraces().getSize()).toBe(2);

    const spy = spyOn(component, 'onOperationFinished');
    const removeButton = htmlElement.querySelector('.uploaded-files button');
    (removeButton as HTMLButtonElement)?.click();
    fixture.detectChanges();
    const uploadedTracesDiv = htmlElement.querySelector('.uploaded-files');
    expect(uploadedTracesDiv).toBeTruthy();
    expect(spy).toHaveBeenCalled();
    expect(component.tracePipeline.getTraces().getSize()).toBe(1);
  });

  it('handles removal of the only uploaded trace', async () => {
    await component.tracePipeline.loadFiles([validSfFile]);
    fixture.detectChanges();

    const spy = spyOn(component, 'onOperationFinished');
    const removeButton = htmlElement.querySelector('.uploaded-files button');
    (removeButton as HTMLButtonElement)?.click();
    fixture.detectChanges();
    const dropInfo = htmlElement.querySelector('.drop-info');
    expect(dropInfo).toBeTruthy();
    expect(spy).toHaveBeenCalled();
    expect(component.tracePipeline.getTraces().getSize()).toBe(0);
  });

  it('can remove all uploaded traces', async () => {
    await component.tracePipeline.loadFiles([validSfFile, validWmFile]);
    fixture.detectChanges();
    expect(component.tracePipeline.getTraces().getSize()).toBe(2);

    const spy = spyOn(component, 'onOperationFinished');
    const clearAllButton = htmlElement.querySelector('.clear-all-btn');
    (clearAllButton as HTMLButtonElement).click();
    fixture.detectChanges();
    const dropInfo = htmlElement.querySelector('.drop-info');
    expect(dropInfo).toBeTruthy();
    expect(spy).toHaveBeenCalled();
    expect(component.tracePipeline.getTraces().getSize()).toBe(0);
  });

  it('can triggers view traces event', async () => {
    await component.tracePipeline.loadFiles([validSfFile]);
    fixture.detectChanges();

    const spy = spyOn(component.viewTracesButtonClick, 'emit');
    const viewTracesButton = htmlElement.querySelector('.load-btn');
    (viewTracesButton as HTMLButtonElement).click();
    fixture.detectChanges();
    expect(spy).toHaveBeenCalled();
  });
});