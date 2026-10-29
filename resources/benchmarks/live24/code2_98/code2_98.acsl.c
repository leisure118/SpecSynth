void foo(int x) {
  int i = 0;
  int j = 0;
  int y = 2;
  /*@
    loop invariant 0 <= i;
    loop invariant j == 2*i;
    loop invariant y == 2;
    loop assigns i, j;
    loop variant x - i + 1;
  */
  while (i <= x) {
    i  = i + 1;
    j  = j + y;
  }
  if (i != j) {
    //@ assert y != 1;
  }
}