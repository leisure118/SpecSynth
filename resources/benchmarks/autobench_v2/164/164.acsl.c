#include <assert.h>
int unknown1();

/*
 * "nest-if8" from InvGen benchmark suite
 */

void main() {
  int i, j, k, n, m;
  if (m + 1 < n);
  else return;
  /*@
    loop invariant 0 <= i;
    loop invariant i % 4 == 0;
    loop assigns i, j, k;
    loop variant n - i;
  */
  for (i = 0; i < n; i += 4) {
    /*@
      loop invariant i <= j;
      loop invariant j >= 0;
      loop invariant i < n;
      loop assigns j, k;
      loop variant m - j;
    */
    for (j = i; j < m;) {
      if (unknown1()) {
        //@ assert(j >= 0);
        j++;
        k = 0;
        /*@
          loop invariant 0 <= k <= j;
          loop assigns k;
          loop variant j - k;
        */
        while (k < j) {
          k++;
        }
      } else {
        //@ assert(n + j + 5 > i);
        j += 2;
      }
    }
  }
}