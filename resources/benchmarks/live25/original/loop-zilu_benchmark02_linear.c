#include<limits.h>
/*@
assigns \nothing;
ensures INT_MIN <= \result < INT_MAX;
*/
int unknown();
#include <assert.h>
int main() {
  int n = unknown();
  int i = unknown();
  int l = unknown();
  i = l;
  if (!(l>0)) return 0;
  while (i < n) {
    i++;
  }
  //@ assert(l>=1);
  return 0;
}
