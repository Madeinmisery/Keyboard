#!/bin/bash
GCC_ROOT=${ANDROID_BUILD_TOP}/prebuilts/gcc/linux-x86/host/x86_64-w64-mingw32-4.8
${GCC_ROOT}/bin/x86_64-w64-mingw32-g++ -c -DUSE_MINGW -DWIN32_LEAN_AND_MEAN -D__STDC_FORMAT_MACROS -D__STDC_CONSTANT_MACROS -D__USE_MINGW_ANSI_STDIO=1 -D_WIN32_WINNT=0x0600 -DWINVER=0x0600 -D_FILE_OFFSET_BITS=64 --sysroot ${GCC_ROOT}/x86_64-w64-mingw32 -m32 -DANDROID -fmessage-length=0 -no-canonical-prefixes -DNDEBUG -UDEBUG -fno-exceptions -O2 -g -fno-strict-aliasing -fdebug-prefix-map=/proc/self/cwd= -D__compiler_offsetof=__builtin_offsetof -isystem ${GCC_ROOT}/x86_64-w64-mingw32/include -B${GCC_ROOT}/x86_64-w64-mingw32/bin -DANDROID_STRICT -std=gnu++11 -D_LIBCPP_ENABLE_THREAD_SAFETY_ANNOTATIONS -nostdinc++ -o Main.o ${ANDROID_BUILD_TOP}/development/samples/WindowsLinkOrderFailure/Main.cpp

${GCC_ROOT}/bin/x86_64-w64-mingw32-g++ Main.o -o Main.exe -B${GCC_ROOT}/x86_64-w64-mingw32/bin  -Wl,--no-undefined -Wl,--dynamicbase -Wl,--nxcompat -m32 -Wl,--large-address-aware -L${GCC_ROOT}/x86_64-w64-mingw32/lib32 -B${GCC_ROOT}/x86_64-w64-mingw32/bin -B${GCC_ROOT}/lib/gcc/x86_64-w64-mingw32/4.8.3/32 -L${GCC_ROOT}//lib/gcc/x86_64-w64-mingw32/4.8.3/32 -B${GCC_ROOT}/x86_64-w64-mingw32/lib32 -Wl,--allow-multiple-definition -Wl,-rpath,\$ORIGIN/../lib -Wl,-rpath,\$ORIGIN/lib  -nodefaultlibs -lmingw32 -lgcc -lmoldname -lmingwex -lmsvcrt -lmsvcr110 -ladvapi32 -lshell32 -luser32 -lkernel32 -lmingw32 -lgcc -lmoldname -lmingwex

${GCC_ROOT}/bin/x86_64-w64-mingw32-g++ Main.o -o Main_broken.exe -B${GCC_ROOT}/x86_64-w64-mingw32/bin  -Wl,--no-undefined -Wl,--dynamicbase -Wl,--nxcompat -m32 -Wl,--large-address-aware -L${GCC_ROOT}/x86_64-w64-mingw32/lib32 -B${GCC_ROOT}/x86_64-w64-mingw32/bin -B${GCC_ROOT}/lib/gcc/x86_64-w64-mingw32/4.8.3/32 -L${GCC_ROOT}//lib/gcc/x86_64-w64-mingw32/4.8.3/32 -B${GCC_ROOT}/x86_64-w64-mingw32/lib32 -Wl,--allow-multiple-definition -Wl,-rpath,\$ORIGIN/../lib -Wl,-rpath,\$ORIGIN/lib  -nodefaultlibs -lmingw32 -lgcc -lmoldname -lmsvcr110 -lmingwex -lmsvcrt -ladvapi32 -lshell32 -luser32 -lkernel32 -lmingw32 -lgcc -lmoldname -lmingwex
