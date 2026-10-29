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
    while (y < 1000 && unknown()) {
        x = x + y;
        y = y + 1;
    }
    //@ assert(x >= y);
    return 0;
}
