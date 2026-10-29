#include<limits.h>
/*@
assigns \nothing;
ensures INT_MIN <= \result < INT_MAX;
*/
int unknown();
#include <assert.h>
int main() {
  int j = unknown();
  int k = unknown();
  int n = unknown();
  if (!((j==n) && (k==n) && (n>0))) return 0;
  /*@
    loop invariant j >= 0;
    loop invariant j == k;
    loop invariant n > 0;
    loop assigns j, k;
    loop variant j;
  */
  while (j>0 && n>0) {
    j--;k--;
  }
  //@ assert((k == 0));
  return 0;
}
