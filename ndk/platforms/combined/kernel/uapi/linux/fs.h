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
#ifndef _UAPI_LINUX_FS_H
#define _UAPI_LINUX_FS_H
#include <linux/limits.h>
#include <linux/ioctl.h>
/* WARNING: DO NOT EDIT, AUTO-GENERATED CODE - SEE TOP FOR INSTRUCTIONS */
#include <linux/types.h>
#undef NR_OPEN
#define INR_OPEN_CUR 1024
#define INR_OPEN_MAX 4096
/* WARNING: DO NOT EDIT, AUTO-GENERATED CODE - SEE TOP FOR INSTRUCTIONS */
#define BLOCK_SIZE_BITS 10
#define BLOCK_SIZE (1<<BLOCK_SIZE_BITS)
#define SEEK_SET 0
#define SEEK_CUR 1
/* WARNING: DO NOT EDIT, AUTO-GENERATED CODE - SEE TOP FOR INSTRUCTIONS */
#define SEEK_END 2
#define SEEK_DATA 3
#define SEEK_HOLE 4
#define SEEK_MAX SEEK_HOLE
/* WARNING: DO NOT EDIT, AUTO-GENERATED CODE - SEE TOP FOR INSTRUCTIONS */
#define RENAME_NOREPLACE (1 << 0)
#define RENAME_EXCHANGE (1 << 1)
#define RENAME_WHITEOUT (1 << 2)
struct fstrim_range {
/* WARNING: DO NOT EDIT, AUTO-GENERATED CODE - SEE TOP FOR INSTRUCTIONS */
 __u64 start;
 __u64 len;
 __u64 minlen;
};
/* WARNING: DO NOT EDIT, AUTO-GENERATED CODE - SEE TOP FOR INSTRUCTIONS */
struct files_stat_struct {
 unsigned long nr_files;
 unsigned long nr_free_files;
 unsigned long max_files;
/* WARNING: DO NOT EDIT, AUTO-GENERATED CODE - SEE TOP FOR INSTRUCTIONS */
};
struct inodes_stat_t {
 long nr_inodes;
 long nr_unused;
/* WARNING: DO NOT EDIT, AUTO-GENERATED CODE - SEE TOP FOR INSTRUCTIONS */
 long dummy[5];
};
#define NR_FILE 8192
#define MS_RDONLY 1
/* WARNING: DO NOT EDIT, AUTO-GENERATED CODE - SEE TOP FOR INSTRUCTIONS */
#define MS_NOSUID 2
#define MS_NODEV 4
#define MS_NOEXEC 8
#define MS_SYNCHRONOUS 16
/* WARNING: DO NOT EDIT, AUTO-GENERATED CODE - SEE TOP FOR INSTRUCTIONS */
#define MS_REMOUNT 32
#define MS_MANDLOCK 64
#define MS_DIRSYNC 128
#define MS_NOATIME 1024
/* WARNING: DO NOT EDIT, AUTO-GENERATED CODE - SEE TOP FOR INSTRUCTIONS */
#define MS_NODIRATIME 2048
#define MS_BIND 4096
#define MS_MOVE 8192
#define MS_REC 16384
/* WARNING: DO NOT EDIT, AUTO-GENERATED CODE - SEE TOP FOR INSTRUCTIONS */
#define MS_VERBOSE 32768
#define MS_SILENT 32768
#define MS_POSIXACL (1<<16)
#define MS_UNBINDABLE (1<<17)
/* WARNING: DO NOT EDIT, AUTO-GENERATED CODE - SEE TOP FOR INSTRUCTIONS */
#define MS_PRIVATE (1<<18)
#define MS_SLAVE (1<<19)
#define MS_SHARED (1<<20)
#define MS_RELATIME (1<<21)
/* WARNING: DO NOT EDIT, AUTO-GENERATED CODE - SEE TOP FOR INSTRUCTIONS */
#define MS_KERNMOUNT (1<<22)
#define MS_I_VERSION (1<<23)
#define MS_STRICTATIME (1<<24)
#define MS_NOSEC (1<<28)
/* WARNING: DO NOT EDIT, AUTO-GENERATED CODE - SEE TOP FOR INSTRUCTIONS */
#define MS_BORN (1<<29)
#define MS_ACTIVE (1<<30)
#define MS_NOUSER (1<<31)
#define MS_RMT_MASK (MS_RDONLY|MS_SYNCHRONOUS|MS_MANDLOCK|MS_I_VERSION)
/* WARNING: DO NOT EDIT, AUTO-GENERATED CODE - SEE TOP FOR INSTRUCTIONS */
#define MS_MGC_VAL 0xC0ED0000
#define MS_MGC_MSK 0xffff0000
#define BLKROSET _IO(0x12,93)
#define BLKROGET _IO(0x12,94)
/* WARNING: DO NOT EDIT, AUTO-GENERATED CODE - SEE TOP FOR INSTRUCTIONS */
#define BLKRRPART _IO(0x12,95)
#define BLKGETSIZE _IO(0x12,96)
#define BLKFLSBUF _IO(0x12,97)
#define BLKRASET _IO(0x12,98)
/* WARNING: DO NOT EDIT, AUTO-GENERATED CODE - SEE TOP FOR INSTRUCTIONS */
#define BLKRAGET _IO(0x12,99)
#define BLKFRASET _IO(0x12,100)
#define BLKFRAGET _IO(0x12,101)
#define BLKSECTSET _IO(0x12,102)
/* WARNING: DO NOT EDIT, AUTO-GENERATED CODE - SEE TOP FOR INSTRUCTIONS */
#define BLKSECTGET _IO(0x12,103)
#define BLKSSZGET _IO(0x12,104)
#define BLKBSZGET _IOR(0x12,112,size_t)
#define BLKBSZSET _IOW(0x12,113,size_t)
/* WARNING: DO NOT EDIT, AUTO-GENERATED CODE - SEE TOP FOR INSTRUCTIONS */
#define BLKGETSIZE64 _IOR(0x12,114,size_t)
#define BLKTRACESETUP _IOWR(0x12,115,struct blk_user_trace_setup)
#define BLKTRACESTART _IO(0x12,116)
#define BLKTRACESTOP _IO(0x12,117)
/* WARNING: DO NOT EDIT, AUTO-GENERATED CODE - SEE TOP FOR INSTRUCTIONS */
#define BLKTRACETEARDOWN _IO(0x12,118)
#define BLKDISCARD _IO(0x12,119)
#define BLKIOMIN _IO(0x12,120)
#define BLKIOOPT _IO(0x12,121)
/* WARNING: DO NOT EDIT, AUTO-GENERATED CODE - SEE TOP FOR INSTRUCTIONS */
#define BLKALIGNOFF _IO(0x12,122)
#define BLKPBSZGET _IO(0x12,123)
#define BLKDISCARDZEROES _IO(0x12,124)
#define BLKSECDISCARD _IO(0x12,125)
/* WARNING: DO NOT EDIT, AUTO-GENERATED CODE - SEE TOP FOR INSTRUCTIONS */
#define BLKROTATIONAL _IO(0x12,126)
#define BLKZEROOUT _IO(0x12,127)
#define BMAP_IOCTL 1
#define FIBMAP _IO(0x00,1)
/* WARNING: DO NOT EDIT, AUTO-GENERATED CODE - SEE TOP FOR INSTRUCTIONS */
#define FIGETBSZ _IO(0x00,2)
#define FIFREEZE _IOWR('X', 119, int)
#define FITHAW _IOWR('X', 120, int)
#define FITRIM _IOWR('X', 121, struct fstrim_range)
/* WARNING: DO NOT EDIT, AUTO-GENERATED CODE - SEE TOP FOR INSTRUCTIONS */
#define FS_IOC_GETFLAGS _IOR('f', 1, long)
#define FS_IOC_SETFLAGS _IOW('f', 2, long)
#define FS_IOC_GETVERSION _IOR('v', 1, long)
#define FS_IOC_SETVERSION _IOW('v', 2, long)
/* WARNING: DO NOT EDIT, AUTO-GENERATED CODE - SEE TOP FOR INSTRUCTIONS */
#define FS_IOC_FIEMAP _IOWR('f', 11, struct fiemap)
#define FS_IOC32_GETFLAGS _IOR('f', 1, int)
#define FS_IOC32_SETFLAGS _IOW('f', 2, int)
#define FS_IOC32_GETVERSION _IOR('v', 1, int)
/* WARNING: DO NOT EDIT, AUTO-GENERATED CODE - SEE TOP FOR INSTRUCTIONS */
#define FS_IOC32_SETVERSION _IOW('v', 2, int)
#define FS_SECRM_FL 0x00000001
#define FS_UNRM_FL 0x00000002
#define FS_COMPR_FL 0x00000004
/* WARNING: DO NOT EDIT, AUTO-GENERATED CODE - SEE TOP FOR INSTRUCTIONS */
#define FS_SYNC_FL 0x00000008
#define FS_IMMUTABLE_FL 0x00000010
#define FS_APPEND_FL 0x00000020
#define FS_NODUMP_FL 0x00000040
/* WARNING: DO NOT EDIT, AUTO-GENERATED CODE - SEE TOP FOR INSTRUCTIONS */
#define FS_NOATIME_FL 0x00000080
#define FS_DIRTY_FL 0x00000100
#define FS_COMPRBLK_FL 0x00000200
#define FS_NOCOMP_FL 0x00000400
/* WARNING: DO NOT EDIT, AUTO-GENERATED CODE - SEE TOP FOR INSTRUCTIONS */
#define FS_ECOMPR_FL 0x00000800
#define FS_BTREE_FL 0x00001000
#define FS_INDEX_FL 0x00001000
#define FS_IMAGIC_FL 0x00002000
/* WARNING: DO NOT EDIT, AUTO-GENERATED CODE - SEE TOP FOR INSTRUCTIONS */
#define FS_JOURNAL_DATA_FL 0x00004000
#define FS_NOTAIL_FL 0x00008000
#define FS_DIRSYNC_FL 0x00010000
#define FS_TOPDIR_FL 0x00020000
/* WARNING: DO NOT EDIT, AUTO-GENERATED CODE - SEE TOP FOR INSTRUCTIONS */
#define FS_EXTENT_FL 0x00080000
#define FS_DIRECTIO_FL 0x00100000
#define FS_NOCOW_FL 0x00800000
#define FS_RESERVED_FL 0x80000000
/* WARNING: DO NOT EDIT, AUTO-GENERATED CODE - SEE TOP FOR INSTRUCTIONS */
#define FS_FL_USER_VISIBLE 0x0003DFFF
#define FS_FL_USER_MODIFIABLE 0x000380FF
#define SYNC_FILE_RANGE_WAIT_BEFORE 1
#define SYNC_FILE_RANGE_WRITE 2
/* WARNING: DO NOT EDIT, AUTO-GENERATED CODE - SEE TOP FOR INSTRUCTIONS */
#define SYNC_FILE_RANGE_WAIT_AFTER 4
#endif
