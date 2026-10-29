#include<limits.h>
/*@
assigns \nothing;
ensures INT_MIN <= \result < INT_MAX;
*/
int unknown();
#include "assert.h"
int main(int argc, char* argv[]) {
  int c1 = 4000;
  int c2 = 2000;
  int c3 = 10000;
  int n, v;
  int i, k, j;
  n = unknown();
  if (!(0 <= n && n < 10)) return 0;
  k = 0;
  i = 0;
  /*@
    loop invariant 0 <= i <= n;
    loop invariant k >= 2000 * i;
    loop assigns i, k, v;
    loop variant n - i;
  */
  while( i < n ) {
    i++;
    v = unknown();
    if (!(0 <= v && n < 2)) return 0;
    if( v == 0 )
      k += c1;
    else if( v == 1 )
      k += c2;
    else
      k += c3;
  }
  j = 0;
  /*@
    loop invariant 0 <= j <= n;
    loop invariant k >= n - j;
    loop assigns j, k;
    loop variant n - j;
  */
  while( j < n ) {
    //@ assert(k > 0);
    j++;
    k--;
  }
  return 0;
}
