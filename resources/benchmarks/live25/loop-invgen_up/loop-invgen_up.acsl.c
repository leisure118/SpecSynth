#include<limits.h>
/*@
assigns \nothing;
ensures INT_MIN <= \result < INT_MAX;
*/
int unknown();
#include "assert.h"
int main() {
  int n;
  int i = 0;
  int k = 0;
  n = unknown();
  /*@
    loop invariant 0 <= i;
    loop invariant k == i;
    loop assigns i, k;
    loop variant n - i;
  */
  while( i < n ) {
	i++;
	k++;
  }
  int j = 0;
  /*@
    loop invariant 0 <= j;
    loop invariant k >= n - j;
    loop assigns j, k;
    loop variant n - j;
  */
  while( j < n ) {
    //@ assert(k > 0);
    j++;
    k--;
  }
}
