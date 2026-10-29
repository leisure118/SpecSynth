#include<limits.h>
/*@
assigns \nothing;
ensures INT_MIN <= \result < INT_MAX;
*/
int unknown();
#include "assert.h"
int main() {
    int n, sum, i;
    n = unknown();
    if (!(1 <= n && n <= 1000)) return 0;
    sum = 0;
    for(i = 1; i <= n; i++) {
        sum = sum + i;
    }
    //@ assert(2*sum == n*(n+1));
    return 0;
}
