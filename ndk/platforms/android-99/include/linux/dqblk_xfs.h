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
#ifndef _LINUX_DQBLK_XFS_H
#define _LINUX_DQBLK_XFS_H
#include <linux/types.h>
#define XQM_CMD(x) (('X'<<8)+(x))
/* WARNING: DO NOT EDIT, AUTO-GENERATED CODE - SEE TOP FOR INSTRUCTIONS */
#define XQM_COMMAND(x) (((x) & (0xff<<8)) == ('X'<<8))
#define XQM_USRQUOTA 0
#define XQM_GRPQUOTA 1
#define XQM_PRJQUOTA 2
/* WARNING: DO NOT EDIT, AUTO-GENERATED CODE - SEE TOP FOR INSTRUCTIONS */
#define XQM_MAXQUOTAS 3
#define Q_XQUOTAON XQM_CMD(1)
#define Q_XQUOTAOFF XQM_CMD(2)
#define Q_XGETQUOTA XQM_CMD(3)
/* WARNING: DO NOT EDIT, AUTO-GENERATED CODE - SEE TOP FOR INSTRUCTIONS */
#define Q_XSETQLIM XQM_CMD(4)
#define Q_XGETQSTAT XQM_CMD(5)
#define Q_XQUOTARM XQM_CMD(6)
#define Q_XQUOTASYNC XQM_CMD(7)
/* WARNING: DO NOT EDIT, AUTO-GENERATED CODE - SEE TOP FOR INSTRUCTIONS */
#define FS_DQUOT_VERSION 1
typedef struct fs_disk_quota {
 __s8 d_version;
 __s8 d_flags;
/* WARNING: DO NOT EDIT, AUTO-GENERATED CODE - SEE TOP FOR INSTRUCTIONS */
 __u16 d_fieldmask;
 __u32 d_id;
 __u64 d_blk_hardlimit;
 __u64 d_blk_softlimit;
/* WARNING: DO NOT EDIT, AUTO-GENERATED CODE - SEE TOP FOR INSTRUCTIONS */
 __u64 d_ino_hardlimit;
 __u64 d_ino_softlimit;
 __u64 d_bcount;
 __u64 d_icount;
/* WARNING: DO NOT EDIT, AUTO-GENERATED CODE - SEE TOP FOR INSTRUCTIONS */
 __s32 d_itimer;
 __s32 d_btimer;
 __u16 d_iwarns;
 __u16 d_bwarns;
/* WARNING: DO NOT EDIT, AUTO-GENERATED CODE - SEE TOP FOR INSTRUCTIONS */
 __s32 d_padding2;
 __u64 d_rtb_hardlimit;
 __u64 d_rtb_softlimit;
 __u64 d_rtbcount;
/* WARNING: DO NOT EDIT, AUTO-GENERATED CODE - SEE TOP FOR INSTRUCTIONS */
 __s32 d_rtbtimer;
 __u16 d_rtbwarns;
 __s16 d_padding3;
 char d_padding4[8];
/* WARNING: DO NOT EDIT, AUTO-GENERATED CODE - SEE TOP FOR INSTRUCTIONS */
} fs_disk_quota_t;
#define FS_DQ_ISOFT (1<<0)
#define FS_DQ_IHARD (1<<1)
#define FS_DQ_BSOFT (1<<2)
/* WARNING: DO NOT EDIT, AUTO-GENERATED CODE - SEE TOP FOR INSTRUCTIONS */
#define FS_DQ_BHARD (1<<3)
#define FS_DQ_RTBSOFT (1<<4)
#define FS_DQ_RTBHARD (1<<5)
#define FS_DQ_LIMIT_MASK (FS_DQ_ISOFT | FS_DQ_IHARD | FS_DQ_BSOFT |   FS_DQ_BHARD | FS_DQ_RTBSOFT | FS_DQ_RTBHARD)
/* WARNING: DO NOT EDIT, AUTO-GENERATED CODE - SEE TOP FOR INSTRUCTIONS */
#define FS_DQ_BTIMER (1<<6)
#define FS_DQ_ITIMER (1<<7)
#define FS_DQ_RTBTIMER (1<<8)
#define FS_DQ_TIMER_MASK (FS_DQ_BTIMER | FS_DQ_ITIMER | FS_DQ_RTBTIMER)
/* WARNING: DO NOT EDIT, AUTO-GENERATED CODE - SEE TOP FOR INSTRUCTIONS */
#define FS_DQ_BWARNS (1<<9)
#define FS_DQ_IWARNS (1<<10)
#define FS_DQ_RTBWARNS (1<<11)
#define FS_DQ_WARNS_MASK (FS_DQ_BWARNS | FS_DQ_IWARNS | FS_DQ_RTBWARNS)
/* WARNING: DO NOT EDIT, AUTO-GENERATED CODE - SEE TOP FOR INSTRUCTIONS */
#define FS_DQ_BCOUNT (1<<12)
#define FS_DQ_ICOUNT (1<<13)
#define FS_DQ_RTBCOUNT (1<<14)
#define FS_DQ_ACCT_MASK (FS_DQ_BCOUNT | FS_DQ_ICOUNT | FS_DQ_RTBCOUNT)
/* WARNING: DO NOT EDIT, AUTO-GENERATED CODE - SEE TOP FOR INSTRUCTIONS */
#define FS_QUOTA_UDQ_ACCT (1<<0)
#define FS_QUOTA_UDQ_ENFD (1<<1)
#define FS_QUOTA_GDQ_ACCT (1<<2)
#define FS_QUOTA_GDQ_ENFD (1<<3)
/* WARNING: DO NOT EDIT, AUTO-GENERATED CODE - SEE TOP FOR INSTRUCTIONS */
#define FS_QUOTA_PDQ_ACCT (1<<4)
#define FS_QUOTA_PDQ_ENFD (1<<5)
#define FS_USER_QUOTA (1<<0)
#define FS_PROJ_QUOTA (1<<1)
/* WARNING: DO NOT EDIT, AUTO-GENERATED CODE - SEE TOP FOR INSTRUCTIONS */
#define FS_GROUP_QUOTA (1<<2)
#define FS_QSTAT_VERSION 1
typedef struct fs_qfilestat {
 __u64 qfs_ino;
/* WARNING: DO NOT EDIT, AUTO-GENERATED CODE - SEE TOP FOR INSTRUCTIONS */
 __u64 qfs_nblks;
 __u32 qfs_nextents;
} fs_qfilestat_t;
typedef struct fs_quota_stat {
/* WARNING: DO NOT EDIT, AUTO-GENERATED CODE - SEE TOP FOR INSTRUCTIONS */
 __s8 qs_version;
 __u16 qs_flags;
 __s8 qs_pad;
 fs_qfilestat_t qs_uquota;
/* WARNING: DO NOT EDIT, AUTO-GENERATED CODE - SEE TOP FOR INSTRUCTIONS */
 fs_qfilestat_t qs_gquota;
 __u32 qs_incoredqs;
 __s32 qs_btimelimit;
 __s32 qs_itimelimit;
/* WARNING: DO NOT EDIT, AUTO-GENERATED CODE - SEE TOP FOR INSTRUCTIONS */
 __s32 qs_rtbtimelimit;
 __u16 qs_bwarnlimit;
 __u16 qs_iwarnlimit;
} fs_quota_stat_t;
/* WARNING: DO NOT EDIT, AUTO-GENERATED CODE - SEE TOP FOR INSTRUCTIONS */
#endif
