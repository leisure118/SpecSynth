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
  int r = unknown();
  if (!(r > i + j)) return 0;
  while (i > 0) {
    i = i - 1;
    j = j + 1;
  }
  //@ assert(r > i + j);
  return 0;
}
