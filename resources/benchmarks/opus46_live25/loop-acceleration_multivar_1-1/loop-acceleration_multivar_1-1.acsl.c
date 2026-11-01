#include<limits.h>
/*@
assigns \nothing;
ensures INT_MIN <= \result < INT_MAX;
*/
int unknown();
int main(void) {
  int x = unknown();
  int y = x;
  /*@
    loop invariant x == y;
    loop assigns x, y;
    loop variant 1024 - x;
  */
  while (x < 1024) {
    x++;
    y++;
  }
  //@ assert(x == y);
}
