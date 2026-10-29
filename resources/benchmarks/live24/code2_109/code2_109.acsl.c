/*@
requires c>0;
*/
void foo(int a, int m, int c) {
    int j = 0;
    int k = 0;
    /*@
      loop invariant 0 <= k <= c;
      loop invariant m >= a || k == 0;
      loop assigns k, m;
      loop variant c - k;
    */
    while ( k < c) {
        if(m < a) {
            m = a;
        }
        k = k + 1;
    }
    if(c > 0) {
        //@ assert a <=  m;
    }
}