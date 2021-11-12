# Copyright (C) 2021 The Android Open Source Project
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.
LOCAL_PATH := $(call my-dir)

KMI_CHK_SCRIPT := $(LOCAL_PATH)/gki_kmi_compatibility_test.sh

# Current kernel symbol files to be checked
# Use the one under kernel/prebuilts if it exists
CURR_5_4_SYMVERS ?= kernel/prebuilts/5.4/arm64/Module.symvers
ifeq ($(wildcard $(CURR_5_4_SYMVERS)),)
CURR_5_4_SYMVERS := development/gki/kmi_abi_chk/sym-5.4/Module.symvers
endif
CURR_5_10_SYMVERS ?= kernel/prebuilts/5.10/arm64/vmlinux.symvers
ifeq ($(wildcard $(CURR_5_10_SYMVERS)),)
CURR_5_10_SYMVERS := development/gki/kmi_abi_chk/sym-5.10/vmlinux.symvers
endif

# Previous kernel symbol files, against which the latest one is checked
# The file names of previous kernel symbol files are of this form:
#     *.symvers-$(BID)
# Here *.symvers is a symbolic link to the latest build.
PREV_5_4_SYMVERS := $(LOCAL_PATH)/sym-5.4/Module.symvers
PREV_5_10_SYMVERS := $(LOCAL_PATH)/sym-5.10/vmlinux.symvers

include $(CLEAR_VARS)
LOCAL_MODULE := gki_5_4_kmi_compatibility_test
LOCAL_MODULE_CLASS := FAKE
LOCAL_MODULE_TAGS := optional
include $(BUILD_SYSTEM)/base_rules.mk

$(LOCAL_BUILT_MODULE): $(KMI_CHK_SCRIPT) $(CURR_5_4_SYMVERS) $(PREV_5_4_SYMVERS)
	@mkdir -p $(dir $@)
	$(hide) $(KMI_CHK_SCRIPT) $(CURR_5_4_SYMVERS) $(PREV_5_4_SYMVERS)
	$(hide) touch $@

include $(CLEAR_VARS)
LOCAL_MODULE := gki_5_10_kmi_compatibility_test
LOCAL_MODULE_CLASS := FAKE
LOCAL_MODULE_TAGS := optional
include $(BUILD_SYSTEM)/base_rules.mk

$(LOCAL_BUILT_MODULE): $(KMI_CHK_SCRIPT) $(CURR_5_10_SYMVERS) $(PREV_5_10_SYMVERS)
	@mkdir -p $(dir $@)
	$(hide) $(KMI_CHK_SCRIPT) $(CURR_5_10_SYMVERS) $(PREV_5_10_SYMVERS)
	$(hide) touch $@

include $(CLEAR_VARS)
LOCAL_MODULE := gki_kmi_compatibility_test
LOCAL_REQUIRED_MODULES := gki_5_4_kmi_compatibility_test gki_5_10_kmi_compatibility_test
include $(BUILD_PHONY_PACKAGE)
