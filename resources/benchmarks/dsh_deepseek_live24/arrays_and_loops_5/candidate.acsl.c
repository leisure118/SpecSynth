/*@
    requires y > 0;
    requires \valid(r);
    requires x >= 0;
    assigns *r;
    ensures *r == x % y;
    ensures \result == x / y;
*/
int fun(int x, int y , int *r) {
    *r = x;
    int d = 0;
    /*@
        loop invariant d >= 0;
        loop invariant *r >= 0;
        loop invariant *r + y*d == x;
        loop assigns *r, d;
        loop variant *r;
    */
    while (*r >= y) {
        *r = *r - y;
        d = d + 1;
    }
    return d;
}
int main() {
    int a = 3;
    int num = fun(1, 2, &a);
    //@ assert a == 1;
    //@ assert num == 0;
    return 0;
}