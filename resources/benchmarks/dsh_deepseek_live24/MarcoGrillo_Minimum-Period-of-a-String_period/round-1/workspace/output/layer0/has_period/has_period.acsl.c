/* Auto-generated minimal verifiable slice */
/* Target function: has_period */
/* Mode: stub */

#include <stdint.h>
#include <unistd.h>
#include <string.h>

typedef uint8_t  u8;
typedef uint16_t u16;
typedef uint32_t u32;
typedef uint64_t u64;


unsigned has_period(const char x[], unsigned int p, unsigned l);

/*@
  predicate is_periodic{L}(char *x, unsigned int p, unsigned int l) =
    (l % p == 0) && (\forall integer j; 0 <= j < l-p-1 ==> x[j] == x[j+p]);
*/

/* === Target: has_period === */
/*@
  requires \valid(x + (0..l-1));
  requires l > 0;
  requires p > 0;
  assigns \nothing;
  ensures is_periodic(x,p,l) ==> \result == 1;
  ensures !is_periodic(x,p,l) ==> \result == 0;
*/
unsigned has_period(const char x[], unsigned int p, unsigned l) {
    if (p == l) return 1;
    if ((l % p) != 0) return 0;
        /*@
            loop assigns i;
            loop invariant 0 <= i;
            loop invariant i + p < l;
            loop invariant \forall unsigned int j; 0 <= j < i ==> (x[j] == x[j+p]);
            loop invariant i <= l-p-1;
            loop variant l - p - 1 - i;
        */
        for (unsigned i = 0 ; i < l-p-1 ; ++i) {
            if (x[i] != x[i + p])
                return 0;
        }     
    return 1; 
}
