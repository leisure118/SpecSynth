#include<limits.h>
/*@
assigns \nothing;
ensures INT_MIN <= \result < INT_MAX;
*/
int unknown();
#include "assert.h"
int main() {
    int i, j;
    i = unknown();
    j = unknown();
    if (!(i >= 0 && j >= 0)) return 0;
    int x = i;
    int y = j;
    while(x != 0) {
        x--;
        y--;
    }
    if (i == j) {
        //@ assert(y == 0);
    }
    return 0;
}
