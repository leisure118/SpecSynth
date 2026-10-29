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
  if (!(0 <= k && k <= 1 && i == 1)) return 0;
  while (unknown()) {
    i = i + 1;
    k = k - 1;
  }
  //@ assert(1 <= i + k && i + k <= 2 && i >= 1);
  return 0;
}
