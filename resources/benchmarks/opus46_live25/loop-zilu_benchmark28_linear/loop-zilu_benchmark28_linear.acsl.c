#include<limits.h>
/*@
assigns \nothing;
ensures 1 <= \result <= 46340;
*/
int unknown();
#include <assert.h>
int main() {
  int i = unknown();
  int j = unknown();
  if (!(i * i < j * j)) return 0;
  /*@
    loop invariant 1 <= i;
    loop invariant i <= j;
    loop assigns i, j;
    loop variant i + j;
  */
  while (i < j) {
    j = j - i;
    if (j < i) {j = j + i;
    i = j - i;
    j = j - i;}
  }
  //@ assert(j == i);
  return 0;
}
