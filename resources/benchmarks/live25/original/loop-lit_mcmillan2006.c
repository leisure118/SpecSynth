#include<limits.h>
/*@
assigns \nothing;
ensures INT_MIN <= \result < INT_MAX;
*/
int unknown();
#include<stdlib.h>
#include "assert.h"
int main() {
    int n = unknown();
    if (!(0 <= n && n <= 1000)) return 0;
    int *x = malloc(n * sizeof(int));
    for (int i = 0; i < n; i++) x[i] = 0;
    for (int i = 0; i < n; i++) //@ assert(x[i] == 0);
    return 0;
}
