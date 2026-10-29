/*@
requires a <= m;
*/
void foo(int a, int m) {
    int j = 0;
    int k = 0;
    /*@
      loop invariant 0 <= k <= 1;
      loop invariant a <= m;
      loop assigns k, m;
      loop variant 1 - k;
    */
    while ( k < 1) {
        if(m < a) {
            m = a;
        }
        k = k + 1;
    }
    //@ assert a <= m;
}