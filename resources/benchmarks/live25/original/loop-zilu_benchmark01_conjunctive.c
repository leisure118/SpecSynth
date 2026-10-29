#include<limits.h>
/*@
assigns \nothing;
ensures INT_MIN <= \result < INT_MAX;
*/
int unknown();
#include <assert.h>
int main() {
  int x = unknown();
  int y = unknown();
  if (!(x==1 && y==1)) return 0;
  while (unknown()) {
    x=x+y;
    y=x;
  }
  //@ assert(y>=1);
  return 0;
}
