/*
 * Copyright 2012, The Android Open Source Project
 *
 * Licensed under the Apache License, Version 2.0 (the "License");
 * you may not use this file except in compliance with the License.
 * You may obtain a copy of the License at
 *
 *     http://www.apache.org/licenses/LICENSE-2.0
 *
 * Unless required by applicable law or agreed to in writing, software
 * distributed under the License is distributed on an "AS IS" BASIS,
 * WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
 * See the License for the specific language governing permissions and
 * limitations under the License.
 */

#include <stat_portable.h>

/* Note: The Portable Header will define stat to stat_portable */
int stat_portable(const char *path, struct stat_portable *s)
{
    struct stat x86_stat;
    int ret = stat(path, &x86_stat);
    stat_ntop(&x86_stat, s);
    return ret;
}

int fstat_portable(int fd, struct stat_portable *s)
{
    struct stat x86_stat;
    int ret = fstat(fd, &x86_stat);
    stat_ntop(&x86_stat, s);
    return ret;
}   

int lstat_portable(const char *path, struct stat_portable *s)
{
    struct stat x86_stat;
    int ret = lstat(path, &x86_stat);
    stat_ntop(&x86_stat, s);
    return ret;
}

int fstatat_portable(int dirfd, const char *path, struct stat_portable *s, int flags)
{
    struct stat x86_stat;
    int ret = fstatat(dirfd, path, &x86_stat, flags);
    stat_ntop(&x86_stat, s);
    return ret;
}
