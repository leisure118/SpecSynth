/*@
requires n > 0;
*/
void foo(int n)
{
    int x = 0;
    int m = 0;

    /*@
      loop invariant 0 <= x <= n;
      loop invariant m >= 0;
      loop assigns x, m;
      loop variant n - x;
    */
    while (x < n) {
        if (unknown()) {
            m = x;
        }
        x = x + 1;
    }

    //post-condition
    if(n > 0) {
       ////@ assert (m < n);
       //@ assert (m >= 0);
    }
}
