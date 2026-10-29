int main() {
  int x = -5000;
  int y = 0;
  
  /*@
    loop invariant 0 <= y;
    loop invariant 2*(x + 5000) == y*(y-1);
    loop assigns x, y;
    loop variant 101 - y;
  */
  while ((x < 0)) {
    x  = x + y;
    y  = y + 1;
  }
  // post-condition
  //@ assert(y > 0);
}
