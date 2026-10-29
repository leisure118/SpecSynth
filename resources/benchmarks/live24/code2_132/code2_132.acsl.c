void foo(int j, int c, int t) {
    int i = 0;
    /*@
      loop invariant 0 <= i;
      loop assigns i, j, t;
    */
    while(unknown()) {
        if(c > 48) {
            if (c < 57) {
                j = i + i;
                t = c - 48;
                i = j + t;
            }
        }
    } 
    //@ assert i >= 0;
}