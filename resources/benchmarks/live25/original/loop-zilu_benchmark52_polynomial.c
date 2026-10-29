#include<limits.h>
/*@
assigns \nothing;
ensures INT_MIN <= \result < INT_MAX;
*/
int unknown();
#include <assert.h>
int main() {
  int i = unknown();
  if (!(i < 10 && i > -10)) return 0;
  while (i * i < 100) {
    i = i + 1;
  }
  //@ assert(i == 10);
  return 0;
}
