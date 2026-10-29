/*@
requires a <= m;
*/
void foo(int a, int m, int c) {
    int j = 0;
    int k = 0;
    /*@
      loop invariant 0 <= k;
      loop invariant a <= m;
      loop assigns m, k;
      loop variant c - k;
    */
    while (k < c) {
        if(m < a) {
            m = a;
        }
        k = k + 1;
    }
    //@ assert a <= m;
}