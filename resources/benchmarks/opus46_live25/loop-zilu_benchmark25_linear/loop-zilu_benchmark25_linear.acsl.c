#include<limits.h>
/*@
assigns \nothing;
ensures INT_MIN <= \result < INT_MAX;
*/
int unknown();
#include <assert.h>
int main() {
  int x = unknown();
  if (!(x<0)) return 0;
  /*@
    loop invariant x <= 10;
    loop assigns x;
    loop variant 10 - x;
  */
  while (x<10) {
    x=x+1;
  }
  //@ assert(x==10);
  return 0;
}
