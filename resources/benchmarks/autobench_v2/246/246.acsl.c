#include <limits.h>
/*@
    ensures \result >= INT_MIN && \result <= INT_MAX;
*/
int unknown_int();

int main() {
    int i,j,k,n;

    k = unknown_int();
    n = unknown_int();
    if( k == n) {
    }
    else {
        goto END;
    }

    /*@
      loop invariant 0 <= i;
      loop invariant k == n;
      loop assigns i, j, k;
      loop variant n - i;
    */
    for (i = 0; i < n; i++) {
        /*@
          loop invariant 2*i <= j;
          loop invariant k == n;
          loop assigns j, k;
          loop variant n - j;
        */
        for (j= 2 * i; j < n; j++) {
            if( unknown_int()) {
                /*@
                  loop invariant j <= k <= n;
                  loop invariant k >= 2*i;
                  loop assigns k;
                  loop variant n - k;
                */
                for (k = j; k < n; k++) {
                    //@ assert(k >= 2*i);
                }
            }
            else {
                //@ assert( k >= n );
                //@ assert( k <= n );
            }
        }
    }
END:
    return 0;
}