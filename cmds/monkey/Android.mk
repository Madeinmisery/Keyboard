# Copyright 2008 The Android Open Source Project
#
LOCAL_PATH:= $(call my-dir)
include $(CLEAR_VARS)

LOCAL_SRC_FILES := $(call all-subdir-java-files)
LOCAL_MODULE := monkey
include $(BUILD_JAVA_LIBRARY)

################################################################
include $(CLEAR_VARS)
LOCAL_MODULE := monkey
LOCAL_MODULE_CLASS := EXECUTABLES
LOCAL_SRC_FILES := monkey
LOCAL_ADDITIONAL_DEPENDENCIES := $(TARGET_OUT_JAVA_LIBRARIES)/monkey$(COMMON_JAVA_PACKAGE_SUFFIX)
include $(BUILD_PREBUILT)
