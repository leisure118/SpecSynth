/*@
requires n > 0;
*/
void foo(int n) {
    int x = 1;
    int y = 0;

    /*@
      loop invariant 1 <= x <= n+1;
      loop invariant 0 <= y;
      loop invariant y < n;
      loop assigns x, y;
      loop variant n - x;
    */
    while (x <= n) {
        y = n - x;
        x = x +1;
    }

    //post-condition
    if (n > 0) {
      ////@ assert (y >= 0);
      //@ assert (y < n);
    }
}
