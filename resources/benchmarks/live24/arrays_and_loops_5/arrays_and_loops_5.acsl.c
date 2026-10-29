/*@
  requires \valid(r);
  requires x >= 0;
  requires y > 0;
  assigns *r;
  ensures \result >= 0;
  ensures *r == x - \result * y;
  ensures 0 <= *r < y;
*/
int fun(int x, int y , int *r) {
    *r = x;
    int d = 0;
    /*@
      loop invariant d >= 0;
      loop invariant *r >= 0;
      loop invariant *r == x - d * y;
      loop assigns d, *r;
      loop variant *r;
    */
    while (*r >= y) {
        *r = *r - y;
        d = d + 1;
    }
    return d;
}
int main() {
    int a = 3;
    int num = fun(1, 2, &a);
    //@ assert a == 1;
    //@ assert num == 0;
    return 0;
}