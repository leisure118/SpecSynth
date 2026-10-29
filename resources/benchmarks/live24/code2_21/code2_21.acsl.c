int main()
{
    int z1,z2,z3;
    int x = 1;
    int m = 1;
    int n;
    /*@
      loop invariant 1 <= x;
      loop invariant 1 <= m;
      loop invariant m <= x;
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
    if(n > 1) {
       //@ assert m < n;
       //@ assert m >= 1;
    }
}