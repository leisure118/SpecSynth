/* === main.c === */

#include "x509_utils.h"

int main(void) {
    u8 buf[5];
    u32 len = 5;

    int ret = check_ia5_string(buf, len);

    //@ assert ret == 0 ==> \forall integer i; 0 <= i < len ==> (buf[i] <= 0x7f); 
    //@ assert ret == -X509_FILE_LINE_NUM_ERR ==> \exists integer i; 0 <= i < len && buf[i] > 0x7f;

    return ret;
}


/* === x509_utils.c === */

#include "x509_utils.h"

static int validate_ia5_char(u8 c)
{
    if (c > 0x7f) {
        return 0; // Invalid
    }
    return 1; // Valid
}

int check_ia5_string(const u8 *buf, u32 len)
{
    int ret = 0;
    u32 i;
    if ((buf == NULL) || (len == 0)) {
        ret = -X509_FILE_LINE_NUM_ERR;
        goto out;
    }
    for (i = 0; i < len; i++) {
        if (validate_ia5_char(buf[i]) == 0) {
            ret = -X509_FILE_LINE_NUM_ERR;
            goto out;
        }
    }
    ret = 0;
out:
    return ret;
}

/* === x509_utils.h === */

#ifndef X509_COMMON_H
#define X509_COMMON_H

#include <stdint.h>
#include <stddef.h> // for NULL

typedef uint8_t  u8;
typedef uint32_t u32;

#define X509_FILE_NUM 1
#define X509_FILE_LINE_NUM_ERR ((X509_FILE_NUM * 100000))


int check_ia5_string(const u8 *buf, u32 len);

#endif
