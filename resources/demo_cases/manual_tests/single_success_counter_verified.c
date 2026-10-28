#include<limits.h>

/*@
requires x >= 0;
ensures \result == x;
assigns \nothing;
*/
int test(int x) {
    int a = x;
    int y = 0;

    /*@
    loop invariant a <= x;
    loop invariant a + y == x;
    loop invariant 0 <= y;
    loop assigns y;
    loop assigns a;
    */
    while(a != 0) {
        y = y + 1;
        a = a - 1;
    }
    return y;
}

int main() {
    int num = test(3);
    //@ assert num == 3;
    return 0;
}
