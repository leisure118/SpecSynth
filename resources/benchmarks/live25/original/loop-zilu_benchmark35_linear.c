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
  while ((x>=0) && (x<10)) {
    x=x+1;
  }
  //@ assert(x>=10);
  return 0;
}
