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
  if (!(i * i < j * j)) return 0;
  while (i < j) {
    j = j - i;
    if (j < i) {j = j + i;
    i = j - i;
    j = j - i;}
  }
  //@ assert(j == i);
  return 0;
}
