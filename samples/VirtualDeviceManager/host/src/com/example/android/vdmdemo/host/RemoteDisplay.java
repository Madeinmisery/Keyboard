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

package com.example.android.vdmdemo.host;

import android.annotation.SuppressLint;
import android.app.ActivityOptions;
import android.app.PendingIntent;
import android.companion.virtual.VirtualDeviceManager;
import android.companion.virtual.VirtualDeviceManager.VirtualDevice;
import android.content.Context;
import android.content.Intent;
import android.graphics.Point;
import android.graphics.PointF;
import android.hardware.display.DisplayManager;
import android.hardware.display.VirtualDisplay;
import android.hardware.display.VirtualDisplayConfig;
import android.hardware.input.VirtualDpad;
import android.hardware.input.VirtualDpadConfig;
import android.hardware.input.VirtualKeyEvent;
import android.hardware.input.VirtualKeyboard;
import android.hardware.input.VirtualKeyboardConfig;
import android.hardware.input.VirtualMouse;
import android.hardware.input.VirtualMouseButtonEvent;
import android.hardware.input.VirtualMouseConfig;
import android.hardware.input.VirtualMouseRelativeEvent;
import android.hardware.input.VirtualMouseScrollEvent;
import android.hardware.input.VirtualNavigationTouchpad;
import android.hardware.input.VirtualNavigationTouchpadConfig;
import android.hardware.input.VirtualTouchEvent;
import android.hardware.input.VirtualTouchscreen;
import android.hardware.input.VirtualTouchscreenConfig;
import android.util.Log;
import android.view.Display;
import android.view.MotionEvent;
import android.view.Surface;

import androidx.annotation.IntDef;

import com.example.android.vdmdemo.common.RemoteEventProto.DisplayCapabilities;
import com.example.android.vdmdemo.common.RemoteEventProto.DisplayRotation;
import com.example.android.vdmdemo.common.RemoteEventProto.RemoteEvent;
import com.example.android.vdmdemo.common.RemoteEventProto.RemoteInputEvent;
import com.example.android.vdmdemo.common.RemoteEventProto.RemoteKeyEvent;
import com.example.android.vdmdemo.common.RemoteEventProto.RemoteMotionEvent;
import com.example.android.vdmdemo.common.RemoteEventProto.StopStreaming;
import com.example.android.vdmdemo.common.RemoteIo;
import com.example.android.vdmdemo.common.VideoManager;

import java.lang.annotation.Retention;
import java.lang.annotation.RetentionPolicy;
import java.util.concurrent.Executor;
import java.util.concurrent.atomic.AtomicBoolean;
import java.util.function.Consumer;

class RemoteDisplay implements AutoCloseable {

    private static final String TAG = "VdmHost";

    private static final int DISPLAY_FPS = 60;

    private static final int DEFAULT_VIRTUAL_DISPLAY_FLAGS =
            DisplayManager.VIRTUAL_DISPLAY_FLAG_TRUSTED
                    | DisplayManager.VIRTUAL_DISPLAY_FLAG_PUBLIC
                    | DisplayManager.VIRTUAL_DISPLAY_FLAG_OWN_CONTENT_ONLY;

    static final int DISPLAY_TYPE_APP = 0;
    static final int DISPLAY_TYPE_HOME = 1;
    static final int DISPLAY_TYPE_MIRROR = 2;
    @IntDef(value = {DISPLAY_TYPE_APP, DISPLAY_TYPE_HOME, DISPLAY_TYPE_MIRROR})
    @Retention(RetentionPolicy.SOURCE)
    public @interface DisplayType {}

    private final Context mContext;
    private final RemoteIo mRemoteIo;
    private final Settings mSettings;
    private final Consumer<RemoteEvent> mRemoteEventConsumer = this::processRemoteEvent;
    private final VirtualDisplay mVirtualDisplay;
    private final VirtualDpad mDpad;
    private final int mRemoteDisplayId;
    private final Executor mPendingIntentExecutor;
    private final VirtualDevice mVirtualDevice;
    private final @DisplayType int mDisplayType;
    private final AtomicBoolean mClosed = new AtomicBoolean(false);
    private int mRotation;
    private int mWidth;
    private int mHeight;
    private int mDpi;

    private VideoManager mVideoManager;
    private VirtualTouchscreen mTouchscreen;
    private VirtualMouse mMouse;
    private VirtualNavigationTouchpad mNavigationTouchpad;
    private VirtualKeyboard mKeyboard;

    @SuppressLint("WrongConstant")
    RemoteDisplay(
            Context context,
            RemoteEvent event,
            VirtualDevice virtualDevice,
            RemoteIo remoteIo,
            @DisplayType int displayType,
            Settings settings) {
        mContext = context;
        mRemoteIo = remoteIo;
        mRemoteDisplayId = event.getDisplayId();
        mVirtualDevice = virtualDevice;
        mPendingIntentExecutor = context.getMainExecutor();
        mDisplayType = displayType;
        mSettings = settings;

        setCapabilities(event.getDisplayCapabilities());

        int flags = DEFAULT_VIRTUAL_DISPLAY_FLAGS;
        if (settings.displayRotationEnabled) {
            flags |= DisplayManager.VIRTUAL_DISPLAY_FLAG_ROTATES_WITH_CONTENT;
        }
        if (mDisplayType == DISPLAY_TYPE_MIRROR) {
            flags &= ~DisplayManager.VIRTUAL_DISPLAY_FLAG_OWN_CONTENT_ONLY;
        }
        mVirtualDisplay =
                virtualDevice.createVirtualDisplay(
                        new VirtualDisplayConfig.Builder(
                                        "VirtualDisplay" + mRemoteDisplayId, mWidth, mHeight, mDpi)
                                .setFlags(flags)
                                .setHomeSupported(mDisplayType == DISPLAY_TYPE_HOME
                                        || mDisplayType == DISPLAY_TYPE_MIRROR)
                                .build(),
                        /* executor= */ Runnable::run,
                        /* callback= */ null);

        mDpad =
                virtualDevice.createVirtualDpad(
                        new VirtualDpadConfig.Builder()
                                .setAssociatedDisplayId(mVirtualDisplay.getDisplay().getDisplayId())
                                .setInputDeviceName("vdmdemo-dpad" + mRemoteDisplayId)
                                .build());

        remoteIo.addMessageConsumer(mRemoteEventConsumer);

        reset();
    }

    void reset(DisplayCapabilities capabilities) {
        setCapabilities(capabilities);
        mVirtualDisplay.resize(mWidth, mHeight, mDpi);
        reset();
    }

    private void reset() {
        if (mVideoManager != null) {
            mVideoManager.stop();
        }
        mVideoManager =
                VideoManager.createEncoder(
                        mRemoteDisplayId, mRemoteIo, mSettings.recordEncoderOutput);
        Surface surface = mVideoManager.createInputSurface(mWidth, mHeight, DISPLAY_FPS);
        mVirtualDisplay.setSurface(surface);

        mRotation = mVirtualDisplay.getDisplay().getRotation();

        if (mTouchscreen != null) {
            mTouchscreen.close();
        }
        mTouchscreen =
                mVirtualDevice.createVirtualTouchscreen(
                        new VirtualTouchscreenConfig.Builder(mWidth, mHeight)
                                .setAssociatedDisplayId(mVirtualDisplay.getDisplay().getDisplayId())
                                .setInputDeviceName("vdmdemo-touchscreen" + mRemoteDisplayId)
                                .build());

        mVideoManager.startEncoding();
    }

    private void setCapabilities(DisplayCapabilities capabilities) {
        mWidth = capabilities.getViewportWidth();
        mHeight = capabilities.getViewportHeight();
        mDpi = capabilities.getDensityDpi();

        // Video encoder needs round dimensions...
        mHeight -= mHeight % 10;
        mWidth -= mWidth % 10;
    }

    void launchIntent(PendingIntent intent) {
        mVirtualDevice.launchPendingIntent(
                mVirtualDisplay.getDisplay().getDisplayId(),
                intent,
                mPendingIntentExecutor,
                (result) -> {
                    switch (result) {
                        case VirtualDeviceManager.LAUNCH_SUCCESS:
                            Log.i(TAG, "launchIntent: Launched app successfully on display "
                                            + mVirtualDisplay.getDisplay().getDisplayId());
                            break;
                        case VirtualDeviceManager.LAUNCH_FAILURE_NO_ACTIVITY:
                        case VirtualDeviceManager.LAUNCH_FAILURE_PENDING_INTENT_CANCELED:
                            Log.w(TAG, "launchIntent: Launching app failed with reason: "
                                    + result);
                            break;
                        default:
                            Log.w(TAG, "launchIntent: Unexpected result when launching app: "
                                    + result);
                    }
                });
    }

    int getRemoteDisplayId() {
        return mRemoteDisplayId;
    }

    int getDisplayId() {
        return mVirtualDisplay.getDisplay().getDisplayId();
    }

    void onDisplayChanged() {
        if (mRotation != mVirtualDisplay.getDisplay().getRotation()) {
            mRotation = mVirtualDisplay.getDisplay().getRotation();
            int rotationDegrees = displayRotationToDegrees(mRotation);
            Log.v(TAG, "Notify client for rotation event: " + rotationDegrees);
            mRemoteIo.sendMessage(
                    RemoteEvent.newBuilder()
                            .setDisplayId(getRemoteDisplayId())
                            .setDisplayRotation(
                                    DisplayRotation.newBuilder()
                                            .setRotationDegrees(rotationDegrees))
                            .build());
        }
    }

    @SuppressWarnings("PendingIntentMutability")
    void processRemoteEvent(RemoteEvent event) {
        if (event.getDisplayId() != mRemoteDisplayId) {
            return;
        }
        if (event.hasHomeEvent()) {
            Intent homeIntent = new Intent(Intent.ACTION_MAIN);
            homeIntent.addCategory(Intent.CATEGORY_HOME);
            homeIntent.addFlags(Intent.FLAG_ACTIVITY_NEW_TASK);
            int targetDisplayId =
                    mDisplayType == DISPLAY_TYPE_MIRROR ? Display.DEFAULT_DISPLAY : getDisplayId();
            mContext.startActivity(
                    homeIntent,
                    ActivityOptions.makeBasic().setLaunchDisplayId(targetDisplayId).toBundle());
        } else if (event.hasInputEvent()) {
            processInputEvent(event.getInputEvent());
        } else if (event.hasStopStreaming() && event.getStopStreaming().getPause()) {
            if (mVideoManager != null) {
                mVideoManager.stop();
                mVideoManager = null;
            }
        }
    }

    private void processInputEvent(RemoteInputEvent inputEvent) {
        switch (inputEvent.getDeviceType()) {
            case DEVICE_TYPE_NONE:
                Log.e(TAG, "Received no input device type");
                break;
            case DEVICE_TYPE_DPAD:
                mDpad.sendKeyEvent(remoteEventToVirtualKeyEvent(inputEvent));
                break;
            case DEVICE_TYPE_NAVIGATION_TOUCHPAD:
                if (mNavigationTouchpad == null) {
                    // Any arbitrarily big enough nav touchpad would work.
                    Point displaySize = new Point(5000, 5000);
                    mNavigationTouchpad =
                            mVirtualDevice.createVirtualNavigationTouchpad(
                                    new VirtualNavigationTouchpadConfig.Builder(
                                                    displaySize.x, displaySize.y)
                                            .setAssociatedDisplayId(getDisplayId())
                                            .setInputDeviceName(
                                                    "vdmdemo-navtouchpad" + mRemoteDisplayId)
                                            .build());
                }
                mNavigationTouchpad.sendTouchEvent(remoteEventToVirtualTouchEvent(inputEvent));
                break;
            case DEVICE_TYPE_MOUSE:
                processMouseEvent(inputEvent);
                break;
            case DEVICE_TYPE_TOUCHSCREEN:
                mTouchscreen.sendTouchEvent(remoteEventToVirtualTouchEvent(inputEvent));
                break;
            case DEVICE_TYPE_KEYBOARD:
                if (mKeyboard == null) {
                    mKeyboard =
                            mVirtualDevice.createVirtualKeyboard(
                                    new VirtualKeyboardConfig.Builder()
                                            .setInputDeviceName(
                                                    "vdmdemo-keyboard" + mRemoteDisplayId)
                                            .setAssociatedDisplayId(getDisplayId())
                                            .build());
                }
                mKeyboard.sendKeyEvent(remoteEventToVirtualKeyEvent(inputEvent));
                break;
            default:
                Log.e(
                        TAG,
                        "processInputEvent got an invalid input device type: "
                                + inputEvent.getDeviceType().getNumber());
                break;
        }
    }

    private void processMouseEvent(RemoteInputEvent inputEvent) {
        if (mMouse == null) {
            mMouse =
                    mVirtualDevice.createVirtualMouse(
                            new VirtualMouseConfig.Builder()
                                    .setAssociatedDisplayId(getDisplayId())
                                    .setInputDeviceName("vdmdemo-mouse" + mRemoteDisplayId)
                                    .build());
        }
        if (inputEvent.hasMouseButtonEvent()) {
            mMouse.sendButtonEvent(
                    new VirtualMouseButtonEvent.Builder()
                            .setButtonCode(inputEvent.getMouseButtonEvent().getKeyCode())
                            .setAction(inputEvent.getMouseButtonEvent().getAction())
                            .build());
        } else if (inputEvent.hasMouseScrollEvent()) {
            mMouse.sendScrollEvent(
                    new VirtualMouseScrollEvent.Builder()
                            .setXAxisMovement(inputEvent.getMouseScrollEvent().getX())
                            .setYAxisMovement(inputEvent.getMouseScrollEvent().getY())
                            .build());
        } else if (inputEvent.hasMouseRelativeEvent()) {
            PointF cursorPosition = mMouse.getCursorPosition();
            mMouse.sendRelativeEvent(
                    new VirtualMouseRelativeEvent.Builder()
                            .setRelativeX(
                                    inputEvent.getMouseRelativeEvent().getX() - cursorPosition.x)
                            .setRelativeY(
                                    inputEvent.getMouseRelativeEvent().getY() - cursorPosition.y)
                            .build());
        } else {
            Log.e(TAG, "Received an invalid mouse event");
        }
    }

    private static int getVirtualTouchEventAction(int action) {
        return switch (action) {
            case MotionEvent.ACTION_POINTER_DOWN -> VirtualTouchEvent.ACTION_DOWN;
            case MotionEvent.ACTION_POINTER_UP -> VirtualTouchEvent.ACTION_UP;
            default -> action;
        };
    }

    private static int getVirtualTouchEventToolType(int action) {
        return switch (action) {
            case MotionEvent.ACTION_CANCEL -> VirtualTouchEvent.TOOL_TYPE_PALM;
            default -> VirtualTouchEvent.TOOL_TYPE_FINGER;
        };
    }

    // Surface rotation is in opposite direction to display rotation.
    // See https://developer.android.com/reference/android/view/Display?hl=en#getRotation()
    private static int displayRotationToDegrees(int displayRotation) {
        return switch (displayRotation) {
            case Surface.ROTATION_90 -> -90;
            case Surface.ROTATION_180 -> 180;
            case Surface.ROTATION_270 -> 90;
            default -> 0;
        };
    }

    private static VirtualKeyEvent remoteEventToVirtualKeyEvent(RemoteInputEvent event) {
        RemoteKeyEvent keyEvent = event.getKeyEvent();
        return new VirtualKeyEvent.Builder()
                .setEventTimeNanos((long) (event.getTimestampMs() * 1e6))
                .setKeyCode(keyEvent.getKeyCode())
                .setAction(keyEvent.getAction())
                .build();
    }

    private static VirtualTouchEvent remoteEventToVirtualTouchEvent(RemoteInputEvent event) {
        RemoteMotionEvent motionEvent = event.getTouchEvent();
        return new VirtualTouchEvent.Builder()
                .setEventTimeNanos((long) (event.getTimestampMs() * 1e6))
                .setPointerId(motionEvent.getPointerId())
                .setAction(getVirtualTouchEventAction(motionEvent.getAction()))
                .setPressure(motionEvent.getPressure() * 255f)
                .setToolType(getVirtualTouchEventToolType(motionEvent.getAction()))
                .setX(motionEvent.getX())
                .setY(motionEvent.getY())
                .build();
    }

    @Override
    public void close() {
        if (mClosed.getAndSet(true)) { // Prevent double closure.
            return;
        }
        mRemoteIo.sendMessage(
                RemoteEvent.newBuilder()
                        .setDisplayId(getRemoteDisplayId())
                        .setStopStreaming(StopStreaming.newBuilder().setPause(false))
                        .build());
        mRemoteIo.removeMessageConsumer(mRemoteEventConsumer);
        mDpad.close();
        mTouchscreen.close();
        if (mMouse != null) {
            mMouse.close();
        }
        if (mNavigationTouchpad != null) {
            mNavigationTouchpad.close();
        }
        if (mKeyboard != null) {
            mKeyboard.close();
        }
        mVirtualDisplay.release();
        if (mVideoManager != null) {
            mVideoManager.stop();
            mVideoManager = null;
        }
    }
}
