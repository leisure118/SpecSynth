void foo(int x) {
  int i = 0;
  int j = 0;
  int y = 0;
  
  /*@
    loop invariant 0 <= i;
    loop invariant j == y * i;
    loop assigns i, j;
    loop variant x - i;
  */
  while (i <= x) {
    i  = i + 1;
    j  = j + y;
  }
  // post-condition
  if (i != j) {
    //@ assert(y != 1);
  }
}
