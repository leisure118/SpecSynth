
int main() {
    int x = 1;
    int y = 0;

    /*@
      loop invariant 1 <= x <= 11;
      loop invariant y >= 0;
      loop invariant y <= 9;
      loop assigns x, y;
      loop variant 11 - x;
    */
    while (x <= 10) {
        y = 10 - x;
        x = x +1;
    }

    //post-condition
    ////@ assert (y >= 0);
    //@ assert (y < 10);
}
