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

import static android.companion.virtual.VirtualDeviceParams.DEVICE_POLICY_CUSTOM;
import static android.companion.virtual.VirtualDeviceParams.DEVICE_POLICY_DEFAULT;
import static android.companion.virtual.VirtualDeviceParams.LOCK_STATE_ALWAYS_UNLOCKED;
import static android.companion.virtual.VirtualDeviceParams.POLICY_TYPE_AUDIO;
import static android.companion.virtual.VirtualDeviceParams.POLICY_TYPE_CLIPBOARD;
import static android.companion.virtual.VirtualDeviceParams.POLICY_TYPE_RECENTS;
import static android.companion.virtual.VirtualDeviceParams.POLICY_TYPE_SENSORS;

import android.annotation.SuppressLint;
import android.app.Notification;
import android.app.NotificationChannel;
import android.app.NotificationManager;
import android.app.PendingIntent;
import android.app.Service;
import android.app.role.RoleManager;
import android.companion.AssociationInfo;
import android.companion.AssociationRequest;
import android.companion.CompanionDeviceManager;
import android.companion.virtual.VirtualDeviceManager;
import android.companion.virtual.VirtualDeviceManager.ActivityListener;
import android.companion.virtual.VirtualDeviceParams;
import android.companion.virtual.sensor.VirtualSensorConfig;
import android.content.ComponentName;
import android.content.Intent;
import android.content.IntentSender;
import android.content.IntentSender.SendIntentException;
import android.content.pm.ActivityInfo;
import android.content.pm.PackageManager.NameNotFoundException;
import android.hardware.display.DisplayManager;
import android.os.Binder;
import android.os.IBinder;
import android.util.Log;
import android.view.Display;

import androidx.annotation.NonNull;

import com.example.android.vdmdemo.common.ConnectionManager;
import com.example.android.vdmdemo.common.RemoteEventProto.DeviceCapabilities;
import com.example.android.vdmdemo.common.RemoteEventProto.DisplayChangeEvent;
import com.example.android.vdmdemo.common.RemoteEventProto.RemoteEvent;
import com.example.android.vdmdemo.common.RemoteEventProto.SensorCapabilities;
import com.example.android.vdmdemo.common.RemoteEventProto.StartStreaming;
import com.example.android.vdmdemo.common.RemoteIo;
import com.google.common.util.concurrent.MoreExecutors;

import dagger.hilt.android.AndroidEntryPoint;

import java.util.Arrays;
import java.util.Map;
import java.util.Objects;
import java.util.function.Consumer;

import javax.inject.Inject;

/**
 * VDM Host service, streaming apps to a remote device and processing the input coming from there.
 */
@AndroidEntryPoint(Service.class)
public final class VdmService extends Hilt_VdmService {

    public static final String TAG = "VdmHost";

    private static final String CHANNEL_ID = "com.example.android.vdmdemo.host.VdmService";
    private static final int NOTIFICATION_ID = 1;

    private static final String ACTION_STOP = "com.example.android.vdmdemo.host.VdmService.STOP";

    public static final String ACTION_LOCKDOWN =
            "com.example.android.vdmdemo.host.VdmService.LOCKDOWN";

    /** Provides an instance of this service to bound clients. */
    public class LocalBinder extends Binder {
        VdmService getService() {
            return VdmService.this;
        }
    }

    private final IBinder mBinder = new LocalBinder();

    @Inject ConnectionManager mConnectionManager;
    @Inject RemoteIo mRemoteIo;
    @Inject AudioStreamer mAudioStreamer;
    @Inject PreferenceController mPreferenceController;
    @Inject DisplayRepository mDisplayRepository;

    private RemoteSensorManager mRemoteSensorManager = null;

    private final Consumer<RemoteEvent> mRemoteEventConsumer = this::processRemoteEvent;
    private VirtualDeviceManager.VirtualDevice mVirtualDevice;
    private DeviceCapabilities mDeviceCapabilities;
    private Intent mPendingRemoteIntent = null;
    private @RemoteDisplay.DisplayType int mPendingDisplayType = RemoteDisplay.DISPLAY_TYPE_APP;
    private DisplayManager mDisplayManager;

    private final DisplayManager.DisplayListener mDisplayListener =
            new DisplayManager.DisplayListener() {
                @Override
                public void onDisplayAdded(int displayId) {}

                @Override
                public void onDisplayRemoved(int displayId) {}

                @Override
                public void onDisplayChanged(int displayId) {
                    mDisplayRepository.onDisplayChanged(displayId);
                }
            };

    private final ConnectionManager.ConnectionCallback mConnectionCallback =
            new ConnectionManager.ConnectionCallback() {
                @Override
                public void onDisconnected() {
                    mDeviceCapabilities = null;
                    closeVirtualDevice();
                }
            };

    public VdmService() {}

    @Override
    public IBinder onBind(Intent intent) {
        return mBinder;
    }

    @Override
    public int onStartCommand(Intent intent, int flags, int startId) {
        if (intent != null && ACTION_STOP.equals(intent.getAction())) {
            Log.i(TAG, "Stopping VDM Service.");
            mConnectionManager.disconnect();
            stopForeground(STOP_FOREGROUND_REMOVE);
            stopSelf();
            return START_NOT_STICKY;
        }

        if (intent != null && ACTION_LOCKDOWN.equals(intent.getAction())) {
            lockdown();
            return START_STICKY;
        }

        NotificationChannel notificationChannel =
                new NotificationChannel(
                        CHANNEL_ID, "VDM Service Channel", NotificationManager.IMPORTANCE_LOW);
        notificationChannel.enableVibration(false);
        NotificationManager notificationManager = getSystemService(NotificationManager.class);
        Objects.requireNonNull(notificationManager).createNotificationChannel(notificationChannel);

        Intent openIntent = new Intent(this, MainActivity.class);
        PendingIntent pendingIntentOpen =
                PendingIntent.getActivity(this, 0, openIntent, PendingIntent.FLAG_IMMUTABLE);
        Intent stopIntent = new Intent(this, VdmService.class);
        stopIntent.setAction(ACTION_STOP);
        PendingIntent pendingIntentStop =
                PendingIntent.getService(this, 0, stopIntent, PendingIntent.FLAG_IMMUTABLE);

        Notification notification =
                new Notification.Builder(this, CHANNEL_ID)
                        .setSmallIcon(R.drawable.connected)
                        .setContentTitle("VDM Demo running")
                        .setContentText("Click to open")
                        .setContentIntent(pendingIntentOpen)
                        .addAction(
                                new Notification.Action.Builder(
                                                R.drawable.close, "Stop", pendingIntentStop)
                                        .build())
                        .setOngoing(true)
                        .build();
        startForeground(NOTIFICATION_ID, notification);

        return START_STICKY;
    }

    @Override
    public void onCreate() {
        super.onCreate();

        mConnectionManager.addConnectionCallback(mConnectionCallback);

        mDisplayManager = getSystemService(DisplayManager.class);
        Objects.requireNonNull(mDisplayManager).registerDisplayListener(mDisplayListener, null);

        mRemoteIo.addMessageConsumer(mRemoteEventConsumer);

        if (mPreferenceController.getBoolean(R.string.pref_enable_client_audio)) {
            mAudioStreamer.start();
        }

        mPreferenceController.addPreferenceObserver(this, Map.of(
                R.string.pref_enable_recents,
                b -> updateDevicePolicy(POLICY_TYPE_RECENTS, !(Boolean) b),

                R.string.pref_enable_cross_device_clipboard,
                b -> updateDevicePolicy(POLICY_TYPE_CLIPBOARD, (Boolean) b),

                R.string.pref_show_pointer_icon,
                b -> {
                    if (mVirtualDevice != null) mVirtualDevice.setShowPointerIcon((Boolean) b);
                },

                R.string.pref_enable_client_audio,
                b -> {
                    if ((Boolean) b) mAudioStreamer.start(); else mAudioStreamer.stop();
                },

                R.string.pref_display_ime_policy,
                s -> {
                    if (mVirtualDevice != null) {
                        int policy = Integer.valueOf((String) s);
                        Arrays.stream(mDisplayRepository.getDisplayIds()).forEach(
                                displayId -> mVirtualDevice.setDisplayImePolicy(displayId, policy));
                    }
                },

                R.string.pref_enable_client_sensors, v -> recreateVirtualDevice(),
                R.string.pref_device_profile, v -> recreateVirtualDevice(),
                R.string.pref_always_unlocked_device, v -> recreateVirtualDevice(),
                R.string.pref_enable_custom_home, v -> recreateVirtualDevice()
        ));
    }

    @Override
    public void onDestroy() {
        super.onDestroy();
        mPreferenceController.removePreferenceObserver(this);
        mConnectionManager.removeConnectionCallback(mConnectionCallback);
        closeVirtualDevice();
        mRemoteIo.removeMessageConsumer(mRemoteEventConsumer);
        mDisplayManager.unregisterDisplayListener(mDisplayListener);
        mAudioStreamer.close();
    }

    private void processRemoteEvent(RemoteEvent event) {
        if (event.hasDeviceCapabilities()) {
            Log.i(TAG, "Host received device capabilities");
            mDeviceCapabilities = event.getDeviceCapabilities();
            associateAndCreateVirtualDevice();
        } else if (event.hasDisplayCapabilities() && !mDisplayRepository.resetDisplay(event)) {
            RemoteDisplay remoteDisplay =
                    new RemoteDisplay(
                            this,
                            event,
                            mVirtualDevice,
                            mRemoteIo,
                            mPendingDisplayType,
                            mPreferenceController);
            mDisplayRepository.addDisplay(remoteDisplay);
            mPendingDisplayType = RemoteDisplay.DISPLAY_TYPE_APP;
            if (mPendingRemoteIntent != null) {
                remoteDisplay.launchIntent(
                        PendingIntent.getActivity(
                                this, 0, mPendingRemoteIntent, PendingIntent.FLAG_IMMUTABLE));
            }
        } else if (event.hasStopStreaming() && !event.getStopStreaming().getPause()) {
            mDisplayRepository.removeDisplayByRemoteId(event.getDisplayId());
        }
    }

    private void associateAndCreateVirtualDevice() {
        CompanionDeviceManager cdm =
                Objects.requireNonNull(getSystemService(CompanionDeviceManager.class));
        RoleManager rm = Objects.requireNonNull(getSystemService(RoleManager.class));
        final String deviceProfile = mPreferenceController.getString(R.string.pref_device_profile);
        for (AssociationInfo associationInfo : cdm.getMyAssociations()) {
            // Flashing the device clears the role and the permissions, but not the CDM
            // associations.
            // TODO(b/290596625): Remove the workaround to clear the associations if the role is not
            // held.
            if (!rm.isRoleHeld(deviceProfile)) {
                cdm.disassociate(associationInfo.getId());
            } else if (Objects.equals(associationInfo.getPackageName(), getPackageName())
                    && associationInfo.getDisplayName() != null
                    && Objects.equals(
                            associationInfo.getDisplayName().toString(),
                            mDeviceCapabilities.getDeviceName())) {
                createVirtualDevice(associationInfo);
                return;
            }
        }

        @SuppressLint("MissingPermission")
        AssociationRequest.Builder associationRequest =
                new AssociationRequest.Builder()
                        .setDeviceProfile(deviceProfile)
                        .setDisplayName(mDeviceCapabilities.getDeviceName())
                        .setSelfManaged(true);
        cdm.associate(
                associationRequest.build(),
                new CompanionDeviceManager.Callback() {
                    @Override
                    public void onAssociationPending(@NonNull IntentSender intentSender) {
                        try {
                            startIntentSender(intentSender, null, 0, 0, 0);
                        } catch (SendIntentException e) {
                            Log.e(
                                    TAG,
                                    "onAssociationPending: Failed to send device selection intent",
                                    e);
                        }
                    }

                    @Override
                    public void onAssociationCreated(@NonNull AssociationInfo associationInfo) {
                        Log.i(TAG, "onAssociationCreated: ID " + associationInfo.getId());
                        createVirtualDevice(associationInfo);
                    }

                    @Override
                    public void onFailure(CharSequence error) {
                        Log.e(TAG, "onFailure: RemoteDevice Association failed " + error);
                    }
                },
                null);
        Log.i(TAG, "createCdmAssociation: Waiting for association to happen");
    }

    private void createVirtualDevice(AssociationInfo associationInfo) {
        VirtualDeviceParams.Builder virtualDeviceBuilder =
                new VirtualDeviceParams.Builder()
                        .setName("VirtualDevice - " + mDeviceCapabilities.getDeviceName())
                        .setDevicePolicy(POLICY_TYPE_AUDIO, DEVICE_POLICY_CUSTOM)
                        .setAudioPlaybackSessionId(mAudioStreamer.getPlaybackSessionId());

        if (mPreferenceController.getBoolean(R.string.pref_always_unlocked_device)) {
            virtualDeviceBuilder.setLockState(LOCK_STATE_ALWAYS_UNLOCKED);
        }

        if (mPreferenceController.getBoolean(R.string.pref_enable_custom_home)) {
            virtualDeviceBuilder.setHomeComponent(
                    new ComponentName(this, CustomLauncherActivity.class));
        }

        if (!mPreferenceController.getBoolean(R.string.pref_enable_recents)) {
            virtualDeviceBuilder.setDevicePolicy(POLICY_TYPE_RECENTS, DEVICE_POLICY_CUSTOM);
        }

        if (mPreferenceController.getBoolean(R.string.pref_enable_cross_device_clipboard)) {
            virtualDeviceBuilder.setDevicePolicy(POLICY_TYPE_CLIPBOARD, DEVICE_POLICY_CUSTOM);
        }

        if (mPreferenceController.getBoolean(R.string.pref_enable_client_sensors)) {
            for (SensorCapabilities sensor : mDeviceCapabilities.getSensorCapabilitiesList()) {
                virtualDeviceBuilder.addVirtualSensorConfig(
                        new VirtualSensorConfig.Builder(
                                        sensor.getType(), "Remote-" + sensor.getName())
                                .setMinDelay(sensor.getMinDelayUs())
                                .setMaxDelay(sensor.getMaxDelayUs())
                                .setPower(sensor.getPower())
                                .setResolution(sensor.getResolution())
                                .setMaximumRange(sensor.getMaxRange())
                                .build());
            }

            if (mDeviceCapabilities.getSensorCapabilitiesCount() > 0) {
                mRemoteSensorManager = new RemoteSensorManager(mRemoteIo);
                virtualDeviceBuilder
                        .setDevicePolicy(POLICY_TYPE_SENSORS, DEVICE_POLICY_CUSTOM)
                        .setVirtualSensorCallback(
                                MoreExecutors.directExecutor(),
                                mRemoteSensorManager.getVirtualSensorCallback());
            }
        }

        VirtualDeviceManager vdm =
                Objects.requireNonNull(getSystemService(VirtualDeviceManager.class));
        mVirtualDevice =
                vdm.createVirtualDevice(associationInfo.getId(), virtualDeviceBuilder.build());
        if (mRemoteSensorManager != null) {
            mRemoteSensorManager.setVirtualSensors(mVirtualDevice.getVirtualSensorList());
        }

        mVirtualDevice.setShowPointerIcon(
                mPreferenceController.getBoolean(R.string.pref_show_pointer_icon));

        mVirtualDevice.addActivityListener(
                MoreExecutors.directExecutor(),
                new ActivityListener() {

                    @Override
                    public void onTopActivityChanged(
                            int displayId, @NonNull ComponentName componentName) {
                        int remoteDisplayId = mDisplayRepository.getRemoteDisplayId(displayId);
                        if (remoteDisplayId == Display.INVALID_DISPLAY) {
                            return;
                        }
                        String title = "";
                        try {
                            ActivityInfo activityInfo =
                                    getPackageManager().getActivityInfo(componentName, 0);
                            title = activityInfo.loadLabel(getPackageManager()).toString();
                        } catch (NameNotFoundException e) {
                            Log.w(TAG, "Failed to get activity label for " + componentName);
                        }
                        mRemoteIo.sendMessage(
                                RemoteEvent.newBuilder()
                                        .setDisplayId(remoteDisplayId)
                                        .setDisplayChangeEvent(
                                                DisplayChangeEvent.newBuilder().setTitle(title))
                                        .build());
                    }

                    @Override
                    public void onDisplayEmpty(int displayId) {
                        Log.i(TAG, "Display " + displayId + " is empty, removing");
                        mDisplayRepository.removeDisplay(displayId);
                    }
                });
        mVirtualDevice.addActivityListener(
                MoreExecutors.directExecutor(),
                new RunningVdmUidsTracker(getApplicationContext(), mAudioStreamer));

        Log.i(TAG, "Created virtual device");
    }

    private void lockdown() {
        Log.i(TAG, "Initiating Lockdown.");
        mDisplayRepository.clear();
    }

    private synchronized void closeVirtualDevice() {
        if (mRemoteSensorManager != null) {
            mRemoteSensorManager.close();
            mRemoteSensorManager = null;
        }
        if (mVirtualDevice != null) {
            Log.i(TAG, "Closing virtual device");
            mDisplayRepository.clear();
            mVirtualDevice.close();
            mVirtualDevice = null;
        }
    }

    int[] getRemoteDisplayIds() {
        return mDisplayRepository.getRemoteDisplayIds();
    }

    void startStreamingHome() {
        mPendingRemoteIntent = null;
        mPendingDisplayType = RemoteDisplay.DISPLAY_TYPE_HOME;
        mRemoteIo.sendMessage(RemoteEvent.newBuilder()
                .setStartStreaming(StartStreaming.newBuilder().setHomeEnabled(true)).build());
    }

    void startMirroring() {
        mPendingRemoteIntent = null;
        mPendingDisplayType = RemoteDisplay.DISPLAY_TYPE_MIRROR;
        mRemoteIo.sendMessage(
                RemoteEvent.newBuilder()
                        .setStartStreaming(StartStreaming.newBuilder().setHomeEnabled(true))
                        .build());
    }

    void startStreaming(Intent intent) {
        mPendingRemoteIntent = intent;
        mRemoteIo.sendMessage(
                RemoteEvent.newBuilder().setStartStreaming(StartStreaming.newBuilder()).build());
    }

    void startIntentOnDisplayIndex(Intent intent, int displayIndex) {
        PendingIntent pendingIntent =
                PendingIntent.getActivity(this, 0, intent, PendingIntent.FLAG_IMMUTABLE);
        mDisplayRepository
                .getDisplayByIndex(displayIndex)
                .ifPresent(d -> d.launchIntent(pendingIntent));
    }

    private void recreateVirtualDevice() {
        if (mVirtualDevice != null) {
            closeVirtualDevice();
            if (mDeviceCapabilities != null) {
                associateAndCreateVirtualDevice();
            }
        }
    }

    private void updateDevicePolicy(int policyType, boolean custom) {
        if (mVirtualDevice != null) {
            mVirtualDevice.setDevicePolicy(
                    policyType, custom ? DEVICE_POLICY_CUSTOM : DEVICE_POLICY_DEFAULT);
        }
    }
}
