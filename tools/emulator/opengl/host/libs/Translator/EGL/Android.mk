LOCAL_PATH := $(call my-dir)

### EGL host implementation ########################
include $(CLEAR_VARS)

translator_path := $(LOCAL_PATH)/..

OS_SRCS:=


ifeq ($(HOST_OS),linux)
    OS_SRCS = EglX11Api.cpp
    LOCAL_LDLIBS := -lX11 -lGL -ldl

LOCAL_SRC_FILES :=            \
     $(OS_SRCS)               \
     ThreadInfo.cpp           \
     EglImp.cpp               \
     EglConfig.cpp            \
     EglContext.cpp           \
     EglGlobalInfo.cpp        \
     EglValidate.cpp          \
     EglSurface.cpp           \
     EglWindowSurface.cpp     \
     EglPbufferSurface.cpp    \
     EglPixmapSurface.cpp     \
     EglThreadInfo.cpp        \
     EglDisplay.cpp


LOCAL_C_INCLUDES += \
                 $(translator_path)/include

LOCAL_CFLAGS := -g -O0
LOCAL_MODULE_TAGS := debug
LOCAL_MODULE := libEGL_translator
LOCAL_STATIC_LIBRARIES := libGLcommon libcutils
include $(BUILD_HOST_SHARED_LIBRARY)

endif
