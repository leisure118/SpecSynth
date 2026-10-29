#include<limits.h>
/*@
assigns \nothing;
ensures INT_MIN <= \result < INT_MAX;
*/
int unknown();
#include "assert.h"
int main() {
    int a = unknown();
    int b = unknown();
    int res, cnt;
    if (!(a <= 1000000)) return 0;
    if (!(0 <= b && b <= 1000000)) return 0;
    res = a;
    cnt = b;
    while (cnt > 0) {
	cnt = cnt - 1;
	res = res + 1;
    }
    //@ assert(res == a + b);
    return 0;
}
