#include<limits.h>
/*@
assigns \nothing;
ensures INT_MIN <= \result < INT_MAX;
*/
int unknown();
#include "assert.h"
int main() {
    int i, n, a, b;
    i = 0; a = 0; b = 0; n = unknown();
    if (!(n >= 0 && n < INT_MAX)) return 0;
    while (i < n) {
        if (unknown()) {
            a = a + 1;
            b = b + 2;
        } else {
            a = a + 2;
            b = b + 1;
        }
        i = i + 1;
    }
    //@ assert(a + b == 3*n);
    return 0;
}
