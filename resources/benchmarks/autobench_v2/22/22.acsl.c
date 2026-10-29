int main()
{
    int x = 1;
    int m = 1;
    int n;

    /*@
      loop invariant 1 <= x;
      loop invariant 1 <= m;
      loop invariant (n > 1) ==> (m < n);
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
    if(n > 1) {
       ////@ assert (m < n);
       //@ assert (m >= 1);
    }
}
