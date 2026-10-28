/* Corrected counterpart of single_fail_false_postcondition.c. */
void main(void) {
  int x;

  x = 0;
  /*@
    loop invariant 0 <= x <= 10;
    loop assigns x;
    loop variant 10 - x;
  */
  while (x < 10) {
    x = x + 1;
  }

  //@ assert x == 10;
}
