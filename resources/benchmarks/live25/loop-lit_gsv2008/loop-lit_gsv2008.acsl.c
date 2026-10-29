#include<limits.h>
/*@
assigns \nothing;
ensures INT_MIN <= \result < INT_MAX;
*/
int unknown();
#include "assert.h"
int main() {
    int x,y;
    x = -50;
    y = unknown();
    if (!(-1000 < y && y < INT_MAX)) return 0;
    /*@
      loop invariant y >= -999;
      loop invariant x < 0 || y > 0;
      loop assigns x, y;
      loop variant INT_MAX - y;
    */
    while (x < 0) {
	x = x + y;
	y++;
    }
    //@ assert(y > 0);
    return 0;
}
