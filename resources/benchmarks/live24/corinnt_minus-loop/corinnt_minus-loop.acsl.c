void minus_loop() {
    int x = 0 ;
    /*@
      loop invariant -10 <= x <= 0;
      loop assigns x;
      loop variant x + 10;
    */
    while (x > -10){
        -- x ;
    }
    //@ assert x == -10 ;
}