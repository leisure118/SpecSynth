#include "assert.h"
int main() {
    int x,y;
    x = 0;
    y = 0;
    /*@
      loop invariant 0 <= x <= 100;
      loop invariant x <= 50 ==> y == x;
      loop invariant x >= 50 ==> y == 100 - x;
      loop invariant y >= 0;
      loop assigns x, y;
      loop variant 100 - x;
    */
    while (1) {
        if (x < 50) {
            y++;
        } else {
            y--;
        }
        if (y < 0) break;
        x++;
    }
    //@ assert(x == 100);
    return 0;
}
