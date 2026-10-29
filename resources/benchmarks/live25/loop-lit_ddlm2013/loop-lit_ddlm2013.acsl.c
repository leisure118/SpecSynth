#include<limits.h>
/*@
assigns \nothing;
ensures INT_MIN <= \result < INT_MAX;
*/
int unknown();
#include "assert.h"
int main() {
    unsigned int i,j,a,b;
    int flag = unknown();
    a = 0;
    b = 0;
    j = 1;
    if (flag) {
        i = 0;
    } else {
        i = 1;
    }
    /*@
      loop invariant (flag != 0) ==> (i == 2*(i/2));
      loop invariant (flag != 0) ==> (j == i + 1 && a == b);
      loop invariant (flag == 0) ==> (i != 2*(i/2));
      loop invariant (flag == 0) ==> ((i + 1) == 2 * j);
      loop assigns a, b, i, j;
    */
    while (unknown()) {
        //@ assert (flag != 0) ==> (i == 2*(i/2));
        //@ assert (flag == 0) ==> (i != 2*(i/2));
        a++;
        b += (j - i);
        i += 2;
        //@ assert (flag != 0) ==> (a == b);
        if (i%2 == 0) {
            j += 2;
        } else {
            j++;
        }
        //@ assert (flag != 0) ==> (j == i + 1 && a == b);
        //@ assert (flag == 0) ==> ((i + 1) == 2 * j);
    }
    if (flag) {
        //@ assert(a == b);
    }
    return 0;
}
