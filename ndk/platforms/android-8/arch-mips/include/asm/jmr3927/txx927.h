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
#ifndef __ASM_TXX927_H
#define __ASM_TXX927_H

struct txx927_sio_reg {
 volatile unsigned long lcr;
 volatile unsigned long dicr;
 volatile unsigned long disr;
 volatile unsigned long cisr;
 volatile unsigned long fcr;
 volatile unsigned long flcr;
 volatile unsigned long bgr;
 volatile unsigned long tfifo;
 volatile unsigned long rfifo;
};

struct txx927_pio_reg {
 volatile unsigned long dout;
 volatile unsigned long din;
 volatile unsigned long dir;
 volatile unsigned long od;
 volatile unsigned long flag[2];
 volatile unsigned long pol;
 volatile unsigned long intc;
 volatile unsigned long maskcpu;
 volatile unsigned long maskext;
};

#define TXx927_SILCR_SCS_MASK 0x00000060
#define TXx927_SILCR_SCS_IMCLK 0x00000000
#define TXx927_SILCR_SCS_IMCLK_BG 0x00000020
#define TXx927_SILCR_SCS_SCLK 0x00000040
#define TXx927_SILCR_SCS_SCLK_BG 0x00000060
#define TXx927_SILCR_UEPS 0x00000010
#define TXx927_SILCR_UPEN 0x00000008
#define TXx927_SILCR_USBL_MASK 0x00000004
#define TXx927_SILCR_USBL_1BIT 0x00000004
#define TXx927_SILCR_USBL_2BIT 0x00000000
#define TXx927_SILCR_UMODE_MASK 0x00000003
#define TXx927_SILCR_UMODE_8BIT 0x00000000
#define TXx927_SILCR_UMODE_7BIT 0x00000001

#define TXx927_SIDICR_TDE 0x00008000
#define TXx927_SIDICR_RDE 0x00004000
#define TXx927_SIDICR_TIE 0x00002000
#define TXx927_SIDICR_RIE 0x00001000
#define TXx927_SIDICR_SPIE 0x00000800
#define TXx927_SIDICR_CTSAC 0x00000600
#define TXx927_SIDICR_STIE_MASK 0x0000003f
#define TXx927_SIDICR_STIE_OERS 0x00000020
#define TXx927_SIDICR_STIE_CTSS 0x00000010
#define TXx927_SIDICR_STIE_RBRKD 0x00000008
#define TXx927_SIDICR_STIE_TRDY 0x00000004
#define TXx927_SIDICR_STIE_TXALS 0x00000002
#define TXx927_SIDICR_STIE_UBRKD 0x00000001

#define TXx927_SIDISR_UBRK 0x00008000
#define TXx927_SIDISR_UVALID 0x00004000
#define TXx927_SIDISR_UFER 0x00002000
#define TXx927_SIDISR_UPER 0x00001000
#define TXx927_SIDISR_UOER 0x00000800
#define TXx927_SIDISR_ERI 0x00000400
#define TXx927_SIDISR_TOUT 0x00000200
#define TXx927_SIDISR_TDIS 0x00000100
#define TXx927_SIDISR_RDIS 0x00000080
#define TXx927_SIDISR_STIS 0x00000040
#define TXx927_SIDISR_RFDN_MASK 0x0000001f

#define TXx927_SICISR_OERS 0x00000020
#define TXx927_SICISR_CTSS 0x00000010
#define TXx927_SICISR_RBRKD 0x00000008
#define TXx927_SICISR_TRDY 0x00000004
#define TXx927_SICISR_TXALS 0x00000002
#define TXx927_SICISR_UBRKD 0x00000001

#define TXx927_SIFCR_SWRST 0x00008000
#define TXx927_SIFCR_RDIL_MASK 0x00000180
#define TXx927_SIFCR_RDIL_1 0x00000000
#define TXx927_SIFCR_RDIL_4 0x00000080
#define TXx927_SIFCR_RDIL_8 0x00000100
#define TXx927_SIFCR_RDIL_12 0x00000180
#define TXx927_SIFCR_RDIL_MAX 0x00000180
#define TXx927_SIFCR_TDIL_MASK 0x00000018
#define TXx927_SIFCR_TDIL_MASK 0x00000018
#define TXx927_SIFCR_TDIL_1 0x00000000
#define TXx927_SIFCR_TDIL_4 0x00000001
#define TXx927_SIFCR_TDIL_8 0x00000010
#define TXx927_SIFCR_TDIL_MAX 0x00000010
#define TXx927_SIFCR_TFRST 0x00000004
#define TXx927_SIFCR_RFRST 0x00000002
#define TXx927_SIFCR_FRSTE 0x00000001
#define TXx927_SIO_TX_FIFO 8
#define TXx927_SIO_RX_FIFO 16

#define TXx927_SIFLCR_RCS 0x00001000
#define TXx927_SIFLCR_TES 0x00000800
#define TXx927_SIFLCR_RTSSC 0x00000200
#define TXx927_SIFLCR_RSDE 0x00000100
#define TXx927_SIFLCR_TSDE 0x00000080
#define TXx927_SIFLCR_RTSTL_MASK 0x0000001e
#define TXx927_SIFLCR_RTSTL_MAX 0x0000001e
#define TXx927_SIFLCR_TBRK 0x00000001

#define TXx927_SIBGR_BCLK_MASK 0x00000300
#define TXx927_SIBGR_BCLK_T0 0x00000000
#define TXx927_SIBGR_BCLK_T2 0x00000100
#define TXx927_SIBGR_BCLK_T4 0x00000200
#define TXx927_SIBGR_BCLK_T6 0x00000300
#define TXx927_SIBGR_BRD_MASK 0x000000ff

#endif
