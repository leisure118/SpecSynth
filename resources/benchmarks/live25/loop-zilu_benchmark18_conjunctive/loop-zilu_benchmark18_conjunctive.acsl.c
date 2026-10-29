#include<limits.h>
/*@
assigns \nothing;
ensures INT_MIN <= \result < INT_MAX;
*/
int unknown();
#include <assert.h>
int main() {
  int i = unknown();
  int k = unknown();
  int n = unknown();
  if (!((i==0) && (k==0) && (n>0))) return 0;
  /*@
    loop invariant 0 <= i <= n;
    loop invariant i == k;
    loop assigns i, k;
    loop variant n - i;
  */
  while (i < n) {
    i++;k++;
  }
  //@ assert((i == k) && (k == n));
  return 0;
}
