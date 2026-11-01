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
{
	int ret;
	u32 i;
	if ((buf == NULL) || (len == 0)) {
		ret = -X509_FILE_LINE_NUM_ERR;
		goto out;
	}
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
