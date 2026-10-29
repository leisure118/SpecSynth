/*@
    requires x == 1 && y == 2;
    requires *r == 3;
*/
int fun(int x, int y , int *r) {
    *r = x;
    int d = 0;

    /*@
      loop invariant *r == 1;
      loop invariant d == 0;
      loop assigns *r, d;
      loop variant 1;
    */
    while (*r >= y) {
        *r = *r - y;
        d = d + 1;
    }
    //@ assert *r == 1;
    //@ assert d == 0;
    return 0;
}