/****************************************************************************
 ****************************************************************************
 ***
 ***   This header was automatically generated from a Linux kernel header
 ***   of the same name, to make information necessary for userspace to
 ***   call into the kernel available to libc.  It contains only constants,
 ***   structures, and macros generated from the original header, and thus,
 ***   contains no copyrightable information.
 ***
 ***   To edit the content of this header, modify the corresponding
 ***   source file (e.g. under external/kernel-headers/original/) then
 ***   run bionic/libc/kernel/tools/update_all.py
 ***
 ***   Any manual change here will be lost the next time this script will
 ***   be run. You've been warned!
 ***
 ****************************************************************************
 ****************************************************************************/
#ifndef _ASM_FCNTL_H
#define _ASM_FCNTL_H
#define O_APPEND 0x0008
#define O_DSYNC 0x0010
/* WARNING: DO NOT EDIT, AUTO-GENERATED CODE - SEE TOP FOR INSTRUCTIONS */
#define O_NONBLOCK 0x0080
#define O_CREAT 0x0100
#define O_TRUNC 0x0200
#define O_EXCL 0x0400
/* WARNING: DO NOT EDIT, AUTO-GENERATED CODE - SEE TOP FOR INSTRUCTIONS */
#define O_NOCTTY 0x0800
#define FASYNC 0x1000
#define O_LARGEFILE 0x2000
#define __O_SYNC 0x4000
/* WARNING: DO NOT EDIT, AUTO-GENERATED CODE - SEE TOP FOR INSTRUCTIONS */
#define O_SYNC (__O_SYNC|O_DSYNC)
#define O_DIRECT 0x8000
#define F_GETLK 14
#define F_SETLK 6
/* WARNING: DO NOT EDIT, AUTO-GENERATED CODE - SEE TOP FOR INSTRUCTIONS */
#define F_SETLKW 7
#define F_SETOWN 24
#define F_GETOWN 23
#ifndef __mips64
/* WARNING: DO NOT EDIT, AUTO-GENERATED CODE - SEE TOP FOR INSTRUCTIONS */
#define F_GETLK64 33
#define F_SETLK64 34
#define F_SETLKW64 35
#endif
/* WARNING: DO NOT EDIT, AUTO-GENERATED CODE - SEE TOP FOR INSTRUCTIONS */
#include <linux/types.h>
struct flock {
 short l_type;
 short l_whence;
/* WARNING: DO NOT EDIT, AUTO-GENERATED CODE - SEE TOP FOR INSTRUCTIONS */
 __kernel_off_t l_start;
 __kernel_off_t l_len;
 long l_sysid;
 __kernel_pid_t l_pid;
/* WARNING: DO NOT EDIT, AUTO-GENERATED CODE - SEE TOP FOR INSTRUCTIONS */
 long pad[4];
};
#define HAVE_ARCH_STRUCT_FLOCK
#include <asm-generic/fcntl.h>
/* WARNING: DO NOT EDIT, AUTO-GENERATED CODE - SEE TOP FOR INSTRUCTIONS */
#endif
