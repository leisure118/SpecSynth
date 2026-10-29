#include<limits.h>
/*@
assigns \nothing;
ensures INT_MIN <= \result < INT_MAX;
*/
int unknown();
int main(void) {
  int x = 0;
  int y = unknown();
  /*@
    loop invariant (y % 2 == 0) ==> (x % 2 == 0);
    loop invariant (x >= 99) ==> (y % 2 == 0);
    loop assigns x;
  */
  while (x < 99) {
    if (y % 2 == 0) x += 2;
    else x++;
    if (y % 2 == 0) x += 2;
    else x -= 2;
    if (y % 2 == 0) x += 2;
    else x += 2;
    if (y % 2 == 0) x += 2;
    else x -= 2;
    if (y % 2 == 0) x += 2;
    else x += 2;
    if (y % 2 == 0) x += 2;
    else x -= 4;
    if (y % 2 == 0) x += 2;
    else x += 4;
    if (y % 2 == 0) x += 2;
    else x += 2;
    if (y % 2 == 0) x += 2;
    else x -= 4;
    if (y % 2 == 0) x += 2;
    else x -= 4;
  }
  //@ assert((x % 2) == (y % 2));
}
