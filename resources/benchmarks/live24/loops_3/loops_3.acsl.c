#include <stdio.h>
/*@
  requires c >= 0;
  ensures \result == c;
  assigns \nothing;
*/
int func(int c) {
    int x = c;
    int y = 0;
    /*@
      loop invariant 0 <= x <= c;
      loop invariant x + y == c;
      loop assigns x, y;
      loop variant x;
    */
    while(x > 0) {
        x = x - 1;
        y = y + 1;
    }
    return y;
}
void main() {
    int t = func(5);
    //@ assert t == 5;
}