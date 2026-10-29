void foo(){
  int h = 42 ;
  int x = 0 ;
  int e = 0 ;
  PreLoop:
  while(e < 10){
    ++ e ;
    x += e * 2 ;
  }
  //@ assert h == 42 ;
}