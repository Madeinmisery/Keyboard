#
# Copyright 2021 The Android Open Source Project
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#      http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.
#
ifeq ($(TARGET_ARCH),arm64)

KMI_CHK_SCRIPT := development/gki/kmi_abi_chk/kmi_static_chk.sh

# Current kernel symbol files to be checked
CURR_5_4_SYMVERS := development/gki/kmi_abi_chk/sym-5.4/Module.symvers
CURR_5_10_SYMVERS := development/gki/kmi_abi_chk/sym-5.10/vmlinux.symvers

# Previous kernel symbol files, against which the latest one is checked
# The file names of previous kernel symbol files are of this form:
#     *.symvers-$(BID)
PREV_5_4_SYMVERS := development/gki/kmi_abi_chk/sym-5.4/Module.symvers-*
PREV_5_10_SYMVERS := development/gki/kmi_abi_chk/sym-5.10/vmlinux.symvers-*

.PHONY: kmi_static_chk kmi504_static_chk kmi510_static_chk

kmi_static_chk: kmi504_static_chk kmi510_static_chk

kmi504_static_chk: $(KMI_CHK_SCRIPT) $(CURR_5_4_SYMVERS)
	$(KMI_CHK_SCRIPT) $(CURR_5_4_SYMVERS) $(PREV_5_4_SYMVERS)

kmi510_static_chk: $(KMI_CHK_SCRIPT) $(CURR_5_10_SYMVERS)
	$(KMI_CHK_SCRIPT) $(CURR_5_10_SYMVERS) $(PREV_5_10_SYMVERS)

endif
