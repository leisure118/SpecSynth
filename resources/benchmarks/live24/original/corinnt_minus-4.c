void minus_loop_2() {
    int x = -20 ;
    int rm = 5; 
    while (x < 0){
        x += 4 ;
        rm -- ; 
    }
    //@ assert x == 0 && rm == 0;
}