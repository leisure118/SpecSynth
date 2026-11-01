/*@
  requires y > 0;
  requires x >= 0;
*/
int fun(int x, int y) {
    int r = x;
    int d = 0;
    /*@
      loop invariant r + d*y == x;
      loop invariant r >= 0;
      loop invariant d >= 0;
      loop assigns r, d;
      loop variant r;
    */
    while (r >= y) {
        printf("r = %d   d = %d   y = %d   x = %d\n", r, d, y, x);
        r = r - y;
        d = d + 1;
    }
    //@ assert r + d*y == x;
    return d;
}