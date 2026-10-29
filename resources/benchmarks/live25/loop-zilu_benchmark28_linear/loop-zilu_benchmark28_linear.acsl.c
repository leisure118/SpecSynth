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
  //@ admit i > 0 && j > 0;
  if (!(i * i < j * j)) return 0;
  /*@
    loop invariant i <= j;
    loop invariant 0 < i;
    loop assigns i, j;
    loop variant j;
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
