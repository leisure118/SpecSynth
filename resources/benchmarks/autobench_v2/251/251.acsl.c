#include <limits.h>
/*@
ensures INT_MIN <= \result <= INT_MAX;
*/
int unknown_int();

int main() {
  int n;
  int i = 0;
  int k = 0;
  n = unknown_int();
  /*@
    loop invariant 0 <= i;
    loop invariant i == k;
    loop invariant n > 0 ==> i <= n;
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
    loop invariant k + j >= n;
    loop assigns j, k;
    loop variant n - j;
  */
  while( j < n ) {
    //@ assert (k > 0);
    j++;
    k--;
  }
}