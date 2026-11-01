/*@ axiomatic GCD {
  logic integer gcd_math(integer a, integer b);
  axiom gcd_zero_l: \forall integer b; b >= 0 ==> gcd_math(0, b) == b;
  axiom gcd_zero_r: \forall integer a; a >= 0 ==> gcd_math(a, 0) == a;
  axiom gcd_equal: \forall integer a; a > 0 ==> gcd_math(a, a) == a;
  axiom gcd_gt: \forall integer a, b; a > b > 0 ==> gcd_math(a, b) == gcd_math(a-b, b);
  axiom gcd_lt: \forall integer a, b; b > a > 0 ==> gcd_math(a, b) == gcd_math(a, b-a);
}*/

/*@ lemma gcd_step1: gcd_math(98, 56) == gcd_math(42, 56); */
/*@ lemma gcd_step2: gcd_math(42, 56) == gcd_math(42, 14); */
/*@ lemma gcd_step3: gcd_math(42, 14) == gcd_math(28, 14); */
/*@ lemma gcd_step4: gcd_math(28, 14) == gcd_math(14, 14); */
/*@ lemma gcd_step5: gcd_math(14, 14) == 14; */
/*@ lemma gcd_result: gcd_math(98, 56) == 14; */

/*@
  requires a >= 0;
  requires b >= 0;
  decreases a + b;
  assigns \nothing;
  ensures \result == gcd_math(a, b);
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
