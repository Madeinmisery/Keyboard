/*
 * Copyright (C) 2014 The Android Open Source Project
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

package com.android.testing.mockime.tests;

import com.android.testing.mockime.SoftKeyboard;

import android.os.Handler;
import android.text.InputType;
import android.view.KeyEvent;

import java.util.Collection;
import java.util.LinkedList;

/**
 * Class that tests number of candidate window based input systems like katakana, romaji, etc.
 *
 */
public class CandidateBasedInputTest extends BaseTestCase {

  /**
   * Default constructor.
   */
  public CandidateBasedInputTest(SoftKeyboard keyboard, Handler handler) {
    super(keyboard, handler);
    notSupportedFieldTypes.add(InputType.TYPE_CLASS_PHONE);
    notSupportedFieldTypes.add(InputType.TYPE_CLASS_NUMBER);
    notSupportedFieldTypes.add(InputType.TYPE_CLASS_DATETIME);
  }

  @Override
  public void runTheTest(final TestRunCallback callback, int fieldType) {
    keyboard.setmCompletionOn(true);
    Thread thread = new Thread(new Runnable() {
      @Override
      public void run() {
        clearInputField();

        simulateCharacterClick(KeyEvent.KEYCODE_T);
        simulateCharacterClick(KeyEvent.KEYCODE_O);
        simulateCharacterClick(KeyEvent.KEYCODE_U);
        simulateCharacterClick(KeyEvent.KEYCODE_K);
        simulateCharacterClick(KeyEvent.KEYCODE_Y);
        simulateCharacterClick(KeyEvent.KEYCODE_O);
        simulateCharacterClick(KeyEvent.KEYCODE_U);

        Collection<String> result = new LinkedList<String>();
        if (!"toukyou".equalsIgnoreCase(keyboard.getmComposing().toString())) {
          result.add("Simple IME buffer test failed. Buffer contains " + "unexpected value in it.");
        }
        runSynchronously(new SyncRunnable() {
          @Override
          protected void realRun() {
            keyboard.pickSuggestionManually(1);
          }
        });

        String internal = getCurrentTextInTheEditor().trim();
        if (!"とうきょう".equals(internal)) {
          result.add("Input with candidate selection failed. Part of the buffer was received "
              + " along with the selected candidate. The output received was '" + internal
              + "' instead of 'とうきょう'. "
              + "This may happen if the input was committed prematurely.");
        }
        clearInputField();

        callback.onTestComplete(result);
      }
    });
    thread.start();
  }

  @Override
  public String getTestExplanation() {
    return "Test that checks the buffer based input, when user"
        + " is typing some English letters and selecting a candidate.";
  }


}
