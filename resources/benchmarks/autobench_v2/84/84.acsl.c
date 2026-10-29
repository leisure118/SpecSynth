int main() {
  int x = -50;
  int y = 0;

  /*@
    loop invariant y >= 0;
    loop invariant x == -50 + y*(y-1)/2;
    loop assigns x, y;
    loop variant 100 - y;
  */
  while (x < 0) {
    x  = x + y;
    y  = y + 1;
  }
  // post-condition
  //@ assert(y > 0);
}
