/* Auto-generated minimal verifiable slice */
/* Target function: bufs_differ */
/* Mode: stub */

#include <stdint.h>
#include <unistd.h>
#include <string.h>

typedef uint8_t  u8;
typedef uint16_t u16;
typedef uint32_t u32;
typedef uint64_t u64;

/*@
  predicate bmatch(u8 *a, u8 *b, integer k) =
    \forall integer j; 0 <= j < k ==> a[j] == b[j];
*/

int bufs_differ(const u8 *b1, const u8 *b2, u32 n);

/* === Target: bufs_differ === */
/*@
  requires \valid_read(b1 + (0..n-1));
  requires \valid_read(b2 + (0..n-1));
  assigns \nothing;
  ensures \result == 0 <==> bmatch(b1, b2, n);
  ensures \result == 1 <==> !bmatch(b1, b2, n);
*/
int bufs_differ(const u8 *b1, const u8 *b2, u32 n)
{
	int ret = 0;
	u32 i = 0;
	/*@
	  loop invariant 0 <= i <= n;
	  loop invariant bmatch(b1, b2, i);
	  loop assigns i, ret;
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
