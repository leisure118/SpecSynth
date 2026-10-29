/*@
  requires \valid(q);
  requires \valid(r);
  requires \separated(q, r);
  requires y != 0;
  assigns *q, *r;
  ensures *q == x / y;
  ensures *r == x % y;
*/
void div_rem(unsigned x, unsigned y, unsigned* q, unsigned* r) {
    *q = x / y;
    *r = x % y;
}
void main() {
    unsigned q, r;
    div_rem(10, 3, &q, &r);
    //@ assert q == 3;
    //@ assert r == 1;
}