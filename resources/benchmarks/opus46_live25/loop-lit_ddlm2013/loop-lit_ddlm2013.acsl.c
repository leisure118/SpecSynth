#include<limits.h>
/*@ lemma uint_parity_odd_plus1_small:
  \forall integer j; 0 <= j <= 4294967293 ==> j % 2 == 1 ==>
    (unsigned int)(1 + j) % 2 == 0;
*/
/*@ lemma uint_parity_odd_plus1_max:
  \forall integer j; j == 4294967295 ==>
    (unsigned int)(1 + j) % 2 == 0;
*/
/*@ lemma uint_step_odd_small:
  \forall integer j; 0 <= j <= 4294967293 ==> j % 2 == 1 ==>
    1 + (unsigned int)(1 + j) == (unsigned int)(2 + j);
*/
/*@ lemma uint_step_odd_max:
  \forall integer j; j == 4294967295 ==>
    1 + (unsigned int)(1 + j) == (unsigned int)(2 + j);
*/
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
      loop invariant flag != 0 ==> a == b;
      loop invariant flag != 0 ==> j == i + 1;
      loop invariant flag != 0 ==> i % 2 == 0;
      loop invariant flag != 0 ==> j % 2 == 1;
      loop assigns a, b, i, j;
    */
    while (unknown()) {
        a++;
        b += (j - i);
        i += 2;
        if (i%2 == 0) {
            j += 2;
        } else {
            j++;
        }
    }
    if (flag) {
        //@ assert(a == b);
    }
    return 0;
}
