/*
 * Copyright (C) 2019 The Android Open Source Project
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

#include <android/log.h>
#include <dlfcn.h>
#include <string>

#define print(...) __android_log_print(ANDROID_LOG_INFO, "GPU-COUNTERS", __VA_ARGS__);
int main(int argc, char **argv) {
  if(argc<2) {
    print("Path to the lib required as parameter. Exiting");
    return -1;
  }
  void *handle = dlopen(argv[1], RTLD_GLOBAL);
  if (!handle) {
    print("Error loading lib. exiting");
    return -1;
  }
  dlerror();
  void (*startFunc)(void);
  * (void **) (&startFunc)  = dlsym(handle, "startProducer");
  char *error;
  if((error=dlerror()) != NULL) {
    print("Error in dlsym. exiting\n %s", error);
    return -1;
  }
  (*startFunc)();
  return 0;
}
