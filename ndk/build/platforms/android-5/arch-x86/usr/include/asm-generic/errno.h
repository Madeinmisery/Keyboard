/****************************************************************************
 ****************************************************************************
 ***
 ***   This header was automatically generated from a Linux kernel header
 ***   of the same name, to make information necessary for userspace to
 ***   call into the kernel available to libc.  It contains only constants,
 ***   structures, and macros generated from the original header, and thus,
 ***   contains no copyrightable information.
 ***
 ****************************************************************************
 ****************************************************************************/
#ifndef _ASM_GENERIC_ERRNO_H
#define _ASM_GENERIC_ERRNO_H

#include <asm-generic/errno-base.h>

#define EDEADLK 35  
#define ENAMETOOLONG 36  
#define ENOLCK 37  
#define ENOSYS 38  
#define ENOTEMPTY 39  
#define ELOOP 40  
#define EWOULDBLOCK EAGAIN  
#define ENOMSG 42  
#define EIDRM 43  
#define ECHRNG 44  
#define EL2NSYNC 45  
#define EL3HLT 46  
#define EL3RST 47  
#define ELNRNG 48  
#define EUNATCH 49  
#define ENOCSI 50  
#define EL2HLT 51  
#define EBADE 52  
#define EBADR 53  
#define EXFULL 54  
#define ENOANO 55  
#define EBADRQC 56  
#define EBADSLT 57  

#define EDEADLOCK EDEADLK

#define EBFONT 59  
#define ENOSTR 60  
#define ENODATA 61  
#define ETIME 62  
#define ENOSR 63  
#define ENONET 64  
#define ENOPKG 65  
#define EREMOTE 66  
#define ENOLINK 67  
#define EADV 68  
#define ESRMNT 69  
#define ECOMM 70  
#define EPROTO 71  
#define EMULTIHOP 72  
#define EDOTDOT 73  
#define EBADMSG 74  
#define EOVERFLOW 75  
#define ENOTUNIQ 76  
#define EBADFD 77  
#define EREMCHG 78  
#define ELIBACC 79  
#define ELIBBAD 80  
#define ELIBSCN 81  
#define ELIBMAX 82  
#define ELIBEXEC 83  
#define EILSEQ 84  
#define ERESTART 85  
#define ESTRPIPE 86  
#define EUSERS 87  
#define ENOTSOCK 88  
#define EDESTADDRREQ 89  
#define EMSGSIZE 90  
#define EPROTOTYPE 91  
#define ENOPROTOOPT 92  
#define EPROTONOSUPPORT 93  
#define ESOCKTNOSUPPORT 94  
#define EOPNOTSUPP 95  
#define EPFNOSUPPORT 96  
#define EAFNOSUPPORT 97  
#define EADDRINUSE 98  
#define EADDRNOTAVAIL 99  
#define ENETDOWN 100  
#define ENETUNREACH 101  
#define ENETRESET 102  
#define ECONNABORTED 103  
#define ECONNRESET 104  
#define ENOBUFS 105  
#define EISCONN 106  
#define ENOTCONN 107  
#define ESHUTDOWN 108  
#define ETOOMANYREFS 109  
#define ETIMEDOUT 110  
#define ECONNREFUSED 111  
#define EHOSTDOWN 112  
#define EHOSTUNREACH 113  
#define EALREADY 114  
#define EINPROGRESS 115  
#define ESTALE 116  
#define EUCLEAN 117  
#define ENOTNAM 118  
#define ENAVAIL 119  
#define EISNAM 120  
#define EREMOTEIO 121  
#define EDQUOT 122  

#define ENOMEDIUM 123  
#define EMEDIUMTYPE 124  
#define ECANCELED 125  
#define ENOKEY 126  
#define EKEYEXPIRED 127  
#define EKEYREVOKED 128  
#define EKEYREJECTED 129  

#define EOWNERDEAD 130  
#define ENOTRECOVERABLE 131  

#endif
