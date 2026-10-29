#include<limits.h>
/*@
assigns \nothing;
ensures INT_MIN <= \result < INT_MAX;
*/
int unknown();
#include "assert.h"
int main() {
  int n;
  int k = 0;
  int i = 0;
  n = unknown();
  /*@
    admit n >= 0;
  */
  /*@
    loop invariant 0 <= i <= n;
    loop invariant k == i;
    loop assigns i, k;
    loop variant n - i;
  */
  while( i < n ) {
      i++;
      k++;
  }
  int j = n;
  /*@
    loop invariant 0 <= j <= n;
    loop invariant k == j;
    loop assigns j, k;
    loop variant j;
  */
  while( j > 0 ) {
      //@ assert(k > 0);
      j--;
      k--;
  }
  return 0;
}
