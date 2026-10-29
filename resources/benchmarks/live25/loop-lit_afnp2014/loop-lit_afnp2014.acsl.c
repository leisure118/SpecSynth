#include<limits.h>
/*@
assigns \nothing;
ensures INT_MIN <= \result < INT_MAX;
*/
int unknown();
#include "assert.h"
int main() {
    int x = 1;
    int y = 0;
    /*@
      loop invariant 0 <= y <= 1000;
      loop invariant x >= 1;
      loop invariant x >= y;
      loop assigns x, y;
      loop variant 1000 - y;
    */
    while (y < 1000 && unknown()) {
        x = x + y;
        y = y + 1;
    }
    //@ assert(x >= y);
    return 0;
}
