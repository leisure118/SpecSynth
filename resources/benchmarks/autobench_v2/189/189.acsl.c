/*@
  axiomatic Gcd {
    logic integer gcd(integer a, integer b);
    axiom gcd_base_a0: \forall integer b; gcd(0, b) == b;
    axiom gcd_base_b0: \forall integer a; gcd(a, 0) == a;
    axiom gcd_eq: \forall integer a; gcd(a, a) == a;
    axiom gcd_step: \forall integer a, b; a > 0 && b > 0 && a != b ==>
      (a > b ? gcd(a, b) == gcd(a-b, b) : gcd(a, b) == gcd(a, b-a));
  }
*/

/*@
  requires a >= 0 && b >= 0;
  ensures \result == gcd(a, b);
  assigns \nothing;
*/
int gcd(int a, int b) {
    if (a == 0)
       return b;

    if (b == 0)
       return a;

    if (a == b)
        return a;

    if (a > b)
        return gcd(a-b, b);
    return gcd(a, b-a);
}

int main()
{
    int a = 98, b = 56;
    int c = gcd(a, b);
    //@ assert c == 14;
    return 0;
}