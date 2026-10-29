void foo(){
  int h = 42 ;
  int x = 0 ;
  int e = 0 ;
  PreLoop:
  /*@
    loop invariant 0 <= e <= 10;
    loop invariant x == e * (e + 1);
    loop invariant h == 42;
    loop assigns e, x;
    loop variant 10 - e;
  */
  while(e < 10){
    ++ e ;
    x += e * 2 ;
  }
  //@ assert h == 42 ;
}