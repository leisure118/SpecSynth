#include "x509_utils.h"

/*@
  requires len > 0;
  requires \valid_read(buf + (0 .. len - 1));
  assigns \nothing;
  ensures \result == 0 ==> \forall integer i; 0 <= i < len ==> buf[i] <= 0x7f;
  ensures \result == -X509_FILE_LINE_NUM_ERR ==> \exists integer i; 0 <= i < len && buf[i] > 0x7f;
*/
int check_ia5_string(const u8 *buf, u32 len)
{
    int ret = 0;
    u32 i;
    if ((buf == NULL) || (len == 0)) {
        return -X509_FILE_LINE_NUM_ERR;
    }

    /*@
      loop invariant 0 <= i <= len;
      loop invariant ret == 0 ==> \forall integer k; 0 <= k < i ==> buf[k] <= 0x7f;
      loop assigns i, ret;
      loop variant len - i;
    */
    for (i = 0; i < len; i++) {
        if (buf[i] > 0x7f) {
            ret = -X509_FILE_LINE_NUM_ERR;
            break;
        }
    }

    return ret;
}

int main(void) {
    u8 buf[5] = {0x41, 0x42, 0x43, 0x44, 0x45};
    u32 len = 5;
    int ret = check_ia5_string(buf, len);

    //@ assert ret == 0;
    return ret;
}
