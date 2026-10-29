#include<limits.h>
/*@
assigns \nothing;
ensures INT_MIN <= \result < INT_MAX;
*/
int unknown();
#include <assert.h>
int main() {
  int i = unknown();
  int j = unknown();
  int k = unknown();
  if (!(i==0 && j==0)) return 0;
  /*@
    loop invariant 0 <= i;
    loop invariant j == i;
    loop assigns i, j;
    loop variant k - i;
  */
  while (i <= k) {
    i++;
    j=j+1;
  }
  //@ assert(j==i);
  return 0;
}
