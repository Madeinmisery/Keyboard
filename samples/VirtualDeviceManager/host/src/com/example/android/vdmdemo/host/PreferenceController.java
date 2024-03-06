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

import static android.os.Build.VERSION.SDK_INT;
import static android.os.Build.VERSION_CODES.UPSIDE_DOWN_CAKE;
import static android.os.Build.VERSION_CODES.VANILLA_ICE_CREAM;

import android.companion.AssociationRequest;
import android.companion.virtual.flags.Flags;
import android.content.Context;
import android.content.SharedPreferences;
import android.util.ArrayMap;

import androidx.annotation.StringRes;
import androidx.preference.Preference;
import androidx.preference.PreferenceManager;

import dagger.hilt.android.qualifiers.ApplicationContext;

import java.util.Arrays;
import java.util.Map;
import java.util.Objects;
import java.util.Set;
import java.util.function.BooleanSupplier;
import java.util.function.Consumer;

import javax.inject.Inject;
import javax.inject.Singleton;

/**
 * Manages the VDM Demo Host application settings and feature switches.
 *
 * <p>Upon creation, it will automatically update the preference values based on the current SDK
 * version and the relevant feature flags.</p>
 */
@Singleton
final class PreferenceController {

    // LINT.IfChange
    private static final Set<PrefRule<?>> RULES = Set.of(

            // Exposed in the settings page

            new BoolRule(R.string.pref_enable_cross_device_clipboard,
                    VANILLA_ICE_CREAM, Flags::crossDeviceClipboard),

            new BoolRule(R.string.pref_enable_client_sensors, UPSIDE_DOWN_CAKE),

            new BoolRule(R.string.pref_enable_display_rotation,
                    VANILLA_ICE_CREAM, Flags::consistentDisplayFlags)
                    .withDefaultValue(true),

            new BoolRule(R.string.pref_enable_custom_home, VANILLA_ICE_CREAM, Flags::vdmCustomHome),

            new StringRule(R.string.pref_display_ime_policy, VANILLA_ICE_CREAM, Flags::vdmCustomIme)
                    .withDefaultValue(String.valueOf(0)),

            // TODO(b/316098039): Evaluate the minSdk of the prefs below.
            new StringRule(R.string.pref_device_profile, VANILLA_ICE_CREAM)
                    .withDefaultValue(AssociationRequest.DEVICE_PROFILE_APP_STREAMING),
            new BoolRule(R.string.pref_enable_recents, VANILLA_ICE_CREAM),
            new BoolRule(R.string.pref_enable_client_audio, VANILLA_ICE_CREAM),
            new BoolRule(R.string.pref_always_unlocked_device, VANILLA_ICE_CREAM),
            new BoolRule(R.string.pref_show_pointer_icon, VANILLA_ICE_CREAM),
            new BoolRule(R.string.pref_record_encoder_output, VANILLA_ICE_CREAM),

            // Internal-only switches not exposed in the settings page.
            // All of these are booleans acting as switches, while the above ones may be any type.

            // TODO(b/316098039): Use the SysDecor flag on <= VIC
            new InternalBoolRule(R.string.internal_pref_enable_home_displays,
                    VANILLA_ICE_CREAM, Flags::vdmCustomHome),

            new InternalBoolRule(R.string.internal_pref_enable_mirror_displays,
                    VANILLA_ICE_CREAM,
                    Flags::consistentDisplayFlags, Flags::interactiveScreenMirror)
    );
    // LINT.ThenChange(/samples/VirtualDeviceManager/README.md:host_options)

    private final ArrayMap<Object, Map<String, Consumer<Object>>> mObservers = new ArrayMap<>();
    private final SharedPreferences.OnSharedPreferenceChangeListener mPreferenceChangeListener =
            this::onPreferencesChanged;

    private final Context mContext;
    private final SharedPreferences mSharedPreferences;

    @Inject
    PreferenceController(@ApplicationContext Context context) {
        mContext = context;
        mSharedPreferences = PreferenceManager.getDefaultSharedPreferences(mContext);

        SharedPreferences.Editor editor = mSharedPreferences.edit();
        RULES.forEach(r -> r.evaluate(mContext, editor));
        editor.commit();

        mSharedPreferences.registerOnSharedPreferenceChangeListener(mPreferenceChangeListener);
    }

    /**
     * Adds an observer for preference changes.
     *
     * @param key an object used only for bookkeeping.
     * @param preferenceObserver a map from resource ID corresponding to the preference string key
     *    to the function that should be executed when that preference changes.
     */
    void addPreferenceObserver(Object key, Map<Integer, Consumer<Object>> preferenceObserver) {
        ArrayMap<String, Consumer<Object>> stringObserver = new ArrayMap<>();
        for (int resId : preferenceObserver.keySet()) {
            stringObserver.put(
                    Objects.requireNonNull(mContext.getString(resId)),
                    preferenceObserver.get(resId));
        }
        mObservers.put(key, stringObserver);
    }

    /** Removes a previously added preference observer for the given key. */
    void removePreferenceObserver(Object key) {
        mObservers.remove(key);
    }

    /**
     * Disables any {@link androidx.preference.Preference}, which is not satisfied by the current
     * SDK version or the relevant feature flags.
     *
     * <p>This doesn't change any of the preference values, only disables the relevant UI elements
     * in the preference screen.</p>
     */
    void evaluate(PreferenceManager preferenceManager) {
        RULES.forEach(r -> r.evaluate(mContext, preferenceManager));
    }

    boolean getBoolean(@StringRes int resId) {
        return mSharedPreferences.getBoolean(mContext.getString(resId), false);
    }

    String getString(@StringRes int resId) {
        return Objects.requireNonNull(
                mSharedPreferences.getString(mContext.getString(resId), null));
    }

    int getInt(@StringRes int resId) {
        return Integer.valueOf(getString(resId));
    }

    private void onPreferencesChanged(SharedPreferences sharedPreferences, String key) {
        Map<String, ?> currentPreferences = sharedPreferences.getAll();
        for (Map<String, Consumer<Object>> observer : mObservers.values()) {
            Consumer<Object> consumer = observer.get(key);
            if (consumer != null) {
                consumer.accept(currentPreferences.get(key));
            }
        }
    }

    private abstract static class PrefRule<T> {
        final @StringRes int mKey;
        final int mMinSdk;
        final BooleanSupplier[] mRequiredFlags;

        protected T mDefaultValue;

        PrefRule(@StringRes int key, T defaultValue, int minSdk, BooleanSupplier... requiredFlags) {
            mKey = key;
            mMinSdk = minSdk;
            mRequiredFlags = requiredFlags;
            mDefaultValue = defaultValue;
        }

        void evaluate(Context context, SharedPreferences.Editor editor) {
            if (!isSatisfied()) {
                reset(context, editor);
            }
        }

        void evaluate(Context context, PreferenceManager preferenceManager)  {
            Preference preference = preferenceManager.findPreference(context.getString(mKey));
            if (preference != null) {
                boolean enabled = isSatisfied();
                if (preference.isEnabled() != enabled) {
                    preference.setEnabled(enabled);
                }
            }
        }

        protected abstract void reset(Context context, SharedPreferences.Editor editor);

        protected boolean isSatisfied() {
            return mMinSdk >= SDK_INT
                    && Arrays.stream(mRequiredFlags).allMatch(BooleanSupplier::getAsBoolean);
        }

        PrefRule<T> withDefaultValue(T defaultValue) {
            mDefaultValue = defaultValue;
            return this;
        }
    }

    private static class BoolRule extends PrefRule<Boolean> {
        BoolRule(@StringRes int key, int minSdk, BooleanSupplier... requiredFlags) {
            super(key, false, minSdk, requiredFlags);
        }

        @Override
        protected void reset(Context context, SharedPreferences.Editor editor) {
            editor.putBoolean(context.getString(mKey), mDefaultValue);
        }
    }

    private static class InternalBoolRule extends BoolRule {
        InternalBoolRule(@StringRes int key, int minSdk, BooleanSupplier... requiredFlags) {
            super(key, minSdk, requiredFlags);
        }

        @Override
        void evaluate(Context context, SharedPreferences.Editor editor) {
            editor.putBoolean(context.getString(mKey), isSatisfied());
        }
    }

    private static class StringRule extends PrefRule<String> {
        StringRule(@StringRes int key, int minSdk, BooleanSupplier... requiredFlags) {
            super(key, null, minSdk, requiredFlags);
        }

        @Override
        protected void reset(Context context, SharedPreferences.Editor editor) {
            editor.putString(context.getString(mKey), mDefaultValue);
        }
    }
}
