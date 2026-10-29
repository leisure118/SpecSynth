#include <stdio.h>
/*@
 axiomatic GCD {
 logic integer Gcd(integer p, integer q);
 axiom Gcd1:
 \forall integer m, n;
 m > n ==> Gcd(m,n) == Gcd(m-n, n);
 axiom Gcd2:
 \forall integer m, n;
 n > m ==> Gcd(m,n) == Gcd(m, n-m);
 axiom Gcd3:
 \forall integer m, n;
 m == n ==> Gcd(m,n) == m;
 }
*/
/*@
  requires p > 0 && q > 0;
  assigns \nothing;
  ensures \result == Gcd(\old(p), \old(q));
*/
int gcd(int p, int q) {
/*@
  loop invariant p > 0 && q > 0;
  loop invariant Gcd(p, q) == Gcd(\at(p, LoopEntry), \at(q, LoopEntry));
  loop assigns p, q;
  loop variant p + q;
*/
while (p != q) {
 if (p > q) 
p = p - q;
 if (q > p) 
q = q - p;
}
return p;
}
int main() {
 int p = 48;
 int q = 18;
 int result = gcd(p, q);
 //@ assert result == 6;
 return 0;
}