#include<limits.h>
/*@
assigns \nothing;
ensures INT_MIN <= \result < INT_MAX;
*/
int unknown();
int main(void) {
  int x = 0;
  int y = unknown();
  //@ admit y >= 0;
  /*@
    loop invariant 0 <= x <= 100;
    loop invariant (y % 2 == 0) ==> (x % 2 == 0);
    loop invariant (y % 2 != 0) ==> (x % 2 != 0 || x < 99);
    loop assigns x;
    loop variant 100 - x;
  */
  while (x < 99) {
    if (y % 2 == 0) {
      x += 2;
    } else {
      x++;
    }
  }
  //@ assert((x % 2) == (y % 2));
}
