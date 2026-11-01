/*@
  requires x >= 0;
  requires y > 0;
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
        // Beginning
        r = r - y;
        d = d + 1;
        // ENd
        //@ assert r + d*y == x;
    }
    return d;
}