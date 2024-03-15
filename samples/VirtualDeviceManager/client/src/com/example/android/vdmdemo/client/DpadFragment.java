/*
 * Copyright (C) 2023 The Android Open Source Project
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

package com.example.android.vdmdemo.client;

import android.annotation.SuppressLint;
import android.os.Bundle;
import android.util.Log;
import android.view.KeyEvent;
import android.view.LayoutInflater;
import android.view.MotionEvent;
import android.view.View;
import android.view.ViewGroup;
import android.widget.ImageButton;

import androidx.fragment.app.Fragment;

import com.example.android.vdmdemo.common.RemoteEventProto.InputDeviceType;

import dagger.hilt.android.AndroidEntryPoint;

import javax.inject.Inject;

/** Fragment to show UI for a Dpad. */
@AndroidEntryPoint(Fragment.class)
public final class DpadFragment extends Hilt_DpadFragment {
    private static final String TAG = "DpadFragment";

    private static final int[] BUTTONS = {
        R.id.dpad_center, R.id.dpad_down, R.id.dpad_left, R.id.dpad_up, R.id.dpad_right
    };

    @Inject InputManager mInputManager;

    @SuppressLint("ClickableViewAccessibility")
    @Override
    public View onCreateView(
            LayoutInflater layoutInflater, ViewGroup parent, Bundle savedInstanceState) {
        View view = layoutInflater.inflate(R.layout.fragment_dpad, parent, false);

        // Set the callback for all the buttons
        // Note: the onClick XML attribute cannot be used with fragments, only activities.
        for (int buttonId : BUTTONS) {
            ImageButton button = view.requireViewById(buttonId);
            button.setOnTouchListener(this::onDpadButtonClick);
        }

        return view;
    }

    private boolean onDpadButtonClick(View v, MotionEvent e) {
        int action;
        if (e.getAction() == MotionEvent.ACTION_DOWN) {
            action = KeyEvent.ACTION_DOWN;
        } else if (e.getAction() == MotionEvent.ACTION_UP) {
            action = KeyEvent.ACTION_UP;
        } else {
            return false;
        }

        int keyCode;
        int id = v.getId();
        if (id == R.id.dpad_center) {
            keyCode = KeyEvent.KEYCODE_DPAD_CENTER;
        } else if (id == R.id.dpad_down) {
            keyCode = KeyEvent.KEYCODE_DPAD_DOWN;
        } else if (id == R.id.dpad_left) {
            keyCode = KeyEvent.KEYCODE_DPAD_LEFT;
        } else if (id == R.id.dpad_up) {
            keyCode = KeyEvent.KEYCODE_DPAD_UP;
        } else if (id == R.id.dpad_right) {
            keyCode = KeyEvent.KEYCODE_DPAD_RIGHT;
        } else {
            Log.w(TAG, "onDpadButtonClick: Method called from a non Dpad button");
            return false;
        }
        mInputManager.sendInputEventToFocusedDisplay(
                InputDeviceType.DEVICE_TYPE_DPAD,
                new KeyEvent(
                        /* downTime= */ System.currentTimeMillis(),
                        /* eventTime= */ System.currentTimeMillis(),
                        action,
                        keyCode,
                        /* repeat= */ 0));
        return true;
    }
}
