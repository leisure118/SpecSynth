int main() {
    int x = 1;
    int y = 0;
    /*@
      loop invariant 1 <= x <= 101;
      loop invariant (x == 1) ==> (y == 0);
      loop invariant (x > 1) ==> (y == 101 - x);
      loop assigns x, y;
      loop variant 101 - x;
    */
    while (x <= 100) {
        y = 100 - x;
        x = x +1;
    }
    //@ assert y < 100;
}