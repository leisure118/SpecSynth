void foo(int x) {
  int i = 0;
  int j = 0;
  int y = 0;
  
  /*@
    loop invariant i >= 0;
    loop invariant y == 0;
    loop invariant j == i * y;
    loop assigns i, j;
    loop variant x - i;
  */
  while (i <= x) {
    i  = i + 1;
    j  = j + y;
  }
  // post-condition
  if (y == 1) {
    //@ assert(i == j);
  }
}
