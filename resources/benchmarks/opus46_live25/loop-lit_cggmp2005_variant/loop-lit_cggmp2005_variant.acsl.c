#include<limits.h>
/*@
assigns \nothing;
ensures INT_MIN <= \result < INT_MAX;
*/
int unknown();
#include "assert.h"
int main() {
    int lo, mid, hi;
    lo = 0;
    mid = unknown();
    if (!(mid > 0 && mid < INT_MAX)) return 0;
    hi = 2*mid;
    /*@
      loop invariant mid >= 0;
      loop invariant lo >= 0;
      loop invariant hi == 2*mid + lo;
      loop assigns lo, mid, hi;
      loop variant mid;
    */
    while (mid > 0) {
        lo = lo + 1;
        hi = hi - 1;
        mid = mid - 1;
    }
    //@ assert(lo == hi);
    return 0;
}
