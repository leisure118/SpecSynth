/*@
    requires x == 1 && y == 2;
    requires *r == 3;
    requires \valid(r);
    assigns *r;
*/
int fun(int x, int y , int *r) {
    *r = x;
    int d = 0;

    /*@
      loop invariant *r + d * y == x;
      loop invariant d >= 0;
      loop invariant *r >= 0;
      loop assigns *r, d;
      loop variant *r;
    */
    while (*r >= y) {
        *r = *r - y;
        d = d + 1;
    }
    //@ assert *r == 1;
    //@ assert d == 0;
    return d;
}