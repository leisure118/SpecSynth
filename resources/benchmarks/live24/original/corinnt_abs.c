#include <limits.h>
int abs(int val){
    if (val < 0) {
        /*@ assert rte: signed_overflow: -2147483647 <= val; */
        return -val;
    } 
    return val;
}
/*@
    requires d_input_not_min: INT_MIN < a; 
    assigns \nothing; 
*/
void foo(int a){
 int b = abs(42);
 int c = abs(-42);
 //@ assert c == 42;
 int d = abs(a);
 int e = abs(INT_MIN + 1);
 //@ assert e == INT_MAX;
}