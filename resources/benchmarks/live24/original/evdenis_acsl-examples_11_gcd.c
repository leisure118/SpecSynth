/*@ 
   inductive is_gcd(integer a, integer b, integer d) {
       case gcd_zero:
          \forall integer n; is_gcd(n,0,n);
       case gcd_succ:
          \forall integer a,b,d; is_gcd(b, a % b, d) ==> is_gcd(a,b,d);
    }
 */
/*@ 
   axiomatic gcd {
       logic integer gcd(integer a, integer b);
       axiom nil:
          \forall integer n; gcd(n,0) == n;
       axiom next:
          \forall integer a,b; gcd(b, a % b) == gcd(a,b);
    }
 */
unsigned gcd_rec(unsigned a, unsigned b)
{
   if (b == 0)
      return a;
   return gcd_rec(b, a % b);
}
int main()
{
   unsigned a = 48;
   unsigned b = 18;
   unsigned result = gcd_rec(a, b);
   //@ assert result == 6;
   return 0;
}