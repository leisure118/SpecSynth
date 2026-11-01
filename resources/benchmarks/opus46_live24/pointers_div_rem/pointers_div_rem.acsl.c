/*@
  requires y != 0;
  requires \valid(q) && \valid(r);
  requires \separated(q, r);
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