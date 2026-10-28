void main() {
  int y;

  y = 0;

  /*@
    loop invariant 0 <= y;
    loop assigns y;
  */
  while (y >= 0) {
    y = y + 1;
  }

  //@ assert y >= 0;
}
