int unknown1();
int unknown2();
int unknown3();

void foo(int flag) {
  int a = 0;
  int b = 0;
  int x = 0;
  int y = 0;
  int z = 0;
  int j = 0;
  int w = 0;

  /*@
    loop invariant w >= z;
    loop invariant z >= 0;
    loop assigns z, w, x, y;
  */
  while (unknown1()) {
    int i = z;
    int j = w;
    int k = 0;
    /*@
      loop invariant i == z + k;
      loop invariant 0 <= k;
      loop assigns i, k;
      loop variant j - i;
    */
    while (i < j) {
      k++;
      i++;
    }

    x = z;
    y = k;

    if (x % 2 == 1) {
      x++;
      y--;
    }

    /*@
      loop invariant x % 2 == 0;
      loop invariant x + y == \at(x + y, LoopEntry);
      loop assigns x, y;
    */
    while (unknown2()) {
      if (x % 2 == 0) {
        x += 2;
        y -= 2;
      } else {
        x--;
        y--;
      }
    }
    z++;
    w = x + y + 1;
  }

  int c = 0;
  int d = 0;
  /*@
    loop invariant a - b == 0;
    loop invariant c == d;
    loop assigns a, b, c, d;
  */
  while (unknown3()) {
    c++;
    d++;
    if (flag) {
      a++;
      b++;
    } else {
      a += c;
      b += d;
    }
  }
  //@ assert(w >= z && a - b == 0);
}