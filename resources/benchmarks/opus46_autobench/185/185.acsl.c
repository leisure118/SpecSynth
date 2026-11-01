#include <limits.h>

/*@
  assigns \nothing;
  ensures val >= 0 ==> \result == val;
  ensures val < 0 ==> \result == -val;
*/
int abs(int val) {
    if(val < 0) return -val;
    return val;
}

void foo(int a) {
    int b = abs(-42);
    //@ assert b == 42;
    int c = abs(42);
    //@ assert c == 42;
    int d = abs(a);
    int e = abs(INT_MIN);
}
