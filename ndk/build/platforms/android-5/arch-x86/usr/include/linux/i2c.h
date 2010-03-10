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
#ifndef _LINUX_I2C_H
#define _LINUX_I2C_H

#include <linux/types.h>

struct i2c_msg {
 __u16 addr;
 __u16 flags;
#define I2C_M_TEN 0x10  
#define I2C_M_RD 0x01
#define I2C_M_NOSTART 0x4000
#define I2C_M_REV_DIR_ADDR 0x2000
#define I2C_M_IGNORE_NAK 0x1000
#define I2C_M_NO_RD_ACK 0x0800
 __u16 len;
 __u8 *buf;
};

#define I2C_FUNC_I2C 0x00000001
#define I2C_FUNC_10BIT_ADDR 0x00000002
#define I2C_FUNC_PROTOCOL_MANGLING 0x00000004  
#define I2C_FUNC_SMBUS_HWPEC_CALC 0x00000008  
#define I2C_FUNC_SMBUS_BLOCK_PROC_CALL 0x00008000  
#define I2C_FUNC_SMBUS_QUICK 0x00010000 
#define I2C_FUNC_SMBUS_READ_BYTE 0x00020000 
#define I2C_FUNC_SMBUS_WRITE_BYTE 0x00040000 
#define I2C_FUNC_SMBUS_READ_BYTE_DATA 0x00080000 
#define I2C_FUNC_SMBUS_WRITE_BYTE_DATA 0x00100000 
#define I2C_FUNC_SMBUS_READ_WORD_DATA 0x00200000 
#define I2C_FUNC_SMBUS_WRITE_WORD_DATA 0x00400000 
#define I2C_FUNC_SMBUS_PROC_CALL 0x00800000 
#define I2C_FUNC_SMBUS_READ_BLOCK_DATA 0x01000000 
#define I2C_FUNC_SMBUS_WRITE_BLOCK_DATA 0x02000000 
#define I2C_FUNC_SMBUS_READ_I2C_BLOCK 0x04000000  
#define I2C_FUNC_SMBUS_WRITE_I2C_BLOCK 0x08000000  
#define I2C_FUNC_SMBUS_READ_I2C_BLOCK_2 0x10000000  
#define I2C_FUNC_SMBUS_WRITE_I2C_BLOCK_2 0x20000000  

#define I2C_FUNC_SMBUS_BYTE (I2C_FUNC_SMBUS_READ_BYTE |   I2C_FUNC_SMBUS_WRITE_BYTE)
#define I2C_FUNC_SMBUS_BYTE_DATA (I2C_FUNC_SMBUS_READ_BYTE_DATA |   I2C_FUNC_SMBUS_WRITE_BYTE_DATA)
#define I2C_FUNC_SMBUS_WORD_DATA (I2C_FUNC_SMBUS_READ_WORD_DATA |   I2C_FUNC_SMBUS_WRITE_WORD_DATA)
#define I2C_FUNC_SMBUS_BLOCK_DATA (I2C_FUNC_SMBUS_READ_BLOCK_DATA |   I2C_FUNC_SMBUS_WRITE_BLOCK_DATA)
#define I2C_FUNC_SMBUS_I2C_BLOCK (I2C_FUNC_SMBUS_READ_I2C_BLOCK |   I2C_FUNC_SMBUS_WRITE_I2C_BLOCK)
#define I2C_FUNC_SMBUS_I2C_BLOCK_2 (I2C_FUNC_SMBUS_READ_I2C_BLOCK_2 |   I2C_FUNC_SMBUS_WRITE_I2C_BLOCK_2)

#define I2C_FUNC_SMBUS_EMUL (I2C_FUNC_SMBUS_QUICK |   I2C_FUNC_SMBUS_BYTE |   I2C_FUNC_SMBUS_BYTE_DATA |   I2C_FUNC_SMBUS_WORD_DATA |   I2C_FUNC_SMBUS_PROC_CALL |   I2C_FUNC_SMBUS_WRITE_BLOCK_DATA |   I2C_FUNC_SMBUS_I2C_BLOCK)

#define I2C_SMBUS_BLOCK_MAX 32   
union i2c_smbus_data {
 __u8 byte;
 __u16 word;
 __u8 block[I2C_SMBUS_BLOCK_MAX + 2];

};

#define I2C_SMBUS_READ 1
#define I2C_SMBUS_WRITE 0

#define I2C_SMBUS_QUICK 0
#define I2C_SMBUS_BYTE 1
#define I2C_SMBUS_BYTE_DATA 2 
#define I2C_SMBUS_WORD_DATA 3
#define I2C_SMBUS_PROC_CALL 4
#define I2C_SMBUS_BLOCK_DATA 5
#define I2C_SMBUS_I2C_BLOCK_DATA 6
#define I2C_SMBUS_BLOCK_PROC_CALL 7  

#define I2C_RETRIES 0x0701  

#define I2C_TIMEOUT 0x0702  

#define I2C_SLAVE 0x0703  

#define I2C_SLAVE_FORCE 0x0706  

#define I2C_TENBIT 0x0704  

#define I2C_FUNCS 0x0705  
#define I2C_RDWR 0x0707  
#define I2C_PEC 0x0708  

#define I2C_SMBUS 0x0720  

#endif
