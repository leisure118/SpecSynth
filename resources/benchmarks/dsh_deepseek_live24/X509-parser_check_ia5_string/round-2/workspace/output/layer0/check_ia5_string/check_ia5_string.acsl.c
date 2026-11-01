/* Auto-generated minimal verifiable slice */
/* Target function: check_ia5_string */
/* Mode: stub */

#include <stdint.h>
#include <unistd.h>
#include <string.h>

typedef uint8_t  u8;
typedef uint16_t u16;
typedef uint32_t u32;
typedef uint64_t u64;

#define X509_FILE_NUM 0
#define X509_FILE_LINE_NUM_ERR ((X509_FILE_NUM * 100000))

static int check_ia5_string(const u8 *buf, u32 len);

/* === Target: check_ia5_string === */
static int check_ia5_string(const u8 *buf, u32 len)
	/*@ requires len == 0 || \valid_read(buf + (0 .. len-1));
	    assigns \nothing;
	    ensures (buf == \null || len == 0) ==> \result == -X509_FILE_LINE_NUM_ERR;
	    ensures (buf != \null && len > 0 && \result == -X509_FILE_LINE_NUM_ERR) ==>
	              \exists integer i; 0 <= i < len && buf[i] > 0x7f;
	    ensures \result == 0 ==>
	              \forall integer i; 0 <= i < len ==> buf[i] <= 0x7f;
	*/
{
	int ret;
	u32 i;
	if ((buf == NULL) || (len == 0)) {
		ret = -X509_FILE_LINE_NUM_ERR;
		goto out;
	}
	/*@ loop invariant 0 <= i <= len;
	    loop invariant \forall integer j; 0 <= j < i ==> buf[j] <= 0x7f;
	    loop assigns i, ret;
	    loop variant len - i;
	*/
	for (i = 0; i < len; i++) {
		if (buf[i] > 0x7f) {
			ret = -X509_FILE_LINE_NUM_ERR;
			goto out;
		}
	}
	ret = 0;
out:
	return ret;
}
