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
  if (!(i==0 && j==0)) return 0;
  /*@
    loop invariant 0 <= i <= 100;
    loop invariant j == 2*i;
    loop assigns i, j;
    loop variant 100 - i;
  */
  while (i<100) {
    j+=2;
    i++;
  }
  //@ assert(j==200);
  return 0;
}
