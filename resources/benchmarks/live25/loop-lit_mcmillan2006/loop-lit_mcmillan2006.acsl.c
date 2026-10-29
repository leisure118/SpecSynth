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
    /*@
      loop invariant 0 <= i <= n;
      loop invariant \forall integer j; 0 <= j < i ==> x[j] == 0;
      loop assigns i, x[0 .. n-1];
      loop variant n - i;
    */
    for (int i = 0; i < n; i++) x[i] = 0;
    /*@
      loop invariant 0 <= i <= n;
      loop invariant \forall integer j; 0 <= j < n ==> x[j] == 0;
      loop assigns i;
      loop variant n - i;
    */
    for (int i = 0; i < n; i++) //@ assert(x[i] == 0);
    return 0;
}
