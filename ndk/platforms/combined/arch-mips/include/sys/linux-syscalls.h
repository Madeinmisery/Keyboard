/* auto-generated by gensyscalls.py, do not touch */
#ifndef _BIONIC_LINUX_SYSCALLS_H_

#if !defined __ASM_ARM_UNISTD_H && !defined __ASM_I386_UNISTD_H && !defined __ASM_MIPS_UNISTD_H
#if defined __arm__ && !defined __ARM_EABI__ && !defined __thumb__
#  define __NR_SYSCALL_BASE  0x900000
#elif defined(__mips__)
#  define __NR_SYSCALL_BASE 4000
#else
#  define  __NR_SYSCALL_BASE  0
#endif

#define __NR_exit                         (__NR_SYSCALL_BASE + 1)
#define __NR_fork                         (__NR_SYSCALL_BASE + 2)
#define __NR_read                         (__NR_SYSCALL_BASE + 3)
#define __NR_write                        (__NR_SYSCALL_BASE + 4)
#define __NR_open                         (__NR_SYSCALL_BASE + 5)
#define __NR_close                        (__NR_SYSCALL_BASE + 6)
#define __NR_link                         (__NR_SYSCALL_BASE + 9)
#define __NR_unlink                       (__NR_SYSCALL_BASE + 10)
#define __NR_execve                       (__NR_SYSCALL_BASE + 11)
#define __NR_chdir                        (__NR_SYSCALL_BASE + 12)
#define __NR_mknod                        (__NR_SYSCALL_BASE + 14)
#define __NR_chmod                        (__NR_SYSCALL_BASE + 15)
#define __NR_lseek                        (__NR_SYSCALL_BASE + 19)
#define __NR_getpid                       (__NR_SYSCALL_BASE + 20)
#define __NR_mount                        (__NR_SYSCALL_BASE + 21)
#define __NR_ptrace                       (__NR_SYSCALL_BASE + 26)
#define __NR_pause                        (__NR_SYSCALL_BASE + 29)
#define __NR_access                       (__NR_SYSCALL_BASE + 33)
#define __NR_sync                         (__NR_SYSCALL_BASE + 36)
#define __NR_rename                       (__NR_SYSCALL_BASE + 38)
#define __NR_mkdir                        (__NR_SYSCALL_BASE + 39)
#define __NR_rmdir                        (__NR_SYSCALL_BASE + 40)
#define __NR_dup                          (__NR_SYSCALL_BASE + 41)
#define __NR_times                        (__NR_SYSCALL_BASE + 43)
#define __NR_brk                          (__NR_SYSCALL_BASE + 45)
#define __NR_acct                         (__NR_SYSCALL_BASE + 51)
#define __NR_umount2                      (__NR_SYSCALL_BASE + 52)
#define __NR_ioctl                        (__NR_SYSCALL_BASE + 54)
#define __NR_fcntl                        (__NR_SYSCALL_BASE + 55)
#define __NR_setpgid                      (__NR_SYSCALL_BASE + 57)
#define __NR_umask                        (__NR_SYSCALL_BASE + 60)
#define __NR_chroot                       (__NR_SYSCALL_BASE + 61)
#define __NR_dup2                         (__NR_SYSCALL_BASE + 63)
#define __NR_getppid                      (__NR_SYSCALL_BASE + 64)
#define __NR_setsid                       (__NR_SYSCALL_BASE + 66)
#define __NR_sigaction                    (__NR_SYSCALL_BASE + 67)
#define __NR_sigsuspend                   (__NR_SYSCALL_BASE + 72)
#define __NR_sigpending                   (__NR_SYSCALL_BASE + 73)
#define __NR_setrlimit                    (__NR_SYSCALL_BASE + 75)
#define __NR_getrusage                    (__NR_SYSCALL_BASE + 77)
#define __NR_gettimeofday                 (__NR_SYSCALL_BASE + 78)
#define __NR_settimeofday                 (__NR_SYSCALL_BASE + 79)
#define __NR_symlink                      (__NR_SYSCALL_BASE + 83)
#define __NR_readlink                     (__NR_SYSCALL_BASE + 85)
#define __NR_reboot                       (__NR_SYSCALL_BASE + 88)
#define __NR_munmap                       (__NR_SYSCALL_BASE + 91)
#define __NR_truncate                     (__NR_SYSCALL_BASE + 92)
#define __NR_ftruncate                    (__NR_SYSCALL_BASE + 93)
#define __NR_fchmod                       (__NR_SYSCALL_BASE + 94)
#define __NR_getpriority                  (__NR_SYSCALL_BASE + 96)
#define __NR_setpriority                  (__NR_SYSCALL_BASE + 97)
#define __NR_syslog                       (__NR_SYSCALL_BASE + 103)
#define __NR_syslog                       (__NR_SYSCALL_BASE + 103)
#define __NR_setitimer                    (__NR_SYSCALL_BASE + 104)
#define __NR_getitimer                    (__NR_SYSCALL_BASE + 105)
#define __NR_wait4                        (__NR_SYSCALL_BASE + 114)
#define __NR_sysinfo                      (__NR_SYSCALL_BASE + 116)
#define __NR_fsync                        (__NR_SYSCALL_BASE + 118)
#define __NR_clone                        (__NR_SYSCALL_BASE + 120)
#define __NR_uname                        (__NR_SYSCALL_BASE + 122)
#define __NR_mprotect                     (__NR_SYSCALL_BASE + 125)
#define __NR_sigprocmask                  (__NR_SYSCALL_BASE + 126)
#define __NR_init_module                  (__NR_SYSCALL_BASE + 128)
#define __NR_delete_module                (__NR_SYSCALL_BASE + 129)
#define __NR_getpgid                      (__NR_SYSCALL_BASE + 132)
#define __NR_fchdir                       (__NR_SYSCALL_BASE + 133)
#define __NR__llseek                      (__NR_SYSCALL_BASE + 140)
#define __NR__newselect                   (__NR_SYSCALL_BASE + 142)
#define __NR_flock                        (__NR_SYSCALL_BASE + 143)
#define __NR_msync                        (__NR_SYSCALL_BASE + 144)
#define __NR_readv                        (__NR_SYSCALL_BASE + 145)
#define __NR_writev                       (__NR_SYSCALL_BASE + 146)

#ifdef __arm__
#define __NR_pipe                         (__NR_SYSCALL_BASE + 42)
#define __NR_fdatasync                    (__NR_SYSCALL_BASE + 148)
#define __NR_mlock                        (__NR_SYSCALL_BASE + 150)
#define __NR_munlock                      (__NR_SYSCALL_BASE + 151)
#define __NR_sched_setparam               (__NR_SYSCALL_BASE + 154)
#define __NR_sched_getparam               (__NR_SYSCALL_BASE + 155)
#define __NR_sched_setscheduler           (__NR_SYSCALL_BASE + 156)
#define __NR_sched_getscheduler           (__NR_SYSCALL_BASE + 157)
#define __NR_sched_yield                  (__NR_SYSCALL_BASE + 158)
#define __NR_sched_get_priority_max       (__NR_SYSCALL_BASE + 159)
#define __NR_sched_get_priority_min       (__NR_SYSCALL_BASE + 160)
#define __NR_sched_rr_get_interval        (__NR_SYSCALL_BASE + 161)
#define __NR_nanosleep                    (__NR_SYSCALL_BASE + 162)
#define __NR_mremap                       (__NR_SYSCALL_BASE + 163)
#define __NR_poll                         (__NR_SYSCALL_BASE + 168)
#define __NR_prctl                        (__NR_SYSCALL_BASE + 172)
#define __NR_rt_sigaction                 (__NR_SYSCALL_BASE + 174)
#define __NR_rt_sigprocmask               (__NR_SYSCALL_BASE + 175)
#define __NR_rt_sigtimedwait              (__NR_SYSCALL_BASE + 177)
#define __NR_pread64                      (__NR_SYSCALL_BASE + 180)
#define __NR_pwrite64                     (__NR_SYSCALL_BASE + 181)
#define __NR_getcwd                       (__NR_SYSCALL_BASE + 183)
#define __NR_capget                       (__NR_SYSCALL_BASE + 184)
#define __NR_capset                       (__NR_SYSCALL_BASE + 185)
#define __NR_sigaltstack                  (__NR_SYSCALL_BASE + 186)
#define __NR_sendfile                     (__NR_SYSCALL_BASE + 187)
#define __NR_vfork                        (__NR_SYSCALL_BASE + 190)
#define __NR_ugetrlimit                   (__NR_SYSCALL_BASE + 191)
#define __NR_mmap2                        (__NR_SYSCALL_BASE + 192)
#define __NR_ftruncate64                  (__NR_SYSCALL_BASE + 194)
#define __NR_stat64                       (__NR_SYSCALL_BASE + 195)
#define __NR_lstat64                      (__NR_SYSCALL_BASE + 196)
#define __NR_fstat64                      (__NR_SYSCALL_BASE + 197)
#define __NR_lchown32                     (__NR_SYSCALL_BASE + 198)
#define __NR_getuid32                     (__NR_SYSCALL_BASE + 199)
#define __NR_getgid32                     (__NR_SYSCALL_BASE + 200)
#define __NR_geteuid32                    (__NR_SYSCALL_BASE + 201)
#define __NR_getegid32                    (__NR_SYSCALL_BASE + 202)
#define __NR_setreuid32                   (__NR_SYSCALL_BASE + 203)
#define __NR_setregid32                   (__NR_SYSCALL_BASE + 204)
#define __NR_getgroups32                  (__NR_SYSCALL_BASE + 205)
#define __NR_setgroups32                  (__NR_SYSCALL_BASE + 206)
#define __NR_fchown32                     (__NR_SYSCALL_BASE + 207)
#define __NR_setresuid32                  (__NR_SYSCALL_BASE + 208)
#define __NR_getresuid32                  (__NR_SYSCALL_BASE + 209)
#define __NR_setresgid32                  (__NR_SYSCALL_BASE + 210)
#define __NR_getresgid32                  (__NR_SYSCALL_BASE + 211)
#define __NR_chown32                      (__NR_SYSCALL_BASE + 212)
#define __NR_setuid32                     (__NR_SYSCALL_BASE + 213)
#define __NR_setgid32                     (__NR_SYSCALL_BASE + 214)
#define __NR_getdents64                   (__NR_SYSCALL_BASE + 217)
#define __NR_mincore                      (__NR_SYSCALL_BASE + 219)
#define __NR_madvise                      (__NR_SYSCALL_BASE + 220)
#define __NR_fcntl64                      (__NR_SYSCALL_BASE + 221)
#define __NR_gettid                       (__NR_SYSCALL_BASE + 224)
#define __NR_futex                        (__NR_SYSCALL_BASE + 240)
#define __NR_sched_setaffinity            (__NR_SYSCALL_BASE + 241)
#define __NR_sched_getaffinity            (__NR_SYSCALL_BASE + 242)
#define __NR_exit_group                   (__NR_SYSCALL_BASE + 248)
#define __NR_epoll_create                 (__NR_SYSCALL_BASE + 250)
#define __NR_epoll_ctl                    (__NR_SYSCALL_BASE + 251)
#define __NR_epoll_wait                   (__NR_SYSCALL_BASE + 252)
#define __NR_timer_create                 (__NR_SYSCALL_BASE + 257)
#define __NR_timer_settime                (__NR_SYSCALL_BASE + 258)
#define __NR_timer_gettime                (__NR_SYSCALL_BASE + 259)
#define __NR_timer_getoverrun             (__NR_SYSCALL_BASE + 260)
#define __NR_timer_delete                 (__NR_SYSCALL_BASE + 261)
#define __NR_clock_settime                (__NR_SYSCALL_BASE + 262)
#define __NR_clock_gettime                (__NR_SYSCALL_BASE + 263)
#define __NR_clock_getres                 (__NR_SYSCALL_BASE + 264)
#define __NR_clock_nanosleep              (__NR_SYSCALL_BASE + 265)
#define __NR_statfs64                     (__NR_SYSCALL_BASE + 266)
#define __NR_fstatfs64                    (__NR_SYSCALL_BASE + 267)
#define __NR_utimes                       (__NR_SYSCALL_BASE + 269)
#define __NR_waitid                       (__NR_SYSCALL_BASE + 280)
#define __NR_socket                       (__NR_SYSCALL_BASE + 281)
#define __NR_bind                         (__NR_SYSCALL_BASE + 282)
#define __NR_connect                      (__NR_SYSCALL_BASE + 283)
#define __NR_listen                       (__NR_SYSCALL_BASE + 284)
#define __NR_accept                       (__NR_SYSCALL_BASE + 285)
#define __NR_getsockname                  (__NR_SYSCALL_BASE + 286)
#define __NR_getpeername                  (__NR_SYSCALL_BASE + 287)
#define __NR_socketpair                   (__NR_SYSCALL_BASE + 288)
#define __NR_sendto                       (__NR_SYSCALL_BASE + 290)
#define __NR_recvfrom                     (__NR_SYSCALL_BASE + 292)
#define __NR_shutdown                     (__NR_SYSCALL_BASE + 293)
#define __NR_setsockopt                   (__NR_SYSCALL_BASE + 294)
#define __NR_getsockopt                   (__NR_SYSCALL_BASE + 295)
#define __NR_sendmsg                      (__NR_SYSCALL_BASE + 296)
#define __NR_recvmsg                      (__NR_SYSCALL_BASE + 297)
#define __NR_ioprio_set                   (__NR_SYSCALL_BASE + 314)
#define __NR_ioprio_get                   (__NR_SYSCALL_BASE + 315)
#define __NR_inotify_init                 (__NR_SYSCALL_BASE + 316)
#define __NR_inotify_add_watch            (__NR_SYSCALL_BASE + 317)
#define __NR_inotify_rm_watch             (__NR_SYSCALL_BASE + 318)
#define __NR_openat                       (__NR_SYSCALL_BASE + 322)
#define __NR_mkdirat                      (__NR_SYSCALL_BASE + 323)
#define __NR_fchownat                     (__NR_SYSCALL_BASE + 325)
#define __NR_fstatat64                    (__NR_SYSCALL_BASE + 327)
#define __NR_unlinkat                     (__NR_SYSCALL_BASE + 328)
#define __NR_renameat                     (__NR_SYSCALL_BASE + 329)
#define __NR_fchmodat                     (__NR_SYSCALL_BASE + 333)
#define __NR_getcpu                       (__NR_SYSCALL_BASE + 345)
#define __NR_utimensat                    (__NR_SYSCALL_BASE + 348)
#define __NR_eventfd2                     (__NR_SYSCALL_BASE + 356)
#define __NR_pipe2                        (__NR_SYSCALL_BASE + 359)
#define __NR_ARM_cacheflush               (__NR_SYSCALL_BASE + 983042)
#define __NR_ARM_set_tls                  (__NR_SYSCALL_BASE + 983045)
#endif

#ifdef __i386__
#define __NR_waitpid                      (__NR_SYSCALL_BASE + 7)
#define __NR_kill                         (__NR_SYSCALL_BASE + 37)
#define __NR_pipe                         (__NR_SYSCALL_BASE + 42)
#define __NR_socketcall                   (__NR_SYSCALL_BASE + 102)
#define __NR_fdatasync                    (__NR_SYSCALL_BASE + 148)
#define __NR_mlock                        (__NR_SYSCALL_BASE + 150)
#define __NR_munlock                      (__NR_SYSCALL_BASE + 151)
#define __NR_sched_setparam               (__NR_SYSCALL_BASE + 154)
#define __NR_sched_getparam               (__NR_SYSCALL_BASE + 155)
#define __NR_sched_setscheduler           (__NR_SYSCALL_BASE + 156)
#define __NR_sched_getscheduler           (__NR_SYSCALL_BASE + 157)
#define __NR_sched_yield                  (__NR_SYSCALL_BASE + 158)
#define __NR_sched_get_priority_max       (__NR_SYSCALL_BASE + 159)
#define __NR_sched_get_priority_min       (__NR_SYSCALL_BASE + 160)
#define __NR_sched_rr_get_interval        (__NR_SYSCALL_BASE + 161)
#define __NR_nanosleep                    (__NR_SYSCALL_BASE + 162)
#define __NR_mremap                       (__NR_SYSCALL_BASE + 163)
#define __NR_poll                         (__NR_SYSCALL_BASE + 168)
#define __NR_prctl                        (__NR_SYSCALL_BASE + 172)
#define __NR_rt_sigaction                 (__NR_SYSCALL_BASE + 174)
#define __NR_rt_sigprocmask               (__NR_SYSCALL_BASE + 175)
#define __NR_rt_sigtimedwait              (__NR_SYSCALL_BASE + 177)
#define __NR_pread64                      (__NR_SYSCALL_BASE + 180)
#define __NR_pwrite64                     (__NR_SYSCALL_BASE + 181)
#define __NR_getcwd                       (__NR_SYSCALL_BASE + 183)
#define __NR_capget                       (__NR_SYSCALL_BASE + 184)
#define __NR_capset                       (__NR_SYSCALL_BASE + 185)
#define __NR_sigaltstack                  (__NR_SYSCALL_BASE + 186)
#define __NR_sendfile                     (__NR_SYSCALL_BASE + 187)
#define __NR_ugetrlimit                   (__NR_SYSCALL_BASE + 191)
#define __NR_mmap2                        (__NR_SYSCALL_BASE + 192)
#define __NR_ftruncate64                  (__NR_SYSCALL_BASE + 194)
#define __NR_stat64                       (__NR_SYSCALL_BASE + 195)
#define __NR_lstat64                      (__NR_SYSCALL_BASE + 196)
#define __NR_fstat64                      (__NR_SYSCALL_BASE + 197)
#define __NR_lchown32                     (__NR_SYSCALL_BASE + 198)
#define __NR_getuid32                     (__NR_SYSCALL_BASE + 199)
#define __NR_getgid32                     (__NR_SYSCALL_BASE + 200)
#define __NR_geteuid32                    (__NR_SYSCALL_BASE + 201)
#define __NR_getegid32                    (__NR_SYSCALL_BASE + 202)
#define __NR_setreuid32                   (__NR_SYSCALL_BASE + 203)
#define __NR_setregid32                   (__NR_SYSCALL_BASE + 204)
#define __NR_getgroups32                  (__NR_SYSCALL_BASE + 205)
#define __NR_setgroups32                  (__NR_SYSCALL_BASE + 206)
#define __NR_fchown32                     (__NR_SYSCALL_BASE + 207)
#define __NR_setresuid32                  (__NR_SYSCALL_BASE + 208)
#define __NR_getresuid32                  (__NR_SYSCALL_BASE + 209)
#define __NR_setresgid32                  (__NR_SYSCALL_BASE + 210)
#define __NR_getresgid32                  (__NR_SYSCALL_BASE + 211)
#define __NR_chown32                      (__NR_SYSCALL_BASE + 212)
#define __NR_setuid32                     (__NR_SYSCALL_BASE + 213)
#define __NR_setgid32                     (__NR_SYSCALL_BASE + 214)
#define __NR_mincore                      (__NR_SYSCALL_BASE + 218)
#define __NR_madvise                      (__NR_SYSCALL_BASE + 219)
#define __NR_getdents64                   (__NR_SYSCALL_BASE + 220)
#define __NR_fcntl64                      (__NR_SYSCALL_BASE + 221)
#define __NR_gettid                       (__NR_SYSCALL_BASE + 224)
#define __NR_tkill                        (__NR_SYSCALL_BASE + 238)
#define __NR_futex                        (__NR_SYSCALL_BASE + 240)
#define __NR_sched_setaffinity            (__NR_SYSCALL_BASE + 241)
#define __NR_sched_getaffinity            (__NR_SYSCALL_BASE + 242)
#define __NR_set_thread_area              (__NR_SYSCALL_BASE + 243)
#define __NR_exit_group                   (__NR_SYSCALL_BASE + 252)
#define __NR_epoll_create                 (__NR_SYSCALL_BASE + 254)
#define __NR_epoll_ctl                    (__NR_SYSCALL_BASE + 255)
#define __NR_epoll_wait                   (__NR_SYSCALL_BASE + 256)
#define __NR_timer_create                 (__NR_SYSCALL_BASE + 259)
#define __NR_timer_settime                (__NR_SYSCALL_BASE + 260)
#define __NR_timer_gettime                (__NR_SYSCALL_BASE + 261)
#define __NR_timer_getoverrun             (__NR_SYSCALL_BASE + 262)
#define __NR_timer_delete                 (__NR_SYSCALL_BASE + 263)
#define __NR_clock_settime                (__NR_SYSCALL_BASE + 264)
#define __NR_clock_gettime                (__NR_SYSCALL_BASE + 265)
#define __NR_clock_getres                 (__NR_SYSCALL_BASE + 266)
#define __NR_clock_nanosleep              (__NR_SYSCALL_BASE + 267)
#define __NR_statfs64                     (__NR_SYSCALL_BASE + 268)
#define __NR_fstatfs64                    (__NR_SYSCALL_BASE + 269)
#define __NR_utimes                       (__NR_SYSCALL_BASE + 271)
#define __NR_waitid                       (__NR_SYSCALL_BASE + 284)
#define __NR_ioprio_set                   (__NR_SYSCALL_BASE + 289)
#define __NR_ioprio_get                   (__NR_SYSCALL_BASE + 290)
#define __NR_inotify_init                 (__NR_SYSCALL_BASE + 291)
#define __NR_inotify_add_watch            (__NR_SYSCALL_BASE + 292)
#define __NR_inotify_rm_watch             (__NR_SYSCALL_BASE + 293)
#define __NR_openat                       (__NR_SYSCALL_BASE + 295)
#define __NR_mkdirat                      (__NR_SYSCALL_BASE + 296)
#define __NR_fchownat                     (__NR_SYSCALL_BASE + 298)
#define __NR_fstatat64                    (__NR_SYSCALL_BASE + 300)
#define __NR_unlinkat                     (__NR_SYSCALL_BASE + 301)
#define __NR_renameat                     (__NR_SYSCALL_BASE + 302)
#define __NR_fchmodat                     (__NR_SYSCALL_BASE + 306)
#define __NR_getcpu                       (__NR_SYSCALL_BASE + 318)
#define __NR_utimensat                    (__NR_SYSCALL_BASE + 320)
#define __NR_eventfd2                     (__NR_SYSCALL_BASE + 328)
#define __NR_pipe2                        (__NR_SYSCALL_BASE + 331)
#endif

#if defined(__SH3__) || defined(__SH4__) 
#define __NR_waitpid                      (__NR_SYSCALL_BASE + 7)
#define __NR_kill                         (__NR_SYSCALL_BASE + 37)
#define __NR_socketcall                   (__NR_SYSCALL_BASE + 102)
#define __NR_fdatasync                    (__NR_SYSCALL_BASE + 148)
#define __NR_mlock                        (__NR_SYSCALL_BASE + 150)
#define __NR_munlock                      (__NR_SYSCALL_BASE + 151)
#define __NR_sched_setparam               (__NR_SYSCALL_BASE + 154)
#define __NR_sched_getparam               (__NR_SYSCALL_BASE + 155)
#define __NR_sched_setscheduler           (__NR_SYSCALL_BASE + 156)
#define __NR_sched_getscheduler           (__NR_SYSCALL_BASE + 157)
#define __NR_sched_yield                  (__NR_SYSCALL_BASE + 158)
#define __NR_sched_get_priority_max       (__NR_SYSCALL_BASE + 159)
#define __NR_sched_get_priority_min       (__NR_SYSCALL_BASE + 160)
#define __NR_sched_rr_get_interval        (__NR_SYSCALL_BASE + 161)
#define __NR_nanosleep                    (__NR_SYSCALL_BASE + 162)
#define __NR_mremap                       (__NR_SYSCALL_BASE + 163)
#define __NR_poll                         (__NR_SYSCALL_BASE + 168)
#define __NR_prctl                        (__NR_SYSCALL_BASE + 172)
#define __NR_rt_sigaction                 (__NR_SYSCALL_BASE + 174)
#define __NR_rt_sigprocmask               (__NR_SYSCALL_BASE + 175)
#define __NR_rt_sigtimedwait              (__NR_SYSCALL_BASE + 177)
#define __NR_pread64                      (__NR_SYSCALL_BASE + 180)
#define __NR_pwrite64                     (__NR_SYSCALL_BASE + 181)
#define __NR_getcwd                       (__NR_SYSCALL_BASE + 183)
#define __NR_capget                       (__NR_SYSCALL_BASE + 184)
#define __NR_capset                       (__NR_SYSCALL_BASE + 185)
#define __NR_sigaltstack                  (__NR_SYSCALL_BASE + 186)
#define __NR_sendfile                     (__NR_SYSCALL_BASE + 187)
#define __NR_vfork                        (__NR_SYSCALL_BASE + 190)
#define __NR_ugetrlimit                   (__NR_SYSCALL_BASE + 191)
#define __NR_mmap2                        (__NR_SYSCALL_BASE + 192)
#define __NR_ftruncate64                  (__NR_SYSCALL_BASE + 194)
#define __NR_stat64                       (__NR_SYSCALL_BASE + 195)
#define __NR_lstat64                      (__NR_SYSCALL_BASE + 196)
#define __NR_fstat64                      (__NR_SYSCALL_BASE + 197)
#define __NR_lchown32                     (__NR_SYSCALL_BASE + 198)
#define __NR_getuid32                     (__NR_SYSCALL_BASE + 199)
#define __NR_getgid32                     (__NR_SYSCALL_BASE + 200)
#define __NR_geteuid32                    (__NR_SYSCALL_BASE + 201)
#define __NR_getegid32                    (__NR_SYSCALL_BASE + 202)
#define __NR_setreuid32                   (__NR_SYSCALL_BASE + 203)
#define __NR_setregid32                   (__NR_SYSCALL_BASE + 204)
#define __NR_getgroups32                  (__NR_SYSCALL_BASE + 205)
#define __NR_setgroups32                  (__NR_SYSCALL_BASE + 206)
#define __NR_fchown32                     (__NR_SYSCALL_BASE + 207)
#define __NR_setresuid32                  (__NR_SYSCALL_BASE + 208)
#define __NR_getresuid32                  (__NR_SYSCALL_BASE + 209)
#define __NR_setresgid32                  (__NR_SYSCALL_BASE + 210)
#define __NR_getresgid32                  (__NR_SYSCALL_BASE + 211)
#define __NR_chown32                      (__NR_SYSCALL_BASE + 212)
#define __NR_setuid32                     (__NR_SYSCALL_BASE + 213)
#define __NR_setgid32                     (__NR_SYSCALL_BASE + 214)
#define __NR_mincore                      (__NR_SYSCALL_BASE + 218)
#define __NR_madvise                      (__NR_SYSCALL_BASE + 219)
#define __NR_getdents64                   (__NR_SYSCALL_BASE + 220)
#define __NR_fcntl64                      (__NR_SYSCALL_BASE + 221)
#define __NR_gettid                       (__NR_SYSCALL_BASE + 224)
#define __NR_tkill                        (__NR_SYSCALL_BASE + 238)
#define __NR_futex                        (__NR_SYSCALL_BASE + 240)
#define __NR_sched_setaffinity            (__NR_SYSCALL_BASE + 241)
#define __NR_sched_getaffinity            (__NR_SYSCALL_BASE + 242)
#define __NR_set_thread_area              (__NR_SYSCALL_BASE + 243)
#define __NR_exit_group                   (__NR_SYSCALL_BASE + 252)
#define __NR_epoll_create                 (__NR_SYSCALL_BASE + 254)
#define __NR_epoll_ctl                    (__NR_SYSCALL_BASE + 255)
#define __NR_epoll_wait                   (__NR_SYSCALL_BASE + 256)
#define __NR_timer_create                 (__NR_SYSCALL_BASE + 259)
#define __NR_timer_settime                (__NR_SYSCALL_BASE + 260)
#define __NR_timer_gettime                (__NR_SYSCALL_BASE + 261)
#define __NR_timer_getoverrun             (__NR_SYSCALL_BASE + 262)
#define __NR_timer_delete                 (__NR_SYSCALL_BASE + 263)
#define __NR_clock_settime                (__NR_SYSCALL_BASE + 264)
#define __NR_clock_gettime                (__NR_SYSCALL_BASE + 265)
#define __NR_clock_getres                 (__NR_SYSCALL_BASE + 266)
#define __NR_clock_nanosleep              (__NR_SYSCALL_BASE + 267)
#define __NR_statfs64                     (__NR_SYSCALL_BASE + 268)
#define __NR_fstatfs64                    (__NR_SYSCALL_BASE + 269)
#define __NR_utimes                       (__NR_SYSCALL_BASE + 271)
#define __NR_waitid                       (__NR_SYSCALL_BASE + 284)
#define __NR_ioprio_set                   (__NR_SYSCALL_BASE + 288)
#define __NR_ioprio_get                   (__NR_SYSCALL_BASE + 289)
#define __NR_inotify_init                 (__NR_SYSCALL_BASE + 290)
#define __NR_inotify_add_watch            (__NR_SYSCALL_BASE + 291)
#define __NR_inotify_rm_watch             (__NR_SYSCALL_BASE + 292)
#define __NR_openat                       (__NR_SYSCALL_BASE + 295)
#define __NR_mkdirat                      (__NR_SYSCALL_BASE + 296)
#define __NR_fchownat                     (__NR_SYSCALL_BASE + 298)
#define __NR_fstatat64                    (__NR_SYSCALL_BASE + 300)
#define __NR_unlinkat                     (__NR_SYSCALL_BASE + 301)
#define __NR_renameat                     (__NR_SYSCALL_BASE + 302)
#define __NR_fchmodat                     (__NR_SYSCALL_BASE + 306)
#define __NR_getcpu                       (__NR_SYSCALL_BASE + 318)
#define __NR_utimensat                    (__NR_SYSCALL_BASE + 320)
#define __NR_eventfd2                     (__NR_SYSCALL_BASE + 328)
#define __NR_pipe2                        (__NR_SYSCALL_BASE + 331)
#endif

#ifdef __mips__
#define __NR_syscall                      (__NR_SYSCALL_BASE + 0)
#define __NR_waitpid                      (__NR_SYSCALL_BASE + 7)
#define __NR_lchown                       (__NR_SYSCALL_BASE + 16)
#define __NR_setuid                       (__NR_SYSCALL_BASE + 23)
#define __NR_getuid                       (__NR_SYSCALL_BASE + 24)
#define __NR_kill                         (__NR_SYSCALL_BASE + 37)
#define __NR_setgid                       (__NR_SYSCALL_BASE + 46)
#define __NR_getgid                       (__NR_SYSCALL_BASE + 47)
#define __NR_geteuid                      (__NR_SYSCALL_BASE + 49)
#define __NR_getegid                      (__NR_SYSCALL_BASE + 50)
#define __NR_setreuid                     (__NR_SYSCALL_BASE + 70)
#define __NR_setregid                     (__NR_SYSCALL_BASE + 71)
#define __NR_getrlimit                    (__NR_SYSCALL_BASE + 76)
#define __NR_getgroups                    (__NR_SYSCALL_BASE + 80)
#define __NR_setgroups                    (__NR_SYSCALL_BASE + 81)
#define __NR_fchown                       (__NR_SYSCALL_BASE + 95)
#define __NR_cacheflush                   (__NR_SYSCALL_BASE + 147)
#define __NR_fdatasync                    (__NR_SYSCALL_BASE + 152)
#define __NR_mlock                        (__NR_SYSCALL_BASE + 154)
#define __NR_munlock                      (__NR_SYSCALL_BASE + 155)
#define __NR_sched_setparam               (__NR_SYSCALL_BASE + 158)
#define __NR_sched_getparam               (__NR_SYSCALL_BASE + 159)
#define __NR_sched_setscheduler           (__NR_SYSCALL_BASE + 160)
#define __NR_sched_getscheduler           (__NR_SYSCALL_BASE + 161)
#define __NR_sched_yield                  (__NR_SYSCALL_BASE + 162)
#define __NR_sched_get_priority_max       (__NR_SYSCALL_BASE + 163)
#define __NR_sched_get_priority_min       (__NR_SYSCALL_BASE + 164)
#define __NR_sched_rr_get_interval        (__NR_SYSCALL_BASE + 165)
#define __NR_nanosleep                    (__NR_SYSCALL_BASE + 166)
#define __NR_mremap                       (__NR_SYSCALL_BASE + 167)
#define __NR_accept                       (__NR_SYSCALL_BASE + 168)
#define __NR_bind                         (__NR_SYSCALL_BASE + 169)
#define __NR_connect                      (__NR_SYSCALL_BASE + 170)
#define __NR_getpeername                  (__NR_SYSCALL_BASE + 171)
#define __NR_getsockname                  (__NR_SYSCALL_BASE + 172)
#define __NR_getsockopt                   (__NR_SYSCALL_BASE + 173)
#define __NR_listen                       (__NR_SYSCALL_BASE + 174)
#define __NR_recvfrom                     (__NR_SYSCALL_BASE + 176)
#define __NR_recvmsg                      (__NR_SYSCALL_BASE + 177)
#define __NR_sendmsg                      (__NR_SYSCALL_BASE + 179)
#define __NR_sendto                       (__NR_SYSCALL_BASE + 180)
#define __NR_setsockopt                   (__NR_SYSCALL_BASE + 181)
#define __NR_shutdown                     (__NR_SYSCALL_BASE + 182)
#define __NR_socket                       (__NR_SYSCALL_BASE + 183)
#define __NR_socketpair                   (__NR_SYSCALL_BASE + 184)
#define __NR_setresuid                    (__NR_SYSCALL_BASE + 185)
#define __NR_getresuid                    (__NR_SYSCALL_BASE + 186)
#define __NR_poll                         (__NR_SYSCALL_BASE + 188)
#define __NR_setresgid                    (__NR_SYSCALL_BASE + 190)
#define __NR_getresgid                    (__NR_SYSCALL_BASE + 191)
#define __NR_prctl                        (__NR_SYSCALL_BASE + 192)
#define __NR_rt_sigaction                 (__NR_SYSCALL_BASE + 194)
#define __NR_rt_sigprocmask               (__NR_SYSCALL_BASE + 195)
#define __NR_rt_sigtimedwait              (__NR_SYSCALL_BASE + 197)
#define __NR_pread64                      (__NR_SYSCALL_BASE + 200)
#define __NR_pwrite64                     (__NR_SYSCALL_BASE + 201)
#define __NR_chown                        (__NR_SYSCALL_BASE + 202)
#define __NR_getcwd                       (__NR_SYSCALL_BASE + 203)
#define __NR_capget                       (__NR_SYSCALL_BASE + 204)
#define __NR_capset                       (__NR_SYSCALL_BASE + 205)
#define __NR_sigaltstack                  (__NR_SYSCALL_BASE + 206)
#define __NR_sendfile                     (__NR_SYSCALL_BASE + 207)
#define __NR_mmap2                        (__NR_SYSCALL_BASE + 210)
#define __NR_ftruncate64                  (__NR_SYSCALL_BASE + 212)
#define __NR_stat64                       (__NR_SYSCALL_BASE + 213)
#define __NR_lstat64                      (__NR_SYSCALL_BASE + 214)
#define __NR_fstat64                      (__NR_SYSCALL_BASE + 215)
#define __NR_mincore                      (__NR_SYSCALL_BASE + 217)
#define __NR_madvise                      (__NR_SYSCALL_BASE + 218)
#define __NR_getdents64                   (__NR_SYSCALL_BASE + 219)
#define __NR_fcntl64                      (__NR_SYSCALL_BASE + 220)
#define __NR_gettid                       (__NR_SYSCALL_BASE + 222)
#define __NR_tkill                        (__NR_SYSCALL_BASE + 236)
#define __NR_futex                        (__NR_SYSCALL_BASE + 238)
#define __NR_sched_setaffinity            (__NR_SYSCALL_BASE + 239)
#define __NR_sched_getaffinity            (__NR_SYSCALL_BASE + 240)
#define __NR_exit_group                   (__NR_SYSCALL_BASE + 246)
#define __NR_epoll_create                 (__NR_SYSCALL_BASE + 248)
#define __NR_epoll_ctl                    (__NR_SYSCALL_BASE + 249)
#define __NR_epoll_wait                   (__NR_SYSCALL_BASE + 250)
#define __NR_statfs64                     (__NR_SYSCALL_BASE + 255)
#define __NR_fstatfs64                    (__NR_SYSCALL_BASE + 256)
#define __NR_timer_create                 (__NR_SYSCALL_BASE + 257)
#define __NR_timer_settime                (__NR_SYSCALL_BASE + 258)
#define __NR_timer_gettime                (__NR_SYSCALL_BASE + 259)
#define __NR_timer_getoverrun             (__NR_SYSCALL_BASE + 260)
#define __NR_timer_delete                 (__NR_SYSCALL_BASE + 261)
#define __NR_clock_settime                (__NR_SYSCALL_BASE + 262)
#define __NR_clock_gettime                (__NR_SYSCALL_BASE + 263)
#define __NR_clock_getres                 (__NR_SYSCALL_BASE + 264)
#define __NR_clock_nanosleep              (__NR_SYSCALL_BASE + 265)
#define __NR_utimes                       (__NR_SYSCALL_BASE + 267)
#define __NR_waitid                       (__NR_SYSCALL_BASE + 278)
#define __NR_set_thread_area              (__NR_SYSCALL_BASE + 283)
#define __NR_inotify_init                 (__NR_SYSCALL_BASE + 284)
#define __NR_inotify_add_watch            (__NR_SYSCALL_BASE + 285)
#define __NR_inotify_rm_watch             (__NR_SYSCALL_BASE + 286)
#define __NR_openat                       (__NR_SYSCALL_BASE + 288)
#define __NR_mkdirat                      (__NR_SYSCALL_BASE + 289)
#define __NR_fchownat                     (__NR_SYSCALL_BASE + 291)
#define __NR_fstatat64                    (__NR_SYSCALL_BASE + 293)
#define __NR_unlinkat                     (__NR_SYSCALL_BASE + 294)
#define __NR_renameat                     (__NR_SYSCALL_BASE + 295)
#define __NR_fchmodat                     (__NR_SYSCALL_BASE + 299)
#define __NR_getcpu                       (__NR_SYSCALL_BASE + 312)
#define __NR_ioprio_set                   (__NR_SYSCALL_BASE + 314)
#define __NR_ioprio_get                   (__NR_SYSCALL_BASE + 315)
#define __NR_utimensat                    (__NR_SYSCALL_BASE + 316)
#define __NR_eventfd2                     (__NR_SYSCALL_BASE + 325)
#define __NR_pipe2                        (__NR_SYSCALL_BASE + 328)
#endif

#endif

#endif /* _BIONIC_LINUX_SYSCALLS_H_ */
