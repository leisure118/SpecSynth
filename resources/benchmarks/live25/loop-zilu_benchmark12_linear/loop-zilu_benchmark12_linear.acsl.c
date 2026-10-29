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
  int t = unknown();
  if (!(x!=y && y==t)) return 0;
  /*@
    loop invariant y >= t;
    loop assigns y;
  */
  while (unknown()) {
    if(x>0) y=y+x;
  }
  //@ assert(y>=t);
  return 0;
}
