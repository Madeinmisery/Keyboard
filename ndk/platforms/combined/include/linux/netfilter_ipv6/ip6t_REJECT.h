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
#ifndef _IP6T_REJECT_H
#define _IP6T_REJECT_H

enum ip6t_reject_with {
 IP6T_ICMP6_NO_ROUTE,
 IP6T_ICMP6_ADM_PROHIBITED,
 IP6T_ICMP6_NOT_NEIGHBOUR,
 IP6T_ICMP6_ADDR_UNREACH,
 IP6T_ICMP6_PORT_UNREACH,
 IP6T_ICMP6_ECHOREPLY,
 IP6T_TCP_RESET
};

struct ip6t_reject_info {
 u_int32_t with;
};

#endif
