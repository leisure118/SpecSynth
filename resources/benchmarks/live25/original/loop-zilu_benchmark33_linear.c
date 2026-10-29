#include<limits.h>
/*@
assigns \nothing;
ensures INT_MIN <= \result < INT_MAX;
*/
int unknown();
#include <assert.h>
int main() {
  int x = unknown();
  if (!(x>=0)) return 0;
  while (x<100 && x>=0) {
    x++;
  }
  //@ assert(x>=100);
  return 0;
}
