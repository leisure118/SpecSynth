int main()
{
    int x = 1;
    int m = 1;
    int n;

    /*@
      loop invariant x >= 1;
      loop invariant m < n || n <= 1;
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
       //@ assert (m < n);
       ////@ assert (m >= 1);
    }
}
