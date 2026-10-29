#include <limits.h>
/*@
    ensures \result >= INT_MIN && \result <= INT_MAX;
*/
int unknown_int();

int main() {
  int n,i,k;
  n = unknown_int();
  k = n;
  i = 0;

  /*@
    loop invariant 0 <= i;
    loop invariant i % 2 == 0;
    loop invariant k + i/2 == n;
    loop invariant i <= n + 1 || n < i;
    loop assigns i, k;
    loop variant i >= n ? 0 : n - i;
  */
  while( i < n ) {
    k--;
    i = i + 2;
  }

  int j = 0;
  //@ admit k == n/2;

  /*@
    loop invariant 0 <= j;
    loop invariant k == n/2 - j;
    loop assigns j, k;
    loop variant n/2 - j;
  */
  while( j < n/2 ) {
    //@ assert(k > 0);
    k--;
    j++;
  }
  return 0;
}