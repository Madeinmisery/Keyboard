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
import {ComponentFixture, TestBed} from "@angular/core/testing";
import { TreeComponent } from "./tree.component";
import { ComponentFixtureAutoDetect } from "@angular/core/testing";
import { NO_ERRORS_SCHEMA } from "@angular/core";

describe("TreeComponent", () => {
  let fixture: ComponentFixture<TreeComponent>;
  let component: TreeComponent;
  let htmlElement: HTMLElement;

  beforeAll(async () => {
    await TestBed.configureTestingModule({
      providers: [
        { provide: ComponentFixtureAutoDetect, useValue: true }
      ],
      declarations: [
        TreeComponent
      ],
      schemas: [NO_ERRORS_SCHEMA]
    }).compileComponents();
  });

  beforeEach(() => {
    fixture = TestBed.createComponent(TreeComponent);
    component = fixture.componentInstance;
    htmlElement = fixture.nativeElement;
    component.isFlattened = true;
    component.item = {
      simplifyNames: false,
      kind: "entry",
      name: "BaseLayerTraceEntry",
      shortName: "BLTE",
      chips: [],
      children: [{kind: "3", id: "3", name: "Child1"}]
    };
    component.diffClass = jasmine.createSpy().and.returnValue("none");
    component.isHighlighted = jasmine.createSpy().and.returnValue(false);
    component.hasChildren = jasmine.createSpy().and.returnValue(true);
  });

  it("can be created", () => {
    fixture.detectChanges();
    expect(component).toBeTruthy();
  });

  it("creates node element", () => {
    fixture.detectChanges();
    const nodeElement = htmlElement.querySelector(".node");
    expect(nodeElement).toBeTruthy();
  });
});
