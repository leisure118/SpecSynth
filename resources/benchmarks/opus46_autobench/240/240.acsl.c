#include <limits.h>
/*@
    assigns \nothing;
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
    loop invariant 2*k + i == 2*n;
    loop invariant n > 0 ==> i <= n + 1;
    loop assigns i, k;
    loop variant n - i;
  */
  while( i < n ) {
    k--;
    i = i + 2;
  }

  int j = 0;
 
  /*@
    loop invariant 0 <= j;
    loop invariant 2*k + 2*j + i == 2*n;
    loop invariant i >= n;
    loop invariant n > 0 ==> i <= n + 1;
    loop invariant i % 2 == 0;
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