#include <stdint.h>
#include <unistd.h>
#include <string.h>
typedef uint8_t	  u8;
typedef uint16_t u16;
typedef uint32_t u32;
typedef uint64_t u64;
#define X509_FILE_NUM 0 
#define X509_FILE_LINE_NUM_ERR ((X509_FILE_NUM * 100000) + __LINE__)
/*@
  predicate bmatch(u8 *b1, u8 *b2, u32 n) =
    \forall integer i; 0 <= i < n ==> b1[i] == b2[i];
  
  predicate bdiffer(u8 *b1, u8 *b2, u32 n) =
    ! bmatch(b1, b2, n);
*/
/*@
  requires \valid_read(b1 + (0 .. n-1));
  requires \valid_read(b2 + (0 .. n-1));
  requires n >= 0;
  ensures \result == 0 <==> bmatch(b1, b2, n);
  ensures \result == 1 <==> bdiffer(b1, b2, n);
  assigns \nothing;
*/
int bufs_differ(const u8 *b1, const u8 *b2, u32 n)
{
	int ret = 0;
	u32 i = 0;
	/*@
	  loop invariant 0 <= i <= n;
	  loop invariant bmatch(b1, b2, i);
	  loop assigns i;
	  loop variant n - i;
	*/
	for (i = 0; i < n; i++) {
		if(b1[i] != b2[i]) {
			ret = 1;
			break;
		}
	}
	return ret;
}
static const u8 null_encoded_val[] = { 0x05, 0x00 };
int parse_null(const u8 *buf, u32 len, u32 *parsed)
{
	int ret;
	if ((len == 0) || (buf == NULL) || (parsed == NULL)) {
		ret = -X509_FILE_LINE_NUM_ERR;
		goto out;
	}
	if (len != sizeof(null_encoded_val)) {
		ret = -X509_FILE_LINE_NUM_ERR;
		goto out;
	}
	ret = bufs_differ(buf, null_encoded_val, sizeof(null_encoded_val));
	if (ret) {
		ret = -X509_FILE_LINE_NUM_ERR;
		goto out;
	}
	ret = 0;
	*parsed = sizeof(null_encoded_val);
out:
	return ret;
}
int main() {
  const u8 b[] = { 0x05, 0x00 };
  u32 parsed;
  int ret = parse_null(b, sizeof(null_encoded_val), &parsed);
  //@ assert parsed == sizeof(null_encoded_val);
  //@ assert ret == 0;
  return 0;
}