#include<limits.h>
/*@
assigns \nothing;
ensures INT_MIN <= \result < INT_MAX;
ensures \result % 2 == 0 || \result % 2 == 1;
*/
int unknown();
int main(void) {
  int x = 0;
  int y = unknown();
  /*@
    loop invariant 0 <= x;
    loop invariant (y % 2 == 0) ==> (x % 2 == 0);
    loop invariant (y % 2 != 0) ==> (x <= 99);
    loop invariant (y % 2 == 0) ==> (x <= 100);
    loop assigns x;
    loop variant 99 - x;
  */
  while (x < 99) {
    if (y % 2 == 0) {
      x += 2;
    } else {
      x++;
    }
  }
  //@ assert (y % 2 != 0) ==> (x == 99);
  //@ assert (y % 2 == 0) ==> (x == 100);
  //@ assert y % 2 == 0 || y % 2 == 1;
  //@ assert 99 % 2 == 1;
  //@ assert 100 % 2 == 0;
  //@ assert (y % 2 != 0) ==> (x % 2 == 1);
  //@ assert (y % 2 == 0) ==> (x % 2 == 0);
  //@ assert((x % 2) == (y % 2));
}
