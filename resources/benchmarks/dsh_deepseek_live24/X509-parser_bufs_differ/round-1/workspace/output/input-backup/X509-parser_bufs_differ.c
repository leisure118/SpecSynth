#include <stdint.h>
#include <unistd.h>
#include <string.h>
typedef uint8_t	  u8;
typedef uint16_t u16;
typedef uint32_t u32;
typedef uint64_t u64;
#define X509_FILE_NUM 0
/*@
  predicate bmatch(u8 *b1, u8 *b2, u32 n) =
    \forall integer i; 0 <= i < n ==> b1[i] == b2[i];
  predicate bdiffer(u8 *b1, u8 *b2, u32 n) =
    ! bmatch(b1, b2, n);
*/
int bufs_differ(const u8 *b1, const u8 *b2, u32 n)
{
	int ret = 0;
	u32 i = 0;
	for (i = 0; i < n; i++) {
		if(b1[i] != b2[i]) {
			ret = 1;
			break;
		}
	}
	return ret;
}
int main() {
  u8 b1[10] = {1,2,3,4,5,6,7,8,9,10};
  u8 b2[10] = {10,9,8,7,6,5,4,3,2,1};
  u8 b3[10] = {1,2,3,4,5,6,7,8,9,10};
  u32 n = 10;
  int ret1 = bufs_differ(b1, b3, n);
  //@ assert ret1 == 0;
  int ret2 = bufs_differ(b1, b2, n);
  //@ assert ret2 == 1;
  return 0;
}